"""
Dump a PostgreSQL database.
"""
import logging
from os import fdopen, environ
import tempfile
import shutil
import atexit
from pathlib import Path
from subprocess import PIPE

from .utils import (
    DPopen, check_binary, parse_zabbix_version,
    preprocess_tables_lists, process_repr, try_find_sockets,
)

logger = logging.getLogger()


def backup_postgresql(args):
    """Perform a PostgreSQL dump in the current directory."""
    logger.info("DBMS: Postgresql")
    if not check_binary("psql", "pg_dump"):
        return 1, "Missing binaries: check 'psql' and 'pg_dump' are available and in PATH"

    args.scope["env"] = {}

    # Phase 0: setup authentication
    _psql_auth(args)

    # Informational data about an eventual connection via socket
    if args.host == "" or args.host == "localhost" or args.host.startswith("/"):
        sockets = try_find_sockets("postgres", args.port)
        logger.info("sockets (actual choice performed directly by postgresql): ")
        logger.info("    %r", sockets)


    # Phase 1: Fetch database version and assign a name
    select_db_version = "SELECT optional FROM dbversion;"
    raw_version = _psql_query(args, select_db_version, "zabbix version query")
    if raw_version is None:
        return 2, "Could not retrieve db version (see logs)"

    version, _ = parse_zabbix_version(raw_version)
    with open("zabbix_dbversion", "w", encoding="utf-8") as fh:
        fh.writelines(["postgres\n", f"{version}\n"])

    logger.info("Zabbix version: %s", version)

    # Phase 2: Perform the actual backup

    # select and filter tables: done here and passed to _pg_dump for simplicity
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.schema}' AND "
        f"table_catalog='{args.dbname}' AND "
        f"table_type='BASE TABLE';")

    table_cmd = _psql_query(args, table_list_query, "zabbix tables list query")
    if table_cmd is None:
        return 3, "Could not retrieve table list (see logs)"

    table_list = sorted(table_cmd)
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    dump_params = []

    if fail:
        return 4, f"Unknwon tables: aborting ({fail!r})"

    if nodata:
        for i in range(0, len(nodata), 4):
            nodata_pattern = f"({'|'.join(nodata[i:i+4])})"
            dump_params += ["--exclude-table-data", nodata_pattern]

    if ignore:
        for i in range(0, len(ignore), 4):
            ignore_pattern = f"({'|'.join(ignore)})"
            dump_params += ["--exclude-table", ignore_pattern]

    # all other flags and arguments are set up by _pg_dump
    outpath = Path("zabbix_dump")
    dump_status = _pg_dump(args, dump_params, outpath, "pgdump command", logging.info)
    if not dump_status:
        return 5, "Could not execute dump (see logs)"

    return 0, "+OK"


def _psql_auth(args):
    # Use provided loginfile and leave it untouched
    if args.loginfile is not None:
        args.scope["env"] = {"PGPASSFILE": str(args.loginfile)}

    elif args.passwd is not None:
        # Create temporary pgpass file
        pgpass_fd, pgpass_path = tempfile.mkstemp(prefix="pgpass_", text=True)
        pgpass_path = Path(pgpass_path)
        fh = fdopen(pgpass_fd, "w")

        pgpass_path.chmod(0o600)
        fh.writelines([
                # TODO: socket?
                f"{args.host}:{args.port}:{args.dbname}:{args.user}:{args.passwd}\n",
            ])
        fh.close()

        abs_pgpass = pgpass_path.absolute()
        atexit.register(abs_pgpass.unlink)

        args.loginfile = pgpass_path
        args.scope["env"] = {"PGPASSFILE": str(pgpass_path)}

    if args.keeploginfile:
        shutil.copy(args.loginfile, "./pgpass")
        Path("./pgpass")


def _psql_query(args, query, description="query", log_func=logging.debug):
    dbname = args.dbname
    env_extra = args.scope["env"]

    # psql command will be used to inspect the database
    query_cmd = [
        "psql",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", dbname,
        "--no-password",
        "--no-align",
        "--tuples-only",
        "--no-psqlrc",
        "--command",
        query,
    ]

    query_cmd = tuple(map(str, query_cmd))
    query_env = {**environ, **env_extra}

    log_func(f"{description}: \n{process_repr(query_cmd, env_extra)}")

    exec_query = DPopen(query_cmd, env=query_env, stdout=PIPE, text=True)
    stdout, stderr = exec_query.communicate()

    if exec_query.returncode != 0:
        if stderr is not None:
            logging.fatal(stderr)
        return None

    return stdout.splitlines()


def _pg_dump(
    args, params, outpath, description="dump cmd", log_func=logging.debug
):
    dbname = args.dbname
    env_extra = args.scope["env"]

    dump_cmd = [
        "pg_dump",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", dbname,
        "--schema", args.schema,
        "--no-password",
    ]

    if args.columns:
        # TODO: figure out if --inserts is redundant
        dump_cmd += ["--inserts", "--column-inserts", "--quote-all-identifiers", ]

    dump_cmd += ["--format", args.pgformat]

    if args.pgcompression is not None:
        dump_cmd += ["--compress", args.pgcompression]

    # choose the extension depending on output format
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

    dump_path = f"{outpath}{ext}{compr_ext}"

    dump_cmd += ["--file", str(dump_path)]

    if args.verbosity in ("very", "debug"):
        dump_cmd += ["--verbose"]

    dump_cmd += params

    dump_env = {**environ, **env_extra}
    dump_cmd = tuple(map(str, dump_cmd))

    log_func(f"{description}: \n{process_repr(dump_cmd, env_extra)}")

    # don't execute if dry run is enabled
    if args.dry_run:
        return True

    dump = DPopen(dump_cmd, env=dump_env)
    dump.communicate()

    return dump.returncode == 0
