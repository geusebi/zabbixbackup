
if __name__ == "__main__":
    import os
    from sys import argv
    import logging
    import tempfile
    from pathlib import Path
    
    from .parser import parse
    from .utils import pretty_log_args
    from .backup_postgre import backup_postgresql
    from .backup_mysql import backup_mysql
    from .archiver import save_files, archive
    from .rotation import rotate

    # Parse and preprocess cli arguments
    args = parse(argv[1:])
    scope = args.scope

    # Create temporary file for the log in the current directory
    raw_fh, tmp_log = tempfile.mkstemp(prefix="zabbixbackup_", suffix=".log", text=True, dir=".")
    tmp_log = Path(tmp_log)
    log_fh = os.fdopen(raw_fh, "w")
    logger = logging.getLogger()
    logger_handler = logging.StreamHandler(log_fh)
    logger.addHandler(logger_handler)

    # Create temporary output directory for the backup
    tmp_dir = tempfile.mkdtemp(prefix="zabbix_", dir=".")
    tmp_dir = Path(tmp_dir)
    scope["tmp_dir"] = tmp_dir

    logging.debug(f"Temporary log file: {tmp_log}")

    # Pretty print arguments as being parsed and processed
    pretty_log_args(args)

    if scope["dbms"] == "psql":
        backup_postgresql(args)
    elif scope["dbms"] == "mysql":
        backup_mysql(args)

    save_files(args)

    # Detach  file logger and save log into place 
    logger.removeHandler(logger_handler)
    log_fh.close()
    tmp_log.rename(tmp_dir / "dump.log")

    # Archive, compress and move the backup to the final destination
    archive(args)

    # Rotate backups
    rotate(args)
