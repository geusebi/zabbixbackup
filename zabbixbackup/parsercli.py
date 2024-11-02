import argparse
from pathlib import Path


__all__ = ["build_parser"]


def build_parser(defaults):
    # TODO: add credits in the help screen
    description = "zabbix dump for mysql and psql inspired and directly translated from..."

    parser = argparse.ArgumentParser(
        "zabbixbackup",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=description)

    parser.add_argument(
        "-t", "--type",
        help="select the DBMS type.",
        default=defaults.type,
        choices=("mysql", "psql"))

    parser.add_argument(
        "-z", "--read-zabbix-config",
        help="try to read database host and credentials from Zabbix config. "
        "Implicit if `--zabbix-config` is set by the user.",
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
        help="MySQL specific: Read database host and credentials from MySQL config file. "
        "Implicit if `--mysql-config` is set by the user.",
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
            "Be aware that the database will be queried for tables selection and "
            "temporary folders and files are created.",
        default=defaults.dry_run,
        action="store_true")


    connection = parser.add_argument_group("connection options")

    connection.add_argument(
        "-H", "--host",
        help="hostname/IP of DBMS server, to specify a blank value pass '-'. "
            "For postgresql special rules might apply (see online documentation).",
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
        help="database login password (specify '-' for an interactive prompt).",
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
        help="action for unknown tables.",
        default=defaults.unknown,
        choices=("dump", "nodata", "ignore", "fail"),
        dest="unknown")

    dump.add_argument(
        "-M", "--monitoring-action",
        help="action for monitoring table",
        default=defaults.monitoring,
        choices=("dump", "nodata"),
        dest="monitoring")

    dump.add_argument(
        "-N", "--add-columns",
        help="add column names in INSERT clauses and quote them as needed.",
        default=defaults.columns,
        action="store_true",
        dest="columns")


    files = parser.add_argument_group("configuration files")

    files.add_argument(
        "--save-files",
        help="save folders and other files listed in this file. "
            "One line per folder or file, non existant will be ignored. "
            "Directory structure is replicated (copied via 'cp')."
            "If '-' is passed then standard directories are copied "
            "(/etc/zabbix, /usr/lib/zabbix).",
        default=defaults.save_files,
        action="store_true")

    files.add_argument(
        "--files",
        help="save folders and other files listed in this 'files'. "
            "One line per folder or file, non existant will be ignored. "
            "Directory structure is replicated (copied via 'cp')."
            "If '-' is passed then standard directories are copied.",
        default=defaults.save_files,
        type=Path)

    output = parser.add_argument_group("output options")

    output.add_argument(
        "-x", "--compression",
        help="PostgreSQL specific: passed as-is to pg_dump --compress, might be implied by format.",
        default=defaults.compression)

    output.add_argument(
        "-f", "--format",
        help="PostgreSQL specific: custom dump format, will mandate the file output format.",
        choices={"plain", "custom", "directory", "tar"},
        default=defaults.format)

    output.add_argument(
        "-r", "--rotate",
        help="rotate backups while keeping up 'R' old backups."
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
    # In case it is needed to change the default value for this group,
    # 'postprocess' must be modified accordingly (else clause is the default
    # during verbosity handling)
    # TODO: choose what to print and in which form
    verbosity_group.add_argument(
        "-q", "--quiet",
        help="don't print anything except unrecoverable errors.",
        action="store_true",
        default=defaults.quiet)

    verbosity_group.add_argument(
        "-v", "--verbose",
        help="print informations.",
        action="store_true",
        default=defaults.verbose)

    verbosity_group.add_argument(
        "-V", "--very-verbose",
        help="print even more informations.",
        action="store_true",
        default=defaults.very_verbose)

    verbosity_group.add_argument(
        "--debug",
        help="print everything.",
        action="store_true",
        default=defaults.debug)

    return parser
