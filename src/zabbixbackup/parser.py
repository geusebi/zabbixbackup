import argparse
from pathlib import Path

from .parser_defaults import PSqlArgs, MySqlArgs
from .parser_post import postprocess


_DESCRIPTION = "zabbix dump for {dbms} inspired and directly translated from..."

def parse(argv):
    """
    Arguments CLI parser.

    What's going on:
        'build_parser' choose the DBMS examining the first argument
        'build_sub_parser' create the actual parser to parse the rest of the arguments
    
    Arguments are then handled and adjusted according to zabbix behaviour
    anduser selection (see @postprocess function).
    
    The double call to 'parse_args' is for properly separating user provided values from
    script default values. In order to keep it working as expected *every* value in the
    parser must have a default (otherwise will prompt the help screen to the user
    regardless of the provided arguments).
    TODO: add credits in the help screen
    """

    main_parser = build_parser()

    main_args, subargv = main_parser(argv)
    dbms = main_args.dbms

    if dbms in ("psql", "pgsql"):
        args = PSqlArgs()
        args.scope["dbms"] = "psql"
    elif dbms in ("mysql", ):
        args = MySqlArgs()
        args.scope["dbms"] = "mysql"
    else:
        raise NotImplementedError(f"DBMS {dbms} not supported")

    sub_parser = build_sub_parser(args)
    args.scope["parser"] = sub_parser

    temp_args = sub_parser.parse_args(subargv)

    try:
        _defaults = temp_args.__dict__
        _blanks = dict((key, None) for key in temp_args.__dict__.keys())

        sub_parser.set_defaults(**_blanks)
        user_args = sub_parser.parse_args(subargv)
        sub_parser.set_defaults(**_defaults)

    except Exception:
        # pylint: disable=W0707:raise-missing-from
        raise ValueError(
            "Parse error: should never happen here."
            "Really.. something is wrong.")

    return postprocess(args, user_args)


def build_parser():
    """
    Create the parser according to user selection (first argument).
    """

    parser = argparse.ArgumentParser(
        "zabbixbackup",
        description=_DESCRIPTION.format(dbms="postgres or mysql"))

    subparsers = parser.add_subparsers(title='DBMS', dest="dbms", required=True)

    subparsers.add_parser(
        'psql',
        aliases=["pgsql"],
        help="(see zabbixbackup psql --help)")

    subparsers.add_parser(
        'mysql',
        help="(see zabbixbackup mysql --help)")

    def _parser(argv):
        subargv = argv[0:1]

        if len(subargv) == 0:
            subargv = ["-h"]

        return parser.parse_args(subargv), argv[1:]

    return _parser


