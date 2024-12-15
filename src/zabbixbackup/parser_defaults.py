"""
Zabbixbackup defaults configuration.
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Script default values
# (these are important to allow to separate user provided values during parsing)
# 'dest' name actions in parsers must be the same as in these dataclasses

# pylint: disable=W0212:protected-access
# pylint: disable=R0902:too-many-instance-attributes

@dataclass
class PSqlArgs:
    """Zabbixbackup defaults configuration for PostgreSQL."""
    read_zabbix_config: bool = False
    zabbix_config: Path      = Path("/etc/zabbix/zabbix_server.conf")

    dry_run: bool               = False
    host: str                   = "127.0.0.1"
    port: int                   = 5432
    user: str                   = "zabbix"
    passwd: str                 = None
    keeploginfile: bool         = False
    loginfile: Optional[Path]   = None
    dbname: str                 = "zabbix"
    schema: str                 = "public"
    rlookup: bool               = True

    save_files: bool            = False
    files: Path                 = "-"

    unknown: str                = "ignore"
    monitoring: str             = "nodata"
    columns: bool               = False
    pgformat: str               = "custom"
    pgcompression: str          = None
    outdir: Path                = Path(".")
    rotate: int                 = 0

    quiet: bool                 = False
    verbose: bool               = True
    very_verbose: bool          = False
    debug: bool                 = False

    verbosity: str              = None # automatically set during parser post process
    archive: str                = "-"
    scope: dict                 = field(default_factory=dict)

PSqlArgs._keys = [
    "read_zabbix_config", "zabbix_config",
    "host", "port", "user", "passwd", "keeploginfile", "loginfile",
    "dbname", "schema", "rlookup",
    "save_files", "files",
    "unknown", "monitoring",
    "columns", "pgformat", "pgcompression",
    "rotate", "outdir", "archive",
    "dry_run", "verbosity",
]


@dataclass
class MySqlArgs:
    """Zabbixbackup defaults configuration for MySQL or MariaSQL"""
    read_zabbix_config: bool    = False
    zabbix_config: Path         = Path("/etc/zabbix/zabbix_server.conf")
    read_mysql_config: bool     = False
    mysql_config: Path          = "/etc/mysql/my.cnf"

    dry_run: bool               = False
    host: str                   = "127.0.0.1"
    port: int                   = 3306
    sock: Optional[Path]        = None
    user: str                   = "zabbix"
    passwd: str                 = None
    keeploginfile: bool         = False
    loginfile: Optional[Path]   = None
    dbname: str                 = "zabbix"
    rlookup: bool               = True

    save_files: bool            = False
    files: Path                 = "-"

    unknown: str                = "ignore"
    monitoring: str             = "nodata"
    columns: bool               = False
    mysqlcompression: str       = "gzip:6"
    outdir: Path                = Path(".")
    rotate: int                 = 0

    quiet: bool                 = False
    verbose: bool               = True
    very_verbose: bool          = False
    debug: bool                 = False

    verbosity: str              = None # automatically set during parser post process
    archive: str                = "-"
    scope: dict                 = field(default_factory=dict)

MySqlArgs._keys = [
    "read_zabbix_config", "zabbix_config", "read_mysql_config", "mysql_config",
    "host", "port", "sock", "user", "passwd", "keeploginfile", "loginfile",
    "dbname", "rlookup",
    "save_files", "files",
    "unknown", "monitoring",
    "columns", "mysqlcompression",
    "rotate", "outdir", "archive",
    "dry_run", "verbosity",
]
