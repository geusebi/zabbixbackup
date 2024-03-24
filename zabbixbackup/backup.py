import logging
from .utils import try_find_sockets
from pathlib import Path
from datetime import datetime
from .utils import CurryCmd
from os import environ
from copy import deepcopy
import atexit
from .tables import zabbix
from sys import exit


def parse_zabbix_version(query_result):
    raw_version = query_result[0]
    major = int(raw_version[:-6])
    minor = int(raw_version[-6:-4])
    revision = int(raw_version[-4:])
    
    version = f"{major}.{minor}.{revision}"
    logging.verbose(f"Zabbix database version: {version}")

    return version, (major, minor, revision)


def create_name(args, version):
    dt = datetime.now().strftime("%Y%m%d-%H%M")
    name = f"zabbix_cfg_{args.host}_{dt}_{version}"
    logging.verbose(f"Backup name: {name}")

    return name


def preprocess_tables_lists(args, table_list):
    logging.debug(f"Table list: {table_list!r}")
    logging.verbose(f"Tables found: {len(table_list)}")

    tables = set(table_list)
    config = tables.intersection(zabbix.config)
    monitoring = tables.intersection(zabbix.monitoring)
    unknown = tables.difference(config, monitoring)

    logging.verbose(f"Config tables: {len(config)}")
    logging.verbose(f"Monitoring tables: {len(monitoring)}")
    logging.verbose(f"Unknown tables: {len(unknown)}")

    nodata, ignore, fail = [], [], []
    if args.monitoring == "nodata":
        nodata += monitoring

    if args.unknown == "nodata":
        nodata += unknown
    elif args.unknown == "ignore":
        ignore += unknown 
    elif args.unknown == "fail":
        fail += unknown

    return sorted(ignore), sorted(nodata), sorted(fail)


def backup_postgresql(args, extra):
    logging.verbose(f"DBMS: Postgresql")

    # Phase 0: setup CLI commands

    # psql command will be used to inspect the database
    psql_query = [
        "psql",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", args.dbname,
        "--no-align", "--tuples-only", "--no-password", "--no-psqlrc",
    ]

    pg_dump = [
        "pg_dump",
        "--host", args.host,
        "--username", args.user,
        "--port", args.port,
        "--dbname", args.dbname,
        "--schema", args.schema,
        "--inserts", "--column-inserts", "--quote-all-identifiers"
    ]

    # Create temporary pgpass file
    pgpassfile = Path(f".\pgpass")
    with pgpassfile.open("w") as fh:
        fh.write(f"{args.host}:{args.port}:{args.dbname}:{args.user}:{args.passwd}")
    pgpassfile.chmod(0o600)
    atexit.register(lambda: pgpassfile.unlink())

    env = deepcopy(environ)
    env_extra = {"PGPASSFILE": str(pgpassfile)}

    # Base commands to query and dump the database
    psql = CurryCmd(psql_query, env, env_extra)
    dump = CurryCmd(pg_dump, env, env_extra)

    logging.debug(f"psql base command: \n{psql}")
    logging.debug(f"dump base command: \n{dump}")

    # Informational data about an eventual connection via socket
    if args.sock is not None or args.host == "" or args.host == "localhost":
        provided = (args.sock, ) if args.sock is not None else tuple()
        sockets = provided + try_find_sockets("postgres", args.port)
        logging.info(f"sockets (actual choice performed by postgresql according to selection): ")
        logging.info(f"    {sockets!r}")

    # Phase 1: Fetch database version
    select_db_version = "SELECT optional FROM dbversion;"
    logging.debug(f"Select zabbix version command: \n{psql.reprexec('-c', select_db_version)}")
    result = psql.exec("-c", select_db_version)

    version, _ = parse_zabbix_version(result)

    # Phase 2 - select and filter out the tables
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.schema}' AND "
        f"table_catalog='{args.dbname}' AND "
        f"table_type='BASE TABLE';")

    table_list = sorted(psql.exec("-c", table_list_query))
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    # Phase 3: select output folder
    # TODO: dry-run handling
    name = create_name(args, version)
    # choose the extension based on output format
    extensions = {"plain": ".sql", "custom": ".pgdump", "directory": "", "tar": ".tar"}
    sqlpath = Path(extra.tmp_dir) / f"zabbix_cfg{extensions[args.format]}"

    # Phase 3: perform the actual dump
    dump_args = []
    dump_args += ["--file", str(sqlpath)]
    dump_args += ["--format", args.format]
    if args.compression is not None:
        dump_args += ["-Z", args.compression]

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

    logging.info(f"Dump command: \n{dump.reprexec(*dump_args)}")

    if args.verbosity in ("very", "debug"):
        dump_args += ["--verbose"]

    if not args.dry_run:
        dump.exec(*dump_args)

    extra.name, extra.version = name, version 


def backup_mysql(args, config):
    pass