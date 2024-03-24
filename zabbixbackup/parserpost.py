from .parserutils import *
from collections import defaultdict
from pathlib import Path
import logging
from types import SimpleNamespace as NS
from getpass import getpass
import sys


__all__ = ["postprocess"]


# Shouldn't have done that.. it works.. I hope
logging.VERBOSE= 17
logging.addLevelName(17, "VERBOSE")
def _verbose(msg, *args, **kwargs):
    logging.log(logging.VERBOSE, msg, *args, **kwargs)
logging.verbose = _verbose
logger = logging.getLogger()


def postprocess(parser, user_args, def_args):
    """
    Adjust the arguments according to zabbix behaviour and user selection.

    See comments inside this function and _handle* functions.
    """
    # user_args: actual provided arguments
    # def_args: only defaults via argparse
    # local

    # The final arguments are stored in args directly, the precedence order is:
    #
    #   1. user provided
    #   2. from configuration files
    #   3. from configuration files defaults
    #   4. from the last shipped default configuration files
    #   5. from this script default
    #
    # I.e. CLI arguments are the most important.
    
    # Precedence lists in the form of {key: [values...]}
    # where local_args[key][0] is the selected final value 
    local_args = defaultdict(list, {})

    # Hostname / Socket: special case
    if user_args.host == "-":
        user_args.host = ""
    if user_args.sock == "-":
        user_args.sock = ""

    # Port number: special case. To show mysql and psql default values in the help,
    # the value is stored unchecked as a string. Actual conversion and defaults are handled here
    _handle_port(parser, user_args, def_args)

    # Implicit read from zabbix config if a file is provided
    if user_args.zbx_config:
        user_args.read_zabbix_config = True

    # Implicit read from mysql config if a file is provided
    if user_args.mysql_config:
        user_args.read_mysql_config = True

    # Implicit save_files if files is provided
    if user_args.files:
        user_args.save_files = True

    # User provided values
    for key, value in vars(user_args).items():
        if value is not None:
            local_args[key].append(value)

    # Add zabbix configuration values to local_args
    if user_args.read_zabbix_config:
        zbx_config = user_args.zbx_config
        if zbx_config is None:
            def_args.zabbix_config
        _handle_zabbix_conf(zbx_config, local_args)

    # Add default args from this script to local_args
    for key, value in vars(def_args).items():
        local_args[key].append(value)

    # Flatten the arguments namespace
    args = NS()
    for key, values in local_args.items():
        setattr(args, key, values[0])

    # Prompt for password if necessary
    if args.passwd == "-":
        print("(echo disabled for password input)", file=sys.stderr)
        args.passwd = getpass("password: ")

    # Clean parameters based on dbms selection
    _handle_dbms_selection(parser, user_args, args)

    if args.rotate < 0:
        raise parser.error(f"Rotate must be 0 or positive: {args.rotate!r}")

    # Collapse verbosity to a single variable ('verbosity')
    _handle_verbosity(parser, args)

    # Checks whether the output directory is a directory or 
    # that it can be created (parent exists and is a directory)
    _handle_output(parser, args)

    return args


def _handle_port(parser, user_args, def_args):
    # A little redundant but it's better to keep simmetry:
    # if user provided a DBMS or if it hasn't and the default DBMS is X then set port accordingly
    if user_args.type == "mysql" or (user_args.type is None and def_args.type == "mysql"):
        def_args.port = 3306
    elif user_args.type == "psql" or (user_args.type is None and def_args.type == "psql"):
        def_args.port = 5432

    if user_args.port is not None:
        if not user_args.port.isdecimal():
            raise parser.error(f"Port must be integer: {user_args.port!r}")
        user_args.port = int(user_args.port)

        if not (1024 <= user_args.port <= 65535):
            raise parser.error(f"Port must be between 1024 and 65535: {user_args.port!r}")


def _handle_zabbix_conf(zbx_config, local_args):
    # We read last shipped configuration defaults + local configuration default (zdefconfig)
    # and proper configuration values (zconfig).
    last_shipped_config = Path(__file__).parent / "assets" / "zabbix_server.conf"
    defconfig = zabbix_try_read_defaults(last_shipped_config)
    zdefconfig = zabbix_try_read_defaults(zbx_config, defconfig)
    zconfig = zabbix_try_read_config(zbx_config)

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
        local_args[key].append(value)

    # Add default configuration values to the precedence list
    for key, value in zdefconfig.items():
        local_args[key].append(value)


def _handle_dbms_selection(parser, user_args, args):
    if args.type == "psql":
        if user_args.mysql_config or user_args.read_mysql_config:
            raise parser.error(f"MySQL parameter specified with wrong db type: {args.type!r}")
        del args.mysql_config
        del args.read_mysql_config
        
        if user_args.host is not None and user_args.sock is not None:
            logging.warn(
                "Conflict, host and socket provided, "
                "socket will takes precedence.")
        if user_args.sock is not None:
            args.host = user_args.sock
    elif args.type == "mysql":
        if user_args.schema:
            raise parser.error(f"Schema name specified with wrong db type: {args.type!r}")
        if user_args.format:
            raise parser.error(f"Format kind specified with wrong db type: {args.type!r}")
        del args.schema
        del args.format


def _handle_verbosity(parser, args):
    # Handle verbosity
    if args.quiet:
        args.verbosity = "quiet"
        logger.setLevel(logging.ERROR)
    elif args.very_verbose:
        args.verbosity = "very"
        logger.setLevel(logging.VERBOSE)
    elif args.debug:
        args.verbosity = "debug"
        logger.setLevel(logging.DEBUG)
    else:
        args.verbosity = "normal"
        logger.setLevel(logging.INFO)

    del args.quiet
    del args.verbose
    del args.very_verbose
    del args.debug


def _handle_output(parser, args):
    if ((args.outdir.exists() and not args.outdir.is_dir()) or
        (args.outdir.parent.exists() and not args.outdir.parent.is_dir())
    ):
        raise parser.error(f"Output directory: cannot create or use {args.outdir!r}")
