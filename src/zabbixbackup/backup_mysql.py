import logging
from os import fdopen, environ
import tempfile
import shutil
import atexit
from pathlib import Path
from subprocess import PIPE

from .utils import (
    DPopen, build_compress_command, check_binary, parse_zabbix_version,
    preprocess_tables_lists, process_repr,
)

logger = logging.getLogger(__name__)


def backup_mysql(args):
    logger.verbose("DBMS: MySQL or MariaSql")
    if not check_binary("mysql", "mysqldump"):
        return 1, "Missing binaries: check 'mysql' and 'mysqldump' are available and in PATH"

    args.scope["env"] = {}

    # Phase 0: setup authentication
    _mysql_auth(args)

    # Phase 1: Fetch database version
    select_db_version = "SELECT optional FROM dbversion;"
    raw_version = _mysql_query(args, select_db_version, "zabbix version query")
    if raw_version is None:
        return 2, "Could not retrieve db version (see logs using --debug)"

    version, _ = parse_zabbix_version(raw_version)
    with open("zabbix_dbversion", "w", encoding="utf-8") as fh:
        fh.writelines(["mysql\n", "{version}\n"])

    logging.info("Zabbix version: %s", version)

    # Phase 2: Perform the actual backup

    # select and filter tables: done here and passed to _mysql_dump for simplicity
    table_list_query = (
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{args.dbname}';")

    table_cmd = _mysql_query(args, table_list_query, "zabbix tables list query")
    if table_cmd is None:
        return 3, "Could not retrieve table list (see logs)"

    table_list = sorted(table_cmd)
    ignore, nodata, fail = preprocess_tables_lists(args, table_list)

    schema_ignores = []
    data_ignores = []
    if fail:
        return 4, f"Unknwon tables: aborting ({fail!r})"

    if nodata:
        for table in nodata:
            data_ignores += ["--ignore-table", f"{args.dbname}.{table}"]

    if ignore:
        for table in ignore:
            schema_ignores += ["--ignore-table", f"{args.dbname}.{table}"]
            data_ignores += ["--ignore-table", f"{args.dbname}.{table}"]

    # Phase 3: perform acqual dump

    # dump schemas
    schema_params = [
        "--opt", "--single-transaction", "--skip-lock-tables",
        "--no-data", "--routines", ]
    schema_outpath = Path("schemas_dump.sql")

    schema_status = _mysql_dump(
        args, schema_params, schema_ignores, schema_outpath,
        "Dump schema command", logging.info)

    if not schema_status:
        return 5, "Could not execute schema dump (see logs)"

    # dump data
    data_outpath = Path("data_dump.sql")
    data_params = [
        "--opt", "--single-transaction", "--skip-lock-tables",
        "--no-create-info", "--skip-extended-insert", "--skip-triggers",
    ]
    dump_status = _mysql_dump(
        args, data_params, data_ignores, data_outpath,
        "Dump data command", logging.info)

    if not dump_status:
        return 5, "Could not execute data dump (see logs)"

    return 0, "+OK"


def _mysql_auth(args):
    # Use provided loginfile and leave it untouched
    if args.loginfile is not None:
        pass

    # Create temporary mylogin.cnf file
    elif args.passwd is not None:
        logincnf_fd, logincnf_path = tempfile.mkstemp(prefix="logincnf_", text=True)
        logincnf_path = Path(logincnf_path)
        fh = fdopen(logincnf_fd, "w")

        logincnf_path.chmod(0o600)
        fh.writelines([
                "[client]\n",
                f"password={args.passwd}\n",
            ])
        fh.close()

        abs_logincnf = logincnf_path.absolute()
        atexit.register(abs_logincnf.unlink)

        args.loginfile = logincnf_path

    if args.keeploginfile:
        shutil.copy(args.loginfile, "./mylogin.cnf")


def _mysql_query(args, query, description="query", log_func=logging.debug):
    dbname = args.dbname
    env_extra = args.scope["env"]

    # mysql command will be used to inspect the database
    query_cmd = [
        "mysql",
        "--login-path=client",
    ]

    if args.read_mysql_config:
        query_cmd += ["--defaults-file", args.mysql_config, ]

    if args.loginfile:
        query_cmd += [f"--defaults-extra-file={args.loginfile}", ]

    if args.sock is None:
        query_cmd += ["--host", args.host]
    else:
        query_cmd += ["--socket", args.sock]

    query_cmd += [
        "--user", args.user,
        "--port", args.port,
        "--database", dbname,
        "--skip-column-names",
        "--execute",
        query,
    ]

    query_cmd = tuple(map(str, query_cmd))
    query_env = {**environ, **env_extra}

    log_func(f"{description}: \n{process_repr(query_cmd, env_extra)}")

    exec_query = DPopen(query_cmd, env=query_env, stdout=PIPE, text=True)
    stdout, stderr = exec_query.communicate()

    if exec_query.returncode != 0:
        if stderr is not None:
            logging.fatal(stderr)
        return None

    return stdout.splitlines()


def _mysql_dump(
    args, params, ignoring, outpath, description="dump cmd", log_func=logging.debug
):
    dbname = args.dbname
    env_extra = args.scope["env"]

    # do we have a compression flag for mysql?
    compressor_profile = args.scope.get("mysqlcompression", None)

    # base command and pre-flags based on user selection
    dump_cmd = [
        "mysqldump",
    ]

    if args.read_mysql_config:
        dump_cmd += ["--defaults-file", args.mysql_config]

    if args.loginfile:
        dump_cmd += [f"--defaults-extra-file={args.loginfile}"]

    if args.sock is None:
        dump_cmd += ["--host", args.host]
    else:
        dump_cmd += ["--socket", args.sock]

    dump_cmd += [
        "--user", args.user,
        "--port", args.port,
        "--compression-algorithms", "zlib,zstd,uncompressed",
    ]

    if args.columns:
        dump_cmd += ["--complete-insert", "--quote-names", ]

    if args.verbosity in ("very", "debug"):
        dump_cmd += ["--verbose"]

    # parameters from outside (data or schema)
    dump_cmd += params

    # if there's no compression let mysqldump save the file
    if compressor_profile is None:
        dump_cmd += ["--result-file", outpath]

    # database to dump and tables exclusion
    dump_cmd += [dbname]
    dump_cmd += ignoring


    # finalize dump command
    dump_env = {**environ, **env_extra}
    dump_cmd = tuple(map(str, dump_cmd))
    log_func(f"{description}: \n{process_repr(dump_cmd, env_extra)}")

    # setup a compress command if needed
    if compressor_profile:
        env, _, ext, compressor = build_compress_command(compressor_profile)

        compr_env = {**environ, **env_extra, **env}
        compr_cmd = compressor + (outpath.name + ext, )
        log_func(f"{description} compression: \n{process_repr(compr_cmd, env)}")

    # don't execute if dry run is enabled
    if args.dry_run:
        return True

    # either run a simple dump or a 'dump | compress'
    dump = DPopen(dump_cmd, env=dump_env, stdout=PIPE, text=True)

    # pylint: disable=E0606, R1705
    if not compressor_profile:
        dump.communicate()
        return dump.returncode == 0
    else:
        compress = DPopen(compr_cmd, env=compr_env, stdin=dump.stdout)
        compress.communicate()
        return compress.returncode == 0
