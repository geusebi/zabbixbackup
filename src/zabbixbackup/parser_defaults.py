from types import SimpleNamespace as NS
from pathlib import Path
from dataclasses import dataclass, field

# Script default values
# (these are important to allow to separate user provided values during parsing)
# 'dest' name actions in parsers must be the same as in these dataclasses

@dataclass
class PSqlArgs(object):
    read_zabbix_config: bool = False
    zabbix_config: Path      = Path("/etc/zabbix/zabbix_server.conf")

    dry_run: bool            = False
    host: str                = "127.0.0.1"
    port: int                = 5432
    user: str                = "zabbix"
    passwd: str              = None
    dbname: str              = "zabbix"
    schema: str              = "public"
    rlookup: bool            = True

    save_files: bool         = True
    files: str|Path          = "-"

    unknown: str             = "ignore"
    monitoring: str          = "nodata"
    columns: bool            = False
    compression: str         = None
    format: str              = "custom"
    outdir: str|Path         = Path(".")
    rotate: int              = 0

    quiet: bool              = False
    verbose: bool            = True
    very_verbose: bool       = False
    debug: bool              = False

    verbosity: str           = None # automatically set during parser post process
    archive: str             = "-"
    scope: dict              = field(default_factory=dict)

PSqlArgs._keys = [
    "read_zabbix_config", "zabbix_config",
    "host", "port", "user", "passwd",
    "dbname", "schema", "rlookup",
    "save_files", "files",
    "unknown", "monitoring",
    "columns", "compression", "format",
    "rotate", "outdir", "archive",
    "dry_run", "verbosity",
]


@dataclass
class MySqlArgs(object):
    read_zabbix_config: bool = False
    zabbix_config: Path      = Path("/etc/zabbix/zabbix_server.conf")
    read_mysql_config: bool  = False
    mysql_config: str|Path   = "/etc/mysql/my.cnf"

    dry_run: bool            = False
    host: str                = "127.0.0.1"
    port: int                = 3306
    sock: Path|None          = None
    user: str                = "zabbix"
    passwd: str              = "-"
    dbname: str              = "zabbix"
    rlookup: bool            = True

    save_files: bool         = True
    files: str|Path          = "-"

    unknown: str             = "ignore"
    monitoring: str          = "nodata"
    columns: bool            = False
    outdir: str|Path         = Path(".")
    rotate: int              = 0

    quiet: bool              = False
    verbose: bool            = True
    very_verbose: bool       = False
    debug: bool              = False

    verbosity: str           = None # automatically set during parser post process
    archive: str             = "-"
    scope: dict            = field(default_factory=dict)

MySqlArgs._keys = [
    "read_zabbix_config", "zabbix_config", "read_mysql_config", "mysql_config",
    "host", "port", "sock", "user", "passwd",
    "dbname", "rlookup",
    "save_files", "files",
    "unknown", "monitoring",
    "columns", "rotate", "outdir", "archive",
    "dry_run", "verbosity",
]