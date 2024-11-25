# Zabbix backup python script

*EXPERIMENTAL: DO NOT USE IN PRODUCTION*

## Install
```
pip install zabbixbackup
```

## Examples
Create a backup connecting as user `postgres` to the db `zabbix` with schema `zabbix`

`python -m zabbixbackup psql --host 127.0.0.1 --user postgres --passwd mypassword --database zabbix --schema zabbix`

Create a tar archive dump and save standard zabbix configuration files along with it.

`python -m zabbixbackup psql --host 127.0.0.1 --passwd mypassword --format tar --save-files`

Create a "custom" archive and save it to a backup folder, rotate backups to retain
only the last four.

`python -m zabbixbackup psql --host 127.0.0.1 --passwd mypassword --format custom --rotate 4`

Setup an authentication (`.pgpass`) file and use it to login in subsequent call.
```
python -m zabbixbackup pgsql --host 127.0.0.1 \
          --passwd - --keep-login-file --dry-run
[input password]
mv .pgpass /root

python -m zabbixbackup pgsql --host 127.0.0.1 --login-file /root/.pgpass
```

Setup an authentication (`mylogin.cnf`) file and use it to login in subsequent call.
```
python -m zabbixbackup mysql --host 127.0.0.1 \
          --passwd - --keep-login-file --dry-run
[input password]
mv mylogin.cnf /root

python -m zabbixbackup mysql --host 127.0.0.1 --login-file /root/mylogin.cnf
```

## First level CLI
```
usage: zabbixbackup [-h] {psql,pgsql,mysql} ...

options:
  -h, --help          show this help message and exit

DBMS:
  {psql,pgsql,mysql}
    psql (pgsql)      (see zabbixbackup psql --help)
    mysql             (see zabbixbackup mysql --help)
```

## Options documentation and examples

