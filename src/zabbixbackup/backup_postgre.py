import logging
from sys import exit
from os import environ
import atexit
from copy import deepcopy
from pathlib import Path
from .utils import (
    CurryCommand, parse_zabbix_version, create_name,
    preprocess_tables_lists, try_find_sockets,
)


def backup_postgresql(args):
    logging.info(f"DBMS: Postgresql")

    # Phase 0: setup authentication
    _psql_auth(args)

    # Informational data about an eventual connection via socket
    if args.host == "" or args.host == "localhost" or args.host.startswith("/"):
        sockets = try_find_sockets("postgres", args.port)
        logging.info(f"sockets (actual choice performed directly by postgresql): ")
        logging.info(f"    {sockets!r}")


    # Phase 1: Fetch database version and assign a name
    select_db_version = "SELECT optional FROM dbversion;"
    raw_version = _psql_query(args, select_db_version, "zabbix version query").exec()
    if raw_version is None:
        logging.fatal("Could not retrieve db version (see logs using --debug)")
        exit(1)

    version, _ = parse_zabbix_version(raw_version)
    logging.info(f"Zabbix version: {version}")

    name = create_name(args, version)
    logging.info(f"Backup base name: {name}")


    # Phase 2: Perform the actual backup
    dump_args = []
    
    # select and filter tables: done here and passed to _pg_dump for simplicity
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.schema}' AND "
        f"table_catalog='{args.dbname}' AND "
        f"table_type='BASE TABLE';")

    table_cmd = _psql_query(args, table_list_query, "zabbix tables list query")
    table_list = sorted(table_cmd.exec())
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    if fail:
        logging.error(f"Unknwon tables: aborting ({fail!r})")
        exit(1)

    if nodata:
        for i in range(0, len(nodata), 4):
            nodata_pattern = f"({'|'.join(nodata[i:i+4])})"
            dump_args += ["--exclude-table-data", nodata_pattern]

    if ignore:
        for i in range(0, len(ignore), 4):
            ignore_pattern = f"({'|'.join(ignore)})"
            dump_args += ["--exclude-table", ignore_pattern]

    # all other flags and arguments are set up by _pg_dump
    dump = _pg_dump(args, dump_args, "pgdump command", logging.info)

    if not args.dry_run:
        dump.exec()

    args.scope["name"], args.scope["version"] = name, version


def _psql_auth(args):
    args.scope["env"] = deepcopy(environ)
    args.scope["env_extra"] = {}

    if args.passwd is not None:
        # Create temporary pgpass file
        pgpassfile = Path(f".\pgpass")
        with pgpassfile.open("w") as fh:
            fh.write(f"{args.host}:{args.port}:{args.dbname}:{args.user}:{args.passwd}")
        pgpassfile.chmod(0o600)
        atexit.register(lambda: pgpassfile.unlink())
        args.scope["env_extra"] = {"PGPASSFILE": str(pgpassfile)}


def _psql_query(args, query, description="query", log_func=logging.debug):
    # psql command will be used to inspect the database
    query = CurryCommand(
        [
            "psql",
            "--host", args.host,
            "--username", args.user,
            "--port", args.port,
            "--dbname", args.dbname,
            "--no-password", "--no-align", "--tuples-only", "--no-psqlrc",
            "--command",
        ] + [query]
        , args.scope["env"], args.scope["env_extra"]
    )

    log_func(f"{description}: \n{query.reprexec()}")

    return query


def _pg_dump(args, params, description="dump cmd", log_func=logging.debug):
    extra_args = []
    if args.columns:
        # Todo: figure out if --inserts is redundant
        extra_args += ["--inserts", "--column-inserts", "--quote-all-identifiers", ]
    
    if args.verbosity in ("very", "debug"):
        extra_args += ["--verbose"]

    if args.compression is not None:
        extra_args += ["--compress", args.compression]

    # choose the extension depending on output format
    # TODO: move out of pg_dump for simmetry
    extensions = {"plain": ".sql", "custom": ".pgdump", "directory": "", "tar": ".tar"}
    sqlpath = Path(args.scope["tmp_dir"]) / f"zabbix_cfg{extensions[args.format]}"

    extra_args += ["--file", str(sqlpath)]
    extra_args += ["--format", args.format]

    cmd = CurryCommand(
        [
            "pg_dump",
            "--host", args.host,
            "--username", args.user,
            "--port", args.port,
            "--dbname", args.dbname,
            "--schema", args.schema,
            "--no-password",
        ] + extra_args + params,
        args.scope["env"], args.scope["env_extra"]
    )

    log_func(f"{description}: \n{cmd.reprexec()}")

    return cmd
