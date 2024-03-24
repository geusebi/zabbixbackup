import os
import logging


def pretty_log_namespace(ns):
    """Print arguments via 'logging.info' in a readable way"""
    dict_args = vars(ns)
    keys = (
        "type", "read_zabbix_config", "zabbix_config", "read_mysql_config", "mysql_config",
        "dry_run", "host", "port", "sock", "user", "passwd", "dbname", "schema",
        "rlookup", "save_files", "files", "unknown", "columns", "compression",
        "format", "rotate", "outdir", "verbosity"
    )

    str_args = ["Arguments:"]
    for key in keys:
        value = getattr(ns, key, None)
        if value is None:
            continue
        if key == "passwd":
            str_args.append(f"    {key:<24}: [omissis]")
        else:
            str_args.append(f"    {key:<24}: {value}")

    for key, value in dict_args.items():
        if key in keys:
            continue
        str_args.append(f"    {key:<24}: {value}")

    logging.info("\n".join(str_args))


if __name__ == "__main__":
    from sys import argv
    from .parser import parse
    from .backup import backup_postgresql, backup_mysql
    from .rotation import rotate
    from .cpfiles import copyfiles
    from types import SimpleNamespace as NS
    from pathlib import Path
    import tempfile


    # Parse and preprocess cli arguments
    args = parse(argv[1:])

    # Namespace used to pass variables thru the stages
    # (should be considered as extra or derived arguments)
    extra = NS()

    # Create temporary file for the log in the current directory
    raw_fh, tmp_log = tempfile.mkstemp(prefix="zbx_backup_", suffix=".log", text=True, dir=".")
    log_fh = os.fdopen(raw_fh, "w")
    logger = logging.getLogger()
    logger_handler = logging.StreamHandler(log_fh)
    logger.addHandler(logger_handler)

    # Create temporary directory for the backup
    tmp_dir = tempfile.mkdtemp(prefix="zbx_backup_", dir=".")
    extra.tmp_dir = tmp_dir

    # Pretty print arguments as being parsed and processed
    pretty_log_namespace(args)

    if args.type == "psql":
        backup_postgresql(args, extra)
    elif args.type == "mysql":
        backup_mysql(args, extra)

    # Copy files to backup directory
    if args.save_files is True:
        files = args.files
        if files == "-":
            files = Path(__file__).parent / "assets" / "files"

        copyfiles(files, Path(tmp_dir) / "root")

    # Move everything into place (log and backup)
    logger.removeHandler(logger_handler)
    log_fh.close()
    Path(tmp_log).rename(Path(tmp_dir) / "dump.log")
    Path(tmp_dir).rename(args.outdir / extra.name)

    # Rotate logs
    if args.rotate > 0:
        rotate(args, extra)