- [DBMS](#dbms)

**Main**
- [--read-zabbix-config](#read-zabbix-config)
- [--zabbix-config ZABBIX_CONFIG](#zabbix-config)
- [--read-mysql-config](#read-mysql-config) (MySQL specific)
- [--mysql-config MYSQL_CONFIG](#mysql-config) (MySQL specific)
- [--dry-run](#dry-run)

**Connection**
- [--host HOST](#host) (special for Postgres)
- [--port PORT](#port)
- [--sock SOCK](#sock) (MySQL specific)
- [--username USER](#user)
- [--passwd PASSWD](#passwd)
- [--keep-login-file](#keeploginfile)
- [--loginfile LOGINFILE](#loginfile)

- [--database DBNAME](#dbname)
- [--schema SCHEMA](#schema) (Postgres specific)
- [--reverse-lookup](#reverse-lookup) (NOT IMPLEMENTED)

**Dump**
- [--unknown-action UNKNOWN](#unknown-action)
- [--monitoring-action MONITORING](#monitoring-action)
- [--add-columns](#add-columns)

**Configuration files**
- [--save-files](#save-files)
- [--files FILES](#files)

**Output**
- [--compression](#compression) (Postgres specific)
- [--format](#format) (Postgres specific)
- [--archive](#archive)
- [--outdir](#outdir)
- [--rotate](#rotate)


**Verbosity**
- [--quiet](#verbosity)
- [--verbose](#verbosity)
- [--very-verbose](#verbosity)
- [--debug](#verbosity)

<a name="dbms"></a>
### Database engine
**```<DBMS>```**

Database engine to use. Either postgresql or mysql (mariasql compatible).

<a name="read-zabbix-config"></a>
### Read zabbix configuration
**```--read-zabbix-config, -z```**

_Default: False_

Try to read database host and credentials from Zabbix config.
The file is read and parsed trying to collect as much as possible.
Every variable collected will be used if not already provided by user arguments.

Implicit if `--zabbix-config` is set.

<a name="zabbix-config"></a>
### Zabbix configuration file
**```--zabbix-config ZBX_CONFIG, -Z ZBX_CONFIG```**

_Default: /etc/zabbix/zabbix_server.conf_

Zabbix configuration file path.

<a name="read-mysql-config"></a>
### Read MySQL configuration (MySQL specific)
**```--read-mysql-config, -c```**

_Default: False_

Read database host and credentials from MySQL config file.
Implicit if `--mysql-config` is set.

<a name="mysql-config"></a>
### MySQL configuration file (MySQL specific)
**```--mysql-config MYSQL_CONFIG, -C MYSQL_CONFIG```**

_Default: /etc/mysql/my.cnf_

MySQL configuration file path.
Implicit if `--read-mysql-config` is set.

<a name="dry-run"></a>
### Dry run
**```--dry-run, -D```**

_Default: False_

Do not create the actual backup, only show dump commands.
**Be aware that the database will be queried** for tables selection **and
temporary folders and files will be created**. This is meant only for inspection
and debugging.

<a name="host"></a>
### Hostname (special for Postgres)
**```--host, -H```**

_Default: 127.0.0.1_

Hostname/IP of DBMS server, to specify a blank value pass '-'.

For postgresql special rules might apply (see Postgres `psql` and `pg_dump`
online documentation for sockets).

<a name="port"></a>
### Port
**```--port PORT, -P PORT```**

_Default: 5432 for Postgres, 3306 for MySQL)_

Database connection port.

<a name="sock"></a>
### Socket (Mysql specific)
**```--socket SOCK, -S SOCK```**

_Default: None_

Path to MySQL socket file. Alternative to specifying host.

<a name="username"></a>
### Username
**```--user USER, -u USER```**

_Default: zabbix_

Username to use for the database connection.

<a name="passwd"></a>
### Password
**```--passwd PASSWD, -p PASSWD```**

_default: None_

Database login password. Specify '-' for an interactive prompt.
For Postgres, a `.pgpass` will be created to connect to the database and then
deleted (might be saved with the backup).

<a name="keeploginfile"></a>
### Keep login file
**```--keep-login-file```**

_default: False_

Do not delete login file (either .pgpass or mylogin.cnf) on program exit.

Useful to create the login file and avoid clear password or interactive prompt.

<a name="loginfile"></a>
### Login file
**```--login-file LOGINFILE```**

_default: None_

Use this file (either .pgpass or mylogin.cnf) for the authentication.


<a name="dbname"></a>
### Database name
**```--database DBNAME, -d DBNAME```**

_Default: zabbix_

The name of the database to connect to.

<a name="schema"></a>
### Database schema (Postgres specific)
**```--schema SCHEMA, -s SCHEMA```**

_Default: public_

The name of the schema to use.

<a name="reverse-lookup"></a>
### Reverse lookup
**```--reverse-lookup, -n```**

_Default: True_

(NOT IMPLEMENTED) Perform a reverse lookup of the IP address for the host.

<a name="unknown-action"></a>
### Unknown tables action
**```--unknown-action {dump,nodata,ignore,fail}, -U {dump,nodata,ignore,fail}```**

_Default: ignore_

Action for unknown tables.

Choose `dump` do dump the tables fully with definitions. `nodata` will include only
the definitions. `ignore` will skip the unknown tables. `fail` will abort the
backup in case of an unknown table.

<a name="monitoring-action"></a>
### Monitoring tables action
**```--monitoring-action {dump,nodata}, -U {dump,nodata}```**

_Default: nodata_

Action for monitoring table.

Choose `dump` do dump the tables fully with definitions. `nodata` will include only
the definitions.

<a name="add-columns"></a>
### Add columns
**```--add-columns, -N```**

_Default: False_

Add column names in INSERT clauses and quote them as needed.

<a name="save-files"></a>
### Save configuration files
**```--save-files```**

_Default: True_

Save folders and other files in the backup (see --files).

<a name="files"></a>
### File index to save with the backup
**```--files FILES```**

_Default: '-'_

Save folders and other files as listed in this index file.
Non existant will be ignored. Directory structure is replicated (copied via
`cp`).

File format: one line per folder or file.

if `FILES` is `-` then the standard files are selected, i.e:

```
/etc/zabbix/
/usr/lib/zabbix/
```

<a name="compression"></a>
### Postgres dump compression
**```--compression COMPRESSION```**

_Default: 'None'_

Passed as-is to pg_dump --compress, might be implied by format.

<a name="format"></a>
### Postgres dump format
**```--format FORMAT```**

_Default: 'custom'_

Dump format, will mandate the file output format.

Available formats: plain, custom, directory, or tar (see postgres documentation).

<a name="archive"></a>
### Backup archive format
**```--archive ARCHIVE, -a ARCHIVE```**

_Default: '-'_

Backup archive format. '-' to leave the backup uncompressed as a folder.

Available formats are `xz`, `gzip` and `bzip2`. Use `:<LEVEL>` to set a compression
level. I.e. `--archive xz:6`.

<a name="outdir"></a>
### Output directory
**```--outdir OUTDIR, -o OUTDIR```**

_Default: '.'_

The destination directory to save the backup to.

<a name="rotate"></a>
### Backup rotation
**```--rotate ROTATE, -r ROTATE```**

_Default: '0'_

Rotate backups while keeping up 'R' old backups. Uses filenames to find old backups.
`0 = keep everything`.

<a name="verbosity"></a>
### Verbosity

**```--quiet, -q```** don't print anything except unrecoverable errors,

**```--verbose, -v```** print informations only,

**```--very-verbose, -V```** print even more informations,

**```--debug```** print everything.

_Default: verbose_

### Postgres SQL: second level CLI

`zabbixbackup psql --help`
```
usage: zabbixbackup psql [-h] [-z] [-Z ZBX_CONFIG] [-D] [-H HOST] [-P PORT]
                         [-u USER] [-p PASSWD] [-d DBNAME] [-s SCHEMA] [-n]
                         [-U {dump,nodata,ignore,fail}] [-M {dump,nodata}]
                         [-N] [--save-files] [--files FILES] [-x COMPRESSION]
                         [-f {plain,custom,directory,tar}] [-r ROTATE]
                         [-o OUTDIR] [-q | -v | -V | --debug]

options:
  -h, --help
  -z, --read-zabbix-config
  -Z ZBX_CONFIG, --zabbix-config ZBX_CONFIG
  -D, --dry-run

connection options:
  -H HOST, --host HOST
  -P PORT, --port PORT
  -u USER, --username USER
  -p PASSWD, --passwd PASSWD
  -d DBNAME, --database DBNAME
  -s SCHEMA, --schema SCHEMA
  -n, --reverse-lookup

dump options:
  -U {dump,nodata,ignore,fail}, --unknown-action {dump,nodata,ignore,fail}
  -M {dump,nodata}, --monitoring-action {dump,nodata}
  -N, --add-columns

configuration files:
  --save-files
  --files FILES

output options:
  -a ARCHIVE, --archive ARCHIVE
  -x COMPRESSION, --compression COMPRESSION
  -f {tar,plain,custom,directory}
  -r ROTATE, --rotate ROTATE
  -o OUTDIR, --outdir OUTDIR

verbosity:
  -q, --quiet
  -v, --verbose
  -V, --very-verbose
  --debug
```

### MySQL: second level CLI

`zabbixbackup mysql --help`
```
usage: zabbixbackup mysql [-h] [-z] [-Z ZBX_CONFIG] [-c] [-C MYSQL_CONFIG]
                          [-D] [-H HOST] [-P PORT] [-S SOCK] [-u USER]
                          [-p PASSWD] [-d DBNAME] [-n]
                          [-U {dump,nodata,ignore,fail}] [-M {dump,nodata}]
                          [-N] [--save-files] [--files FILES] [-r ROTATE]
                          [-o OUTDIR] [-q | -v | -V | --debug]

options:
  -h, --help
  -z, --read-zabbix-config
  -Z ZBX_CONFIG, --zabbix-config ZBX_CONFIG
  -c, --read-mysql-config
  -C MYSQL_CONFIG, --mysql-config MYSQL_CONFIG
  -D, --dry-run

connection options:
  -H HOST, --host HOST
  -P PORT, --port PORT
  -S SOCK, --socket SOCK
  -u USER, --username USER
  -p PASSWD, --passwd PASSWD
  -d DBNAME, --database DBNAME
  -n, --reverse-lookup

dump options:
  -U {dump,nodata,ignore,fail}, --unknown-action {dump,nodata,ignore,fail}
  -M {dump,nodata}, --monitoring-action {dump,nodata}
  -N, --add-columns

configuration files:
  --save-files
  --files FILES

output options:
  -a ARCHIVE, --archive ARCHIVE
  -r ROTATE, --rotate ROTATE
  -o OUTDIR, --outdir OUTDIR

verbosity:
  -q, --quiet
  -v, --verbose
  -V, --very-verbose
  --debug
```