import argparse
from pathlib import Path
from collections import defaultdict
from types import SimpleNamespace as NS
import logging
from .parserutils import *
from pprint import pprint


# Script default values
# (these are important to allow to separate user provided values during parsing)
# 'dest' name actions in parsing must be the same as in this namespace
defs = NS()
defs.type                 = "psql"

defs.read_zabbix_config   = True
defs.zabbix_config        = "/etc/zabbix/zabbix_server.conf"

defs.read_mysql_config    = False
defs.mysql_config         = Path("/etc/mysql/my.cnf")
defs.dry_run              = False

defs.host                 = "127.0.0.1"
defs.port                 = "mysql=3306 or psql=5432" # handled manually
defs.sock                 = None
defs.user                 = "zabbix"
defs.passwd               = "-"
defs.dbname               = "zabbix"
defs.schema               = "public"
defs.rlookup              = True

defs.unknown              = "ignore"
defs.columns              = False

defs.compression          = "gzip"
defs.format               = "custom"
defs.rotate               = 0
defs.outdir               = Path(".")

defs.quiet                = False
defs.verbose              = True
defs.very_verbose         = False
defs.debug                = False


description = "zabbix dump for mysql and psql inspired and directly translated from..."

parser = argparse.ArgumentParser(
    "zabbixdump",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=description)

parser.add_argument(
    "-t", "--type",
    help="database connection or autofetch via zabbix configuration file.",
    default=defs.type,
    choices=("mysql", "psql"))

parser.add_argument(
    "-z", "--read-zabbix-config",
    help="try to read database host and credentials from Zabbix config.",
    action="store_true",
    default=defs.read_zabbix_config)

parser.add_argument(
    "-Z", "--zabbix-config",
    help="Zabbix config file path.",
    default=defs.zabbix_config,
    type=Path,
    dest="zbx_config")

parser.add_argument(
    "-c", "--read-mysql-config",
    help="MySQL specific: Read database host and credentials from MySQL config file.",
    action="store_true",
    default=defs.read_mysql_config)

parser.add_argument(
    "-C", "--mysql-config",
    help="MySQL specific: MySQL config file path.",
    default=defs.mysql_config,
    type=Path)

parser.add_argument(
    "-D", "--dry-run",
    help="do not create the actual backup, only show dump commands. "
         "Be aware that the database will be queried for tables selection.",
    default=defs.dry_run,
    action="store_true")


connection = parser.add_argument_group("connection options")

connection.add_argument(
    "-H", "--host",
    help="dostname/IP of database server DBMS, to specify a blank value pass '-'.",
    default=defs.host)

connection.add_argument(
    "-P", "--port",
    help="DBMS port.",
    default="mysql=3306 or psql=5432")

connection.add_argument(
    "-S", "--socket",
    help="path to DBMS socket file. "
         "Alternative to specifying host.",
    dest="sock",
    default=defs.sock)

connection.add_argument(
    "-u", "--username",
    help="database login user.",
    default=defs.user,
    dest="user")

connection.add_argument(
    "-p", "--passwd",
    help="database login password (specify '-' for a prompt).",
    default=defs.passwd)

connection.add_argument(
    "-d", "--database",
    help="database name.",
    default=defs.dbname,
    dest="dbname")

connection.add_argument(
    "-s", "--schema",
    help="PostgreSQL specific: database schema.",
    default=defs.schema)

connection.add_argument(
    "-n", "--reverse-lookup",
    help="perform a reverse lookup of IP address for the host.",
    action="store_true",
    default=defs.rlookup,
    dest="rlookup")


dump = parser.add_argument_group("dump options")

dump.add_argument(
    "-U", "--unknown-action",
    help="ingore unknown tables (don't include them into the backup)",
    default=defs.unknown,
    choices=("dump", "schema", "ignore", "fail"),
    dest="unknown")

dump.add_argument(
    "-N", "--add-columns",
    help="add column names in "
         "INSERT clauses and quote them as needed.",
    default=defs.columns,
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
    default=defs.compression,
    choices=("gzip", "xz", "none"))

output.add_argument(
    "-f", "--format",
    help="PostgreSQL specific: custom dump format",
    default=defs.format)

output.add_argument(
    "-r", "--rotate",
    help="rotate backups while keeping up to 'R' old backups. "
         "Uses filename to match '0=keep everything'.",
    default=defs.rotate,
    type=int)

output.add_argument(
    "-o", "--outdir",
    help="save database dump to 'outdir'.",
    default=defs.outdir,
    type=Path)


verbosity = parser.add_argument_group("verbosity")
verbosity_group = verbosity.add_mutually_exclusive_group()
# In case its needed to change the default value for this group 'postprocess' must be
# modified accordingly (else clause is the default during verbosity handling) 
verbosity_group.add_argument(
    "-q", "--quiet",
    help="don't print anything except unrecoverable errors.",
    action="store_true",
    default=defs.quiet)

verbosity_group.add_argument(
    "-v", "--verbose",
    help="print informations",
    action="store_true",
    default=defs.verbose)

verbosity_group.add_argument(
    "-V", "--very-verbose",
    help="print even more informations",
    action="store_true",
    default=defs.very_verbose)

verbosity_group.add_argument(
    "--debug",
    help="print everything",
    action="store_true",
    default=defs.debug)


