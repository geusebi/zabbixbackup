import logging
import subprocess
from sys import exit
from os import environ
import atexit
from copy import deepcopy
from pathlib import Path
from .utils import (
    Command, CurryCommand, parse_zabbix_version, create_name,
    preprocess_tables_lists, try_find_sockets,
)


def backup_postgresql(args):
    logging.info(f"DBMS: Postgresql")

    # Phase 0: setup authentication
    _psql_auth(args)
    env_extra = args.scope["env_extra"]

    # Informational data about an eventual connection via socket
    if args.host == "" or args.host == "localhost" or args.host.startswith("/"):
        sockets = try_find_sockets("postgres", args.port)
        logging.info(f"sockets (actual choice performed directly by postgresql): ")
        logging.info(f"    {sockets!r}")


    # Phase 1: Fetch database version and assign a name
    select_db_version = "SELECT optional FROM dbversion;"
    raw_version = _psql_query(args, select_db_version, env_extra, "zabbix version query").exec()
    if raw_version is None:
        logging.fatal("Could not retrieve db version (see logs using --debug)")
        exit(1)

    version, _ = parse_zabbix_version(raw_version)
    args.scope["version"] = version
    logging.info(f"Zabbix version: {version}")

    name = create_name(args)
    logging.info(f"Backup base name: {name}")


    # Phase 2: Perform the actual backup
    dump_params = []
    
    # select and filter tables: done here and passed to _pg_dump for simplicity
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.schema}' AND "
        f"table_catalog='{args.dbname}' AND "
        f"table_type='BASE TABLE';")

    table_cmd = _psql_query(args, table_list_query, env_extra, "zabbix tables list query")
    table_list = sorted(table_cmd.exec())
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    if fail:
        logging.error(f"Unknwon tables: aborting ({fail!r})")
        exit(1)

    if nodata:
        for i in range(0, len(nodata), 4):
            nodata_pattern = f"({'|'.join(nodata[i:i+4])})"
            dump_params += ["--exclude-table-data", nodata_pattern]

    if ignore:
        for i in range(0, len(ignore), 4):
            ignore_pattern = f"({'|'.join(ignore)})"
            dump_params += ["--exclude-table", ignore_pattern]

    # all other flags and arguments are set up by _pg_dump
    dump = _pg_dump(args, dump_params, env_extra, "pgdump command", logging.info)

    if not args.dry_run:
        dump.exec()

    args.scope["name"], args.scope["version"] = name, version


def _psql_auth(args):
    args.scope["env"] = deepcopy(environ)
    args.scope["env_extra"] = {}

    if args.loginfile is not None:
        args.scope["env_extra"] = {"PGPASSFILE": str(args.loginfile)}
    elif args.passwd is not None:
        # Create temporary pgpass file
        pgpassfile = Path(f"./.pgpass")
        with pgpassfile.open("w") as fh:
            # TODO: socket?
            fh.write(f"{args.host}:{args.port}:{args.dbname}:{args.user}:{args.passwd}")
        pgpassfile.chmod(0o600)
        if not args.keeploginfile:
            atexit.register(lambda: pgpassfile.unlink())
        args.scope["env_extra"] = {"PGPASSFILE": str(pgpassfile)}


def _psql_query(args, query, env_extra={}, description="query", log_func=logging.debug):
    # psql command will be used to inspect the database
    cmd = [
        "psql",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", args.dbname,
        "--no-password",
        "--no-align",
        "--tuples-only",
        "--no-psqlrc",
        "--command",
        query,
    ]

    exec_query = Command(cmd, env_extra=env_extra)

    log_func(f"{description}: \n{exec_query.reprexec()}")

    return exec_query


def _pg_dump(args, params, env_extra={}, description="dump cmd", log_func=logging.debug):
    cmd = [
        "pg_dump",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", args.dbname,
        "--schema", args.schema,
        "--no-password",
    ]

    if args.columns:
        # TODO: figure out if --inserts is redundant
        cmd += ["--inserts", "--column-inserts", "--quote-all-identifiers", ]

    cmd += ["--format", args.pgformat]

    if args.pgcompression is not None:
        cmd += ["--compress", args.pgcompression]

    # choose the extension depending on output format
    # TODO: move out of pg_dump for simmetry
    extensions = {"plain": ".sql", "custom": ".pgdump", "directory": "", "tar": ".tar"}
    ext = extensions[args.pgformat]

    # try to guess the correct extension in case of dump compression,
    # good enough, might fail in some edge cases
    compr_ext = ""
    if args.pgcompression is not None and args.pgformat == "plain":
        algo, _, detail = args.pgcompression.partition(":")

        if algo == "0" or detail == "0":
            pass
        elif algo == "gzip" or algo.isdigit():
            compr_ext = ".gz"
        elif algo == "lz4":
            compr_ext = ".lz"
        elif algo == "zstd":
            compr_ext = ".zst"

    dump_path = Path(args.scope["tmp_dir"]) / f"zabbix_dump{ext}{compr_ext}"

    cmd += ["--file", str(dump_path)]

    if args.verbosity in ("very", "debug"):
        cmd += ["--verbose"]

    cmd += params

    dump = Command(cmd, env_extra=env_extra)

    log_func(f"{description}: \n{dump.reprexec()}")

    return dump
