import logging
from sys import exit
from os import environ
import atexit
from copy import deepcopy
from pathlib import Path
from .utils import (
    CurryCommand, parse_zabbix_version, create_name,
    preprocess_tables_lists, try_find_sockets,
)


def backup_mysql(args):
    logging.verbose(f"DBMS: MySQL or MariaSql")

    # Phase 0: setup authentication
    _mysql_auth(args)


    # Phase 1: Fetch database version
    select_db_version = "SELECT optional FROM dbversion;"
    raw_version = _mysql_query(args, select_db_version, "zabbix version query").exec()
    if raw_version is None:
        logging.fatal("Could not retrieve db version (see logs using --debug)")
        exit(1)

    version, _ = parse_zabbix_version(raw_version)
    logging.info(f"Zabbix version: {version}")

    name = create_name(args, version)
    logging.info(f"Backup base name: {name}")

    # Phase 2: Perform the actual backup
    dump_args = []
    
    # select and filter tables: done here and passed to _mysql_dump for simplicity
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.dbname}';")

    table_cmd = _mysql_query(args, table_list_query, "zabbix tables list query")
    table_list = sorted(table_cmd.exec())
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    schema_path = Path(args.scope["tmp_dir"]) / f"schemas.sql"
    data_path = Path(args.scope["tmp_dir"]) / f"data.sql"

    dump_schema_args = [
        "--opt", "--single-transaction", "--skip-lock-tables",
        "--no-data", "--routines",
        "--result-file", schema_path, args.dbname,
        ]
    dump_data_args = [
        "--opt", "--single-transaction", "--skip-lock-tables",
        "--no-create-info", "--skip-extended-insert", "--skip-triggers",
        "--result-file", data_path, args.dbname,
    ]

    if fail:
        logging.error(f"Unknwon tables: aborting ({fail!r})")
        exit(1)

    if nodata:
        for table in nodata:
            dump_data_args += ["--ignore-table", f"{args.dbname}.{table}"]

    if ignore:
        for table in ignore:
            dump_schema_args += ["--ignore-table", f"{args.dbname}.{table}"]
            dump_data_args += ["--ignore-table", f"{args.dbname}.{table}"]

    dump_schema = _mysql_dump(args, dump_schema_args, f"Dump schema command", logging.info)
    dump_data = _mysql_dump(args, dump_data_args, f"Dump data command", logging.info)

    if not args.dry_run:
        dump_schema.exec()
        dump_data.exec()

    args.scope["name"], args.scope["version"] = name, version 


def _mysql_auth(args):
    args.scope["env"] = deepcopy(environ)
    args.scope["env_extra"] = {}

    if args.loginfile is not None:
        pass
    # Create temporary mylogin.cnf file
    elif args.passwd is not None:
        logincnf = Path(f"./mylogin.cnf")
        with logincnf.open("w") as fh:
            fh.writelines([
                f"[client]\r\n",
                f"password={args.passwd}\r\n",
            ])
        logincnf.chmod(0o600)
        if not args.keeploginfile:
            atexit.register(lambda: logincnf.unlink())
        args.loginfile = "./mylogin.cnf"


def _mysql_query(args, query, description="query", log_func=logging.debug):
    # mysql command will be used to inspect the database
    extra = []
    if args.read_mysql_config:
        extra += ["--defaults-file", args.mysql_config, ]

    if args.loginfile:
        extra += [f"--defaults-extra-file={args.loginfile}", ]

    if args.sock is None:
        extra += ["--host", args.host]
    else:
        extra += ["--socket", args.sock]

    query = CurryCommand(
        [
            "mysql",
            "--login-path=client",
        ] + extra + [
            "--user", args.user,
            "--port", args.port,
            "--database", args.dbname,
            "--skip-column-names",
            "--execute"
        ] + [query]
        , args.scope["env"], args.scope["env_extra"]
    )

    log_func(f"{description}: \n{query.reprexec()}")

    return query


def _mysql_dump(args, params, description="dump cmd", log_func=logging.debug):
    extra = []
    if args.read_mysql_config:
        extra += ["--defaults-file", args.mysql_config, ]

    if args.loginfile:
        extra += [f"--defaults-extra-file={args.loginfile}", ]

    if args.sock is None:
        extra += ["--host", args.host]
    else:
        extra += ["--socket", args.sock]

    extra_args = []
    if args.columns:
        extra_args += ["--complete-insert", "--quote-names", ]
    
    if args.verbosity in ("very", "debug"):
        extra_args += ["--verbose"]

    cmd = CurryCommand(
        [
            "mysqldump",
        ] + extra + [
            "--user", args.user,
            "--port", args.port,
        ] + extra_args + params,
        args.scope["env"], args.scope["env_extra"]
    )

    log_func(f"{description}: \n{cmd.reprexec()}")

    return cmd