def postprocess(uargs, dargs):
    """
    Adjust the arguments according to zabbix behaviour and user selection.

    See comments inside the function.
    """
    # uargs: actual provided arguments
    # dargs: only defaults via argparse

    # The final arguments are stored in args directly and their override order is:
    #   TODO: WRITE DOC
    # I.E. CLI arguments are the most important

    # Hostname / Socket: special case. 
    if uargs.host == "-":
        uargs.host = ""
    if uargs.sock == "-":
        uargs.sock = ""


    # Port number: special case. To show mysql and psql default values in the help is passed
    # unchecked as a string. Actual conversion and defaults are handled here
    
    # A little redundant but it's better to keep simmetry:
    # if user provided a DBMS or if it hasn't and the default DBMS is X then set port accordingly
    if uargs.type == "mysql" or (uargs.type is None and dargs.type == "mysql"):
        dargs.port = 3306
    elif uargs.type == "psql" or (uargs.type is None and dargs.type == "psql"):
        dargs.port = 5432

    if uargs.port is not None:
        if not uargs.port.isdecimal():
            raise parser.error(f"Port must be integer: {uargs.port!r}")
        uargs.port = int(uargs.port)

        if not (1024 <= uargs.port <= 65535):
            raise parser.error(f"Port must be between 1024 and 65535: {uargs.port!r}")


    # Implicit read from zabbix config if a file is provided
    if uargs.zbx_config:
        uargs.read_zabbix_config = True

    # Implicit read from mysql config if a file is provided
    if uargs.mysql_config:
        uargs.read_mysql_config = True

    # Argument precedence lists (largs): dict[list]
    # Every argument is added to the dict as {key: [values...]}.
    # If no zabbix configuration file is specified, the order is:
    #    user provided, default arguments from this script
    # If a zabbix configuration file is specified, the order is:
    #    user provided, configuration, configuration default, last-shipped configuration default 
    largs = defaultdict(list, {})

    # User provided
    for key, value in vars(uargs).items():
        if value is not None:
            largs[key].append(value)

    if uargs.read_zabbix_config:
        # We read last shipped configuration defaults + local configuration default (zdefconfig)
        # and proper configuration values (zconfig).
        last_shipped_config = Path(__file__).parent / "assets" / "zabbix_server.conf"
        defconfig = zabbix_try_read_defaults(last_shipped_config)
        zdefconfig = zabbix_try_read_defaults(uargs.zbx_config, defconfig)
        zconfig = zabbix_try_read_config(uargs.zbx_config)

        zbx_var_map = (
            ("DBHost", "host", str, ),
            ("DBPort", "port", int, ),
            ("DBName", "dbname", str, ),
            ("DBSchema", "schema", str, ),
            ("DBUser", "user", str, ),
            ("DBPassword", "passwd", str, ),
            ("DBSocket", "sock", Path, ),
        )

        zdefconfig = map_clean_vars(zdefconfig, zbx_var_map)
        zconfig = map_clean_vars(zconfig, zbx_var_map)

        # Add local configured values to the precedence list 
        for key, value in zconfig.items():
            largs[key].append(value)

        # Add default configuration values to the precedence list
        for key, value in zdefconfig.items():
            largs[key].append(value)

    # If we do not read zabbix configuration, default args from this script are used 
    for key, value in vars(dargs).items():
        largs[key].append(value)


    # Create flat arguments namespace
    args = NS()
    for key, values in largs.items():
        setattr(args, key, values[0])

    # Clean parameters based on dbms selection 
    if args.type == "psql":
        if uargs.mysql_config or uargs.read_mysql_config:
            raise parser.error(f"MySQL parameter specified with wrong db type: {args.type!r}")
        del args.mysql_config
        del args.read_mysql_config
        
        if uargs.host is not None and uargs.sock is not None:
            logging.warn(
                "Conflict, host and socket provided, "
                "socket will takes precedence.")
        if uargs.sock is not None:
            args.host = uargs.sock
    elif args.type == "mysql":
        if uargs.schema:
            raise parser.error(f"Schema name specified with wrong db type: {args.type!r}")
        if uargs.format:
            raise parser.error(f"Format kind specified with wrong db type: {args.type!r}")
        del args.schema
        del args.format

    if args.rotate < 0:
        raise parser.error(f"Port must be between 1024 and 65535: {args.port!r}")

    # Handle verbosity
    if args.quiet:
        args.verbosity = "quiet"
        logging.getLogger().setLevel(logging.ERROR)
    elif args.very_verbose:
        args.verbosity = "very"
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug:
        args.verbosity = "debug"
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        args.verbosity = "normal"
        logging.getLogger().setLevel(logging.WARNING)
    del args.quiet
    del args.verbose
    del args.very_verbose
    del args.debug

    # Checks whether the output directory is a directory or 
    # that it can be created (parent exists and is a directory)
    if ((args.outdir.exists() and not args.outdir.is_dir()) or
        (args.outdir.parent.exists() and not args.outdir.parent.is_dir())
    ):
        raise parser.error(f"Output directory: cannot create or use {args.outdir!r}")

    return args


def parse(argv):
    """
    Parse arguments from the command line and return a Namespace.

    Arguments are handled and adjusted according to zabbix behaviour and
    user selection (see @postprocess function).
    """
    # The double call to 'parse_args' is for properly separating user provided values from
    # script default values. In order to keep it working as expected *every* value in the parser
    # must have a default (otherwise the next line will prompt the help screen to the user without
    # regardless of real arguments). TODO: use default dict at the top and avoid this double call?
    temp_args = parser.parse_args(argv)

    try:
        _defaults = temp_args.__dict__
        _blanks = dict((key, None) for key in temp_args.__dict__.keys())

        parser.set_defaults(**_blanks)
        uargs = parser.parse_args(argv)
        parser.set_defaults(**_defaults)

    except argparse.ArgumentError:
        raise ValueError(
            "Parse error: should never happen here."
            "Really.. something is wrong.")

    return postprocess(uargs, defs)
