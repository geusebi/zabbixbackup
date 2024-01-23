from shlex import quote as shquote
import logging
from .utils import try_find_sockets
from pathlib import Path
from datetime import datetime


def quote(s):
    return shquote(str(s))


def backup_postgresql(args):
    logging.info(f"DBMS: Postgresql")

    # psql command will be used to execute select statements to inspect the database
    psql = ["psql"]
    psql += ["-h", args.host]
    psql += ["-U", args.user]
    psql += ["-p", args.port]
    psql += ["--no-align", "--tuples-only", "--no-password", "--no-psqlrc"]
    psql += ["-d", args.dbname]

    psql = tuple(map(quote, psql))

    # pg_dump command will execute the actual database backup   
    dump = ["pg_dump"]
    dump += ["-h", args.host]
    dump += ["-U", args.user]
    dump += ["-p", args.port]
    dump += ["-d", args.dbname]
    dump += ["-n", args.schema]
    dump += ["--format", args.format]
    dump += ["--inserts", "--column-inserts", "--quote-all-identifiers"]

    dump = tuple(map(quote, dump))

    if args.sock is not None or args.host == "" or args.host == "localhost":
        provided = (args.sock, ) if args.sock is not None else tuple()
        sockets = provided + try_find_sockets("postgres", args.port)
        logging.debug(f"sockets (actual choice performed by postgresql according to selection): ")
        logging.debug(f"    {sockets!r}")

    logging.debug(f"psql base command: {' '.join(psql)}")
    logging.debug(f"dump base command: {' '.join(dump)}")

    # phase 1 - select and filter out the tables
    table_list_query = (
        "SELECT table_name FROM information_schema.tables "
        "WHERE  table_schema='{args.schema}' AND "
        "       table_catalog='{args.dbname}' AND "
        "       table_type='BASE TABLE';")


    # Fetch database version
    db_version_query = "select optional from dbversion;"
    raw_version = "6040025"
    major = int(raw_version[:-6])
    minor = int(raw_version[-6:-4])
    revision = int(raw_version[-4:])
    
    version = f"{major}.{minor}.{revision}"
    logging.info(f"zabbix database version: {version}")

    dt = datetime.now().strftime("%Y%m%d-%HM")
    dump_name = Path(f"zabbix_cfg_{args.host}_{dt}_{version}.sql")
    dump_path = Path(f"{args.outdir}") / dump_name
    logging.info(f"dump destination: {dump_path}")

def backup_mysql(args, config):
    pass