def build_sub_parser(args):
    """
    Create the parser according to user selection (by @build_parser).
    """
    dbms = args.scope["dbms"]

    parser = argparse.ArgumentParser(
        f"zabbixbackup {dbms}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=_DESCRIPTION.format(dbms=dbms))

    parser.add_argument(
        "-z", "--read-zabbix-config",
        help="try to read database host and credentials from Zabbix config. "
            "Implicit if `--zabbix-config` is set.",
        action="store_true",
        default=args.read_zabbix_config)

    parser.add_argument(
        "-Z", "--zabbix-config",
        help="Zabbix config file path. "
        "Implicit if `--read-zabbix-config` is set.",
        default=args.zabbix_config,
        type=Path,
        dest="zbx_config")

    if dbms == "mysql":
        parser.add_argument(
            "-c", "--read-mysql-config",
            help="Read database host and credentials from MySQL config file. "
                "Implicit if `--mysql-config` is set.",
            action="store_true",
            default=args.read_mysql_config)

        parser.add_argument(
            "-C", "--mysql-config",
            help="MySQL config file path. "
                "Implicit if `--read-mysql-config` is set.",
            default=args.mysql_config,
            type=Path)

    parser.add_argument(
        "-D", "--dry-run",
        help="Do not create the actual backup, only show dump commands. "
            "Be aware that the database will be queried for tables selection and "
            "temporary folders and files will be created.",
        default=args.dry_run,
        action="store_true")


    connection = parser.add_argument_group("connection options")

    _host_help = "hostname/IP of DBMS server, to specify a blank value pass '-'."
    if dbms == "psql":
        _host_help += " If host starts with a slash it's interpreted as a socket directory."
        _host_help += " Special rules might apply (see postgre online documentation for sockets)."

    connection.add_argument(
        "-H", "--host",
        help=_host_help,
        default=args.host)

    connection.add_argument(
        "-P", "--port",
        help="DBMS port.",
        default=args.port)

    if dbms == "mysql":
        connection.add_argument(
            "-S", "--socket",
            help="path to DBMS socket file. "
                "Alternative to specifying host.",
            dest="sock",
            default=args.sock)

    connection.add_argument(
        "-u", "--username",
        help="database login user.",
        default=args.user,
        dest="user")

    connection.add_argument(
        "-p", "--passwd",
        help="database login password (specify '-' for an interactive prompt).",
        default=args.passwd)

    login_file = ".pgpass" if dbms == "psql" else "mylogin.cnf"
    connection.add_argument(
        "--keep-login-file",
        help=f"if a credential file is created ({login_file}) do not "
            "delete it on exit.",
        action="store_true",
        default=args.keeploginfile,
        dest="keeploginfile")


    connection.add_argument(
        "--login-file",
        help=f"use '{login_file}' file for the authentication.",
        default=args.loginfile,
        dest="loginfile")

    connection.add_argument(
        "-d", "--database",
        help="database name.",
        default=args.dbname,
        dest="dbname")

    if dbms == "psql":
        connection.add_argument(
            "-s", "--schema",
            help="database schema.",
            default=args.schema)

    connection.add_argument(
        "-n", "--reverse-lookup",
        help="(NOT IMPLEMENTED) perform a reverse lookup of the IP address for the host.",
        action="store_true",
        default=args.rlookup,
        dest="rlookup")


    dump = parser.add_argument_group("dump action options")

    dump.add_argument(
        "-U", "--unknown-action",
        help="action for unknown tables.",
        default=args.unknown,
        choices=("dump", "nodata", "ignore", "fail"),
        dest="unknown")

    dump.add_argument(
        "-M", "--monitoring-action",
        help="action for monitoring table",
        default=args.monitoring,
        choices=("dump", "nodata"),
        dest="monitoring")

    dump.add_argument(
        "-N", "--add-columns",
        help="add column names in INSERT clauses and quote them as needed.",
        default=args.columns,
        action="store_true",
        dest="columns")

    compression = parser.add_argument_group("dump level compression options")

    if dbms == "psql":
        compression.add_argument(
            "-x", "--pgcompression",
            help="passed as-is to pg_dump --compress, might be implied by format.",
            default=args.pgcompression)

        compression.add_argument(
            "-f", "--pgformat",
            help="dump format, will mandate the file output format.",
            choices={"plain", "custom", "directory", "tar"},
            default=args.pgformat)

    if dbms == "mysql":
        compression.add_argument(
            "--mysqlcompression",
            help="dump level compression. "
                "Available formats are xz, gzip and bzip2. Use ':<LEVEL>' to set a compression "
                "level. I.e. --archive xz:6. See documentation for the details.",
            default=args.mysqlcompression)

    files = parser.add_argument_group("configuration files")

    files.add_argument(
        "--save-files",
        help="save folders and other files (see --files).",
        default=args.save_files,
        action="store_true")

    files.add_argument(
        "--files",
        help="save folders and other files as listed in this file. "
            "One line per folder or file, non existant will be ignored. "
            "Directory structure is replicated (copied via 'cp').",
        default=args.files)

    output = parser.add_argument_group("output options")

    output.add_argument(
        "-a", "--archive",
        help="archive level compression. 'tar' to create a tar archive, "
            "'-' to leave the backup uncompressed as a folder. "
            "Other available formats are xz, gzip and bzip2. "
            "Use ':<LEVEL>' to set a compression level. I.e. --archive xz:6",
        default=args.archive)

    output.add_argument(
        "-o", "--outdir",
        help="save database dump to 'outdir'.",
        default=args.outdir,
        type=Path)

    output.add_argument(
        "-r", "--rotate",
        help="rotate backups while keeping up 'R' old backups."
            "Uses filename to match '0=keep everything'.",
        default=args.rotate,
        type=int)

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
        default=args.quiet)

    verbosity_group.add_argument(
        "-v", "--verbose",
        help="print informations.",
        action="store_true",
        default=args.verbose)

    verbosity_group.add_argument(
        "-V", "--very-verbose",
        help="print even more informations.",
        action="store_true",
        default=args.very_verbose)

    verbosity_group.add_argument(
        "--debug",
        help="print everything.",
        action="store_true",
        default=args.debug)

    return parser
