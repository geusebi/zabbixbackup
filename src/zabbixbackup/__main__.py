

if __name__ == "__main__":
    import os
    import sys
    import logging
    from pathlib import Path
    from .parser import parse
    from .utils import create_name, pretty_log_args
    from .backup_postgre import backup_postgresql
    from .backup_mysql import backup_mysql
    from .archiver import save_files, archive
    from .rotation import rotate
    import atexit

    logger = logging.getLogger(__name__)

    # Parse and preprocess cli arguments
    args = parse(sys.argv[1:])
    scope = args.scope

    # TODO: rlookup here
    outdir = args.outdir
    abs_outdir = outdir.absolute()

    name = create_name(args)
    archive_dir = outdir / name
    abs_archive_dir = archive_dir.absolute()

    # Chdir into this backup directory
    logger.debug("Create archive diretory and chdir to it: %s", archive_dir)
    prev_cwd = Path(os.getcwd()).absolute()
    atexit.register(lambda: os.chdir(prev_cwd))
    archive_dir.mkdir()
    os.chdir(archive_dir)

    log_path = Path("dump.log")

    # Create log in the destination directory
    logger.debug("Log file: %s", log_path)
    log_fh = log_path.open("w", encoding="utf-8")

    logger_handler = logging.StreamHandler(log_fh)
    logger_handler.setLevel(logging.NOTSET)
    logger.addHandler(logger_handler)

    logger.debug("Log file: %s", log_path)

    # Pretty print arguments as being parsed and processed
    pretty_log_args(args)

    if scope["dbms"] == "psql":
        status, message = backup_postgresql(args)
    elif scope["dbms"] == "mysql":
        status, message = backup_mysql(args)
    else:
        status, message = 100, "invalid dbms {scope['dbms']}"

    # exit immediately if something went wrong
    if status != 0:
        logger.fatal(message)
        sys.exit(status)

    save_files(args)

    # Detach file logger
    logger.removeHandler(logger_handler)
    log_fh.close()

    # No file logging from here

    # From now on operate from backups diretory
    os.chdir(abs_outdir)
    # Archive, compress and move the backup to the final destination
    archive_path = archive(abs_archive_dir, args)

    # Rotate backups
    os.chdir(abs_outdir)
    rotate(args)

    print(archive_path)
