from pathlib import Path
import logging
from getpass import getpass
from .parser_defaults import PSqlArgs, MySqlArgs
import sys


__all__ = ["postprocess"]


def postprocess(args: PSqlArgs|MySqlArgs, user_args):
    """
    Adjust the arguments according to zabbix behaviour and user selection.

    See comments inside this function and _handle* functions.
    """
    parser = args.scope["parser"]
    dbms = args.scope["dbms"]

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

    # Hostname / Socket: special case
    if user_args.host == "-":
        user_args.host = ""

    # Check port limits
    if user_args.port is not None and not (1024 <= user_args.port <= 65535):
        raise parser.error(f"Port must be between 1024 and 65535: {user_args.port!r}")

    # Implicit read from zabbix config if a file is provided
    if user_args.zbx_config:
        user_args.read_zabbix_config = True

    if dbms == "mysql":
        # Implicit read from mysql config if a file is provided
        if user_args.mysql_config:
            user_args.read_mysql_config = True

    # Implicit save_files if files is provided
    if user_args.files:
        user_args.save_files = True
        user_args.files = Path(user_args.files)

    
    for key, value in vars(user_args).items():
        if value is not None:
            setattr(args, key, value)

    if args.read_zabbix_config:
        _handle_zabbix_conf(args, user_args)

    if args.rotate < 0:
        raise parser.error(f"Rotate must be 0 or positive: {args.rotate!r}")

    # Collapse verbosity to a single variable ('verbosity')
    _handle_verbosity(args)
    
    # Handle archiving, set archive type and compression level
    _handle_archiving(args)

    # Checks whether the output directory is a directory or 
    # that it can be created (parent exists and is a directory)
    _handle_output(args)

    # Prompt for password if necessary (do it last to fail early on other arguments)
    if args.loginfile is None and args.passwd == "-":
        print("(echo disabled for password input)", file=sys.stderr)
        args.passwd = getpass("password: ")

    return args


def _handle_archiving(args):
    parser = args.scope["parser"]
    
    # Handle archiving
    if args.archive == "-":
        args.scope["archive_env"] = None
        args.scope["archive_command"] = None
        args.scope["archive_extension"] = None
        return
    
    valid = True
    opts = []

    if ":" not in args.archive:
        archiver = args.archive
        level = "9"
    elif ":" in args.archive:
        archiver, level = args.archive.split(":")

    if archiver == "xz" and level.endswith("e"):
        level = level[:-1]
        opts.append("-e")

    if not level.isdecimal() or len(level) != 1:
        valid = False
    else:
        opts.append(f"-{level}")

    if archiver not in ("xz", "gzip", "bzip2"):
        valid = False

    if not valid:
        raise parser.error(f"Invalid archive format: {args.archive!r}")

    extensions = {"xz": ".tar.xz", "gzip": ".tar.gz", "bzip2": ".tar.bz2"}
    env_map = {"xz": "XZ_OPT", "gzip": "GZIP", "bzip2": "BZIP2"}
    tar_map = {"xz": "J", "gzip": "z", "bzip2": "j"}
    
    env_name = env_map[archiver]
    tar_compr_opts = tar_map[archiver]
    string_opts = " ".join(opts)

    args.scope["archive_env"] = {env_name: string_opts}
    args.scope["archive_command"] = ["tar", f"-c{tar_compr_opts}f"]
    args.scope["archive_extension"] = extensions[archiver]


def _handle_verbosity(args):
    """Set verbosity level."""
    logger = logging.getLogger()
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


def _handle_output(args):
    """Check whether the output directory is useable."""
    parser = args.scope["parser"]

    if ((args.outdir.exists() and not args.outdir.is_dir()) or
        (args.outdir.parent.exists() and not args.outdir.parent.is_dir())
    ):
        raise parser.error(f"Output directory: cannot create or use {args.outdir!r}")


def _handle_zabbix_conf(args, user_args):
    # args is a mix of user provided arguments and defaults
    # user_args has only values provided by the user
    # we need to update args if and only if the user has not
    # provided a value for something that comes from the zabbix
    # configuration file

    zconfig = _zabbix_try_read_config(args.zabbix_config)

    zbx_var_map = (
        ("DBHost", "host", str, ),
        ("DBPort", "port", int, ),
        ("DBName", "dbname", str, ),
        ("DBSchema", "schema", str, ),
        ("DBUser", "user", str, ),
        ("DBPassword", "passwd", str, ),
        ("DBSocket", "sock", Path, ),
    )

    zconfig = _map_clean_vars(zconfig, zbx_var_map)

    # For postgres prefer socket over host in zabbix configuration
    if args.scope["dbms"] == "psql":
        if "sock" in zconfig and "host" not in zconfig:
            zconfig["dbms"] = zconfig["sock"]
            del zconfig["sock"]

    # Copy value from the config if it isn't provided by the user  
    for key, value in zconfig.items():
        user_value = getattr(user_args, key, None)
        if user_value is None:
            setattr(args, key, value)


def _zabbix_try_read_config(path):
    """
    Try reading key value pairs from zabbix config file.
    
    Empty values are skipped silently.
    The defaults from the last shipped version are used as a base. Then are
    overriden by defaults from 'path' and, lastly, from the actual specified values.
    """
    config = []

    with path.open("r") as fh:
        for line in map(str.strip, fh):
            if line == "" or line.startswith("#"):
                continue
            
            key, eq, value = map(str.strip, line.partition("="))
            if eq == "=" and len(key) and len(value):
                config[key] = value

    return config


def _map_clean_vars(config, map_clean_var):
    """Helper function to merge configuration variables."""
    return dict((
        (new_name, type(config[key]))
        for key, new_name, type in map_clean_var
        if key in config
    ))