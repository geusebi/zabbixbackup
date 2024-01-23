import argparse
from pathlib import Path


__all__ = ["build_parser"]


def build_parser(defaults):
    description = "zabbix dump for mysql and psql inspired and directly translated from..."

    parser = argparse.ArgumentParser(
        "zabbixdump",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=description)

    parser.add_argument(
        "-t", "--type",
        help="database connection or autofetch via zabbix configuration file.",
        default=defaults.type,
        choices=("mysql", "psql"))

    parser.add_argument(
        "-z", "--read-zabbix-config",
        help="try to read database host and credentials from Zabbix config.",
        action="store_true",
        default=defaults.read_zabbix_config)

    parser.add_argument(
        "-Z", "--zabbix-config",
        help="Zabbix config file path.",
        default=defaults.zabbix_config,
        type=Path,
        dest="zbx_config")

    parser.add_argument(
        "-c", "--read-mysql-config",
        help="MySQL specific: Read database host and credentials from MySQL config file.",
        action="store_true",
        default=defaults.read_mysql_config)

    parser.add_argument(
        "-C", "--mysql-config",
        help="MySQL specific: MySQL config file path.",
        default=defaults.mysql_config,
        type=Path)

    parser.add_argument(
        "-D", "--dry-run",
        help="do not create the actual backup, only show dump commands. "
            "Be aware that the database will be queried for tables selection.",
        default=defaults.dry_run,
        action="store_true")


    connection = parser.add_argument_group("connection options")

    connection.add_argument(
        "-H", "--host",
        help="dostname/IP of database server DBMS, to specify a blank value pass '-'.",
        default=defaults.host)

    connection.add_argument(
        "-P", "--port",
        help="DBMS port.",
        default="mysql=3306 or psql=5432")

    connection.add_argument(
        "-S", "--socket",
        help="path to DBMS socket file. "
            "Alternative to specifying host.",
        dest="sock",
        default=defaults.sock)

    connection.add_argument(
        "-u", "--username",
        help="database login user.",
        default=defaults.user,
        dest="user")

    connection.add_argument(
        "-p", "--passwd",
        help="database login password (specify '-' for a prompt).",
        default=defaults.passwd)

    connection.add_argument(
        "-d", "--database",
        help="database name.",
        default=defaults.dbname,
        dest="dbname")

    connection.add_argument(
        "-s", "--schema",
        help="PostgreSQL specific: database schema.",
        default=defaults.schema)

    connection.add_argument(
        "-n", "--reverse-lookup",
        help="perform a reverse lookup of IP address for the host.",
        action="store_true",
        default=defaults.rlookup,
        dest="rlookup")


    dump = parser.add_argument_group("dump options")

    dump.add_argument(
        "-U", "--unknown-action",
        help="ingore unknown tables (don't include them into the backup)",
        default=defaults.unknown,
        choices=("dump", "schema", "ignore", "fail"),
        dest="unknown")

    dump.add_argument(
        "-N", "--add-columns",
        help="add column names in "
            "INSERT clauses and quote them as needed.",
        default=defaults.columns,
        action="store_true",
        dest="columns")


    output = parser.add_argument_group("output options")

    compression_desc = """
    set compression algorithm. xz will take longer and consume more CPU time
    but the backup will be smaller of the same dump compressed using gzip.
    """.strip()

    output.add_argument(
        "-x", "--compression",
        help=compression_desc,
        default=defaults.compression,
        choices=("gzip", "xz", "none"))

    output.add_argument(
        "-f", "--format",
        help="PostgreSQL specific: custom dump format",
        default=defaults.format)

    output.add_argument(
        "-r", "--rotate",
        help="rotate backups while keeping up to 'R' old backups. "
            "Uses filename to match '0=keep everything'.",
        default=defaults.rotate,
        type=int)

    output.add_argument(
        "-o", "--outdir",
        help="save database dump to 'outdir'.",
        default=defaults.outdir,
        type=Path)


    verbosity = parser.add_argument_group("verbosity")
    verbosity_group = verbosity.add_mutually_exclusive_group()
    # In case its needed to change the default value for this group 'postprocess' must be
    # modified accordingly (else clause is the default during verbosity handling) 
    verbosity_group.add_argument(
        "-q", "--quiet",
        help="don't print anything except unrecoverable errors.",
        action="store_true",
        default=defaults.quiet)

    verbosity_group.add_argument(
        "-v", "--verbose",
        help="print informations",
        action="store_true",
        default=defaults.verbose)

    verbosity_group.add_argument(
        "-V", "--very-verbose",
        help="print even more informations",
        action="store_true",
        default=defaults.very_verbose)

    verbosity_group.add_argument(
        "--debug",
        help="print everything",
        action="store_true",
        default=defaults.debug)

    return parser
