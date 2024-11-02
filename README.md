# zabbixbackup

zabbix dump for mysql and psql inspired and directly translated from @nopotorino et al

## Install
```
pip install zabbixbackup
```

## Usage

See `python3 -m zabbixbackup --help`

```
python3 -m zabbixbackup
    [-h] [-t {mysql,psql}] [-z] [-Z ZBX_CONFIG] [-c] [-C MYSQL_CONFIG] [-D]
    [-H HOST] [-P PORT] [-S SOCK] [-u USER] [-p PASSWD] [-d DBNAME] [-s SCHEMA]      
    [-n] [-U {dump,nodata,ignore,fail}] [-M {dump,nodata}] [-N] [--save-files]       
    [--files FILES] [-x COMPRESSION] [-f {directory,tar,plain,custom}] [-r ROTATE]   
    [-o OUTDIR] [-q | -v | -V | --debug]

```

### General options
**`-h`\
`--help`**

Show this help message and exit.

**`-t {mysql,psql}`\
`--type {mysql,psql}`**

Select the DBMS type.
(default: `psql`)

**`-z`\
`--read-zabbix-config`**

Try to read database host and credentials from Zabbix config.
Implicit if `--zabbix-config` is set by the user. (default: `False`)

**`-Z ZBX_CONFIG`\
`--zabbix-config ZBX_CONFIG`**

Zabbix config file path. (default: `/etc/zabbix/zabbix_server.conf`)

**`-c`\
`--read-mysql-config`**

MySQL specific: Read database host and credentials from MySQL config file.
Implicit if `--mysql-config` is set by the user. (default: `False`)

**`-C MYSQL_CONFIG`\
`--mysql-config MYSQL_CONFIG`**

MySQL specific: MySQL config file path.
(default: `\etc\mysql\my.cnf`)

**`-D`\
`--dry-run`**

Do not perform an actual backup, only show dump commands.
__Be aware that the database will be queried for tables selection and temporary folders and files are created.__ (default: `False`)

### Connection options

**`-H HOST`\
`--host HOST`**

Hostname/IP of database server DBMS, to specify a blank value pass `-`.
For postgresql special rules might apply (see
[psql cli --host](https://www.postgresql.org/docs/current/app-psql.html) and
[pg_dump cli --host](https://www.postgresql.org/docs/current/app-pgdump.html).
(default: `127.0.0.1`)

**`-P PORT`\
` --port PORT`**

DBMS port. (default: mysql=`3306` or psql=`5432`)
  
**`-S SOCK`\
`--socket SOCK`**

Path to DBMS socket file. Alternative to specifying host. (default: `None`)

**`-u USER`\
`--username USER`**

Database login user. (default: `zabbix`)

**`-p PASSWD`\
`--passwd PASSWD`**

Database login password (specify `-` for an interactive prompt). (default: `-`)

**`-d DBNAME`\
`--database DBNAME`**

Database name. (default: `zabbix`)

**`-s SCHEMA`\
`--schema SCHEMA`**

PostgreSQL specific: database schema. (default: `public`)

**`-n`\
` --reverse-lookup`**

Perform a reverse lookup of IP address for the host. (default: `True`)

### Dump options

**`-U {dump,schema,ignore,fail}`\
`--unknown-action {dump,nodata,ignore,fail}`**

Unknown tables action to perform.
Either full dump, only schema definition (nodata), ignore completely or
fail and stop the backup. (default: `ignore`)

**`-M {dump,nodata}`\
`--monitoring-action {dump,nodata}`**

Monitoring tables action.
Either full dump or only schema definition (nodata). (default: `nodata`)

**`-N`\
`--add-columns`**

Add column names in INSERT clauses and quote them as needed. (default: `False`)

### Configuration files
**`--save-files`**

Save folders and other files (see `--files`). (default: `True`)

**`--files FILES`**

Save folders and other files listed in `FILES`. One line item to copy,
non existant will be ignored. Directory structure is replicated 
and everything is copied with `cp -r`.
If `-` is passed then standard directories are copied (/etc/zabbix, /usr/lib/zabbix).   
(default: `-`)

### Output options

**`-x {gzip,xz,none}`\
`--compression {gzip,xz,none}`**

Set compression algorithm. xz will take longer and consume more CPU time but the       
backup will be smaller of the same dump compressed using gzip. (default: `gzip`)

**`-f FORMAT`\
`--format FORMAT`**

PostgreSQL specific: custom dump format
(see [pg_dump cli --format](https://www.postgresql.org/docs/current/app-pgdump.html)).
(default: `custom`)

**`-r ROTATE`\
`--rotate ROTATE`**

Rotate backups while keeping up to `ROTATE` old backups.
Uses filename to match '0=keep everything'. (default: `0`)

**`-o OUTDIR`\
`--outdir OUTDIR`**

Save database dump to `OUTDIR`. (default: `.`)

### Verbosity

**`-q`\
`--quiet`**

Don't print anything except unrecoverable errors. (default: `False`)

**`-v`\
`--verbose`**

Print informations (default: `True`)

**`-V`\
`--very-verbose`**

Print even more informations (default: `False`)

**`--debug`**

Print everything (default: `False`)
