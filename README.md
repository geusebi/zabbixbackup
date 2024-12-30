# Zabbix backup python script

[![Tox unittest](https://github.com/geusebi/zabbixbackup/actions/workflows/tox-unittest.yml/badge.svg?event=push
)](https://github.com/geusebi/zabbixbackup/actions/workflows/tox-unittest.yml/badge.svg?event=push)
[![Pylint](https://github.com/geusebi/zabbixbackup/actions/workflows/pylint.yml/badge.svg?event=push)](https://github.com/geusebi/zabbixbackup/actions/workflows/pylint.yml?event=push)

*EXPERIMENTAL: use at your own risk!*

Python script to perform zabbix dumps.

See full project documentation at https://www.zabbixbackup.com.

Inspired by the project https://github.com/npotorino/zabbix-backup.

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

## Options

**Database engine**
- [`<DBMS> (psql|mysql)`](#dbms)

**Main**
- [`--read-zabbix-config`](#readzabbixconfig)
- [`--zabbix-config ZABBIX_CONFIG`](#zabbixconfig)
- [`--read-mysql-config`](#readmysqlconfig) (MySQL specific)
- [`--mysql-config MYSQL_CONFIG`](#mysqlconfig) (MySQL specific)
- [`--dry-run`](#dryrun)

**Connection**
- [`--host HOST`](#host) (special for Postgres)
- [`--port PORT`](#port)
- [`--sock SOCK`](#sock) (MySQL specific)
- [`--username USER`](#username)
- [`--passwd PASSWD`](#passwd)
- [`--keep-login-file`](#keeploginfile)
- [`--login-file LOGINFILE`](#loginfile)

- [`--database DBNAME`](#dbname)
- [`--schema SCHEMA`](#schema) (Postgres specific)
- [`--reverse-lookup`](#reverselookup) (**Not implemented**)
- [`--name`](#name)

**Dump action**
- [`--unknown-action UNKNOWN`](#unknownaction)
- [`--monitoring-action MONITORING`](#monitoringaction)
- [`--add-columns`](#addcolumns)

**Dump compression**
- [`--pgformat PGFORMAT`](#pgformat) (Postgres specific)
- [`--pgcompression PGCOMPRESSION`](#pgcompression) (Postgres specific)
- [`--mysqlcompression MYSQLCOMPRESSION`](#mysqlcompression) (MySQL specific)

**Configuration files**
- [`--save-files`](#savefiles)
- [`--files FILES`](#files)

**Output**
- [`--archive ARCHIVE`](#archive)
- [`--outdir OUTDIR`](#outdir)
- [`--rotate ROTATE`](#rotate)

**Verbosity**
- [`--quiet`](#verbosity)
- [`--verbose`](#verbosity)
- [`--very-verbose`](#verbosity)
- [`--debug`](#verbosity)


<a name="dbms"></a>
### Database engine
**```<DBMS> (psql|mysql)```**

_Default: no default (mandatory)_

Database engine to use. Either postgresql or mysql (mariasql compatible).

<a name="readzabbixconfig"></a>
### Read zabbix configuration
**```--read-zabbix-config, -z```**

_Default: `False`_

Try to read database host and credentials from Zabbix config.
The file is read and parsed trying to collect as much as possible.
Every variable collected will be used if not already provided by user arguments.

Implicit if `--zabbix-config` is set.

<a name="zabbixconfig"></a>
### Zabbix configuration file
**```--zabbix-config ZBX_CONFIG, -Z ZBX_CONFIG```**

_Default: `/etc/zabbix/zabbix_server.conf`_

Zabbix configuration file path.

<a name="readmysqlconfig"></a>
### Read MySQL configuration (MySQL specific)
**```--read-mysql-config, -c```**

_Default: `False`_

Read database host and credentials from MySQL config file.
Implicit if `--mysql-config` is set.

<a name="mysqlconfig"></a>
### MySQL configuration file (MySQL specific)
**```--mysql-config MYSQL_CONFIG, -C MYSQL_CONFIG```**

_Default: `/etc/mysql/my.cnf`_

MySQL configuration file path.
Implicit if `--read-mysql-config` is set.

<a name="dryrun"></a>
### Dry run
**```--dry-run, -D```**

_Default: `False`_

Do not create the actual backup, only show dump commands.
**Be aware that the database will be queried** for tables selection and
**folders and files will be created**. This is meant only for setup, inspection
and debugging.

<a name="host"></a>
### Hostname (special for Postgres)
**```--host, -H```**

_Default: `127.0.0.1`_

Hostname/IP of DBMS server, to specify a blank value pass `-`.

For postgresql special rules might apply (see Postgres `psql` and `pg_dump`
online documentation for sockets).

<a name="port"></a>
### Port
**```--port PORT, -P PORT```**

_Default: `5432` for Postgres, `3306` for MySQL)_

Database connection port.

<a name="sock"></a>
### Socket (Mysql specific)
**```--socket SOCK, -S SOCK```**

_Default: `None`_

Path to MySQL socket file. Alternative to specifying host.

<a name="username"></a>
### Username
**```--user USER, -u USER```**

_Default: `zabbix`_

Username to use for the database connection.

<a name="passwd"></a>
### Password
**```--passwd PASSWD, -p PASSWD```**

_Default: `None`_

Database login password. Specify `-` for an interactive prompt.
For Postgres, a `.pgpass` will be created to connect to the database and then
deleted (might be saved with the backup).

<a name="keeploginfile"></a>
### Keep login file
**```--keep-login-file```**

_Default: `False`_

Do not delete login file (either `.pgpass` or `mylogin.cnf`) on program exit.

Useful to create the login file and avoid clear password or interactive prompt.

For postgres, the saved file is not hidden (`pgpass`).

<a name="loginfile"></a>
### Login file
**```--login-file LOGINFILE```**

_Default: `None`_

Use this file (either `.pgpass` or `mylogin.cnf`) for the authentication.

<a name="dbname"></a>
### Database name
**```--database DBNAME, -d DBNAME```**

_Default: `zabbix`_

The name of the database to connect to.

<a name="schema"></a>
### Database schema (Postgres specific)
**```--schema SCHEMA, -s SCHEMA```**

_Default: `public`_

The name of the schema to use.

<a name="reverselookup"></a>
### Reverse lookup
**```--reverse-lookup, -n```**

_Default: `True`_

(NOT IMPLEMENTED) Perform a reverse lookup of the IP address for the host.

<a name="name"></a>
### Name
**```--name```**

_Default: `None`_

Use this name instead of `host` while creating the name of the archive.

The name must be alphanumeric, only `-` and `.` special characters are allowed).

_Using this option automatically disable `--reverse-lookup`!_

<a name="unknownaction"></a>
### Unknown tables action
**```--unknown-action {dump,nodata,ignore,fail}, -U {dump,nodata,ignore,fail}```**

_Default: `ignore`_

Action for unknown tables.

Choose `dump` to dump the tables fully with definitions. `nodata` will include only
the definitions. `ignore` will skip the unknown tables. `fail` will abort the
backup in case of an unknown table.

<a name="monitoringaction"></a>
### Monitoring tables action
**```--monitoring-action {dump,nodata}, -U {dump,nodata}```**

_Default: `nodata`_

Action for monitoring table.

Choose `dump` do dump the tables fully with definitions. `nodata` will include only
the definitions.

<a name="addcolumns"></a>
### Add columns
**```--add-columns, -N```**

_Default: `False`_

Add column names in INSERT clauses and quote them as needed.

<a name="pgformat"></a>
### Postgres dump format
**```--pgformat PGFORMAT```**

_Default: `custom`_

Dump format, will mandate the file output format.

Available formats: plain, custom, directory, or tar (see postgres documentation).

<a name="pgcompression"></a>
### Postgres dump compression
**```--pgcompression PGCOMPRESSION```**

_Default: `None`_

Passed as-is to `pg_dump` `--compress`, might be implied by format (see postgres documentation).

Be aware that the postgres `tar` format won't be compressed. In that case you could use `--archive`.

<a name="mysqlcompression"></a>
### Dump compression
**```--mysqlcompression MYSQLCOMPRESSION```**

_Default: `-`_

Mysql dump compression.

`-` to leave the dump uncompressed as is.

Available compression formats are `xz`, `gzip` and `bzip2`.
Use `:<LEVEL>` to set a compression.

The compression binary must be available in current shell.
`xz`, `gzip`, and `bzip2` will take precedence and `7z` is used as fallback (might be useful on Windows platforms).

**NOTE: on windows platforms this result is a compressed file with CRLF line termination instead of LF.**

<a name="savefiles"></a>
### Save configuration files
**```--save-files```**

_Default: `False`_

Save folders and other files in the backup (see --files).

<a name="files"></a>
### File index to save with the backup
**```--files FILES```**

_Default: `-`_

Save folders and other files as listed in this index file.
Non existant will be ignored. Directory structure is replicated (copied via
`cp`).

File format: one line per folder or file.

If `FILES` is `-` then the standard files are selected, i.e:
`/etc/zabbix/` and `/usr/lib/zabbix/`.

<a name="archive"></a>
### Backup archive format
**```--archive ARCHIVE, -a ARCHIVE```**

_Default: `-`_

Use `tar` to create a tar archive.

`-` to leave the backup uncompressed as a folder.

Available compression formats are `xz`, `gzip` and `bzip2`.
Use `:<LEVEL>` to set a compression level. I.e. `--archive xz:6`.

<a name="outdir"></a>
### Output directory
**```--outdir OUTDIR, -o OUTDIR```**

_Default: `.`_

The destination directory to save the backup to.

<a name="rotate"></a>
### Backup rotation
**```--rotate ROTATE, -r ROTATE```**

_Default: `0`_

Rotate backups while keeping up `R` old backups. Uses filenames to find old backups.\
`0 = keep everything`.

<a name="verbosity"></a>
### Verbosity

**```--quiet, -q```**

**```--verbose, -v```** 

**```--very-verbose, -V```** 

**```--debug```** 

_Default: `verbose`_

Don't print anything except unrecoverable errors (quiet),\
print informations only (verbose),\
print even more informations (very verbose),\
print everything (debug).

## Postgres SQL: second level CLI

`zabbixbackup psql --help`
```
usage: zabbixbackup psql [-h] [-z] [-Z ZBX_CONFIG] [-D] [-H HOST] [-P PORT]
                         [-u USER] [-p PASSWD] [--keep-login-file]
                         [--login-file LOGINFILE] [-d DBNAME] [-s SCHEMA] [-n]
                         [--name NAME] [-U {dump,nodata,ignore,fail}]
                         [-M {dump,nodata}] [-N] [-x PGCOMPRESSION]
                         [-f {plain,custom,directory,tar}] [--save-files]
                         [--files FILES] [-a ARCHIVE] [-o OUTDIR] [-r ROTATE]
                         [-q | -v | -V | --debug]

zabbix dump for psql inspired and directly translated from...

options:
  -h, --help            show this help message and exit
  -z, --read-zabbix-config
                        try to read database host and credentials from Zabbix
                        config. Implicit if `--zabbix-config` is set.
                        (default: False)
  -Z ZBX_CONFIG, --zabbix-config ZBX_CONFIG
                        Zabbix config file path. Implicit if `--read-zabbix-
                        config` is set. (default:
                        /etc/zabbix/zabbix_server.conf)
  -D, --dry-run         Do not create the actual backup, only show dump
                        commands. Be aware that the database will be queried
                        for tables selection and temporary folders and files
                        will be created. (default: False)

connection options:
  -H HOST, --host HOST  hostname/IP of DBMS server, to specify a blank value
                        pass '-'. If host starts with a slash it's interpreted
                        as a socket directory. Special rules might apply (see
                        postgre online documentation for sockets). (default:
                        127.0.0.1)
  -P PORT, --port PORT  DBMS port. (default: 5432)
  -u USER, --username USER
                        database login user. (default: zabbix)
  -p PASSWD, --passwd PASSWD
                        database login password (specify '-' for an
                        interactive prompt). (default: None)
  --keep-login-file     if a credential file is created (.pgpass) do not
                        delete it on exit. (default: False)
  --login-file LOGINFILE
                        use '.pgpass' file for the authentication. (default:
                        None)
  -d DBNAME, --database DBNAME
                        database name. (default: zabbix)
  -s SCHEMA, --schema SCHEMA
                        database schema. (default: public)
  -n, --reverse-lookup  (NOT IMPLEMENTED) perform a reverse lookup of the IP
                        address for the host. (default: True)
  --name NAME           use this name instead of 'host' for the backup name.
                        (allowed alphanum, -, .) (default: None)

dump action options:
  -U {dump,nodata,ignore,fail}, --unknown-action {dump,nodata,ignore,fail}
                        action for unknown tables. (default: ignore)
  -M {dump,nodata}, --monitoring-action {dump,nodata}
                        action for monitoring table (default: nodata)
  -N, --add-columns     add column names in INSERT clauses and quote them as
                        needed. (default: False)

dump level compression options:
  -x PGCOMPRESSION, --pgcompression PGCOMPRESSION
                        passed as-is to pg_dump --compress, might be implied
                        by format. (default: None)
  -f {plain,custom,directory,tar}, --pgformat {plain,custom,directory,tar}
                        dump format, will mandate the file output format.
                        (default: custom)

configuration files:
  --save-files          save folders and other files (see --files). (default:
                        False)
  --files FILES         save folders and other files as listed in this file.
                        One line per folder or file, non existant will be
                        ignored. Directory structure is replicated (copied via
                        'cp'). (default: -)

output options:
  -a ARCHIVE, --archive ARCHIVE
                        archive level compression. 'tar' to create a tar
                        archive, '-' to leave the backup uncompressed as a
                        folder. Other available formats are xz, gzip and
                        bzip2. Use ':<LEVEL>' to set a compression level. I.e.
                        --archive xz:6 (default: -)
  -o OUTDIR, --outdir OUTDIR
                        save database dump to 'outdir'. (default: .)
  -r ROTATE, --rotate ROTATE
                        rotate backups while keeping up 'R' old backups.Uses
                        filename to match '0=keep everything'. (default: 0)

verbosity:
  -q, --quiet           don't print anything except unrecoverable errors.
                        (default: False)
  -v, --verbose         print informations. (default: True)
  -V, --very-verbose    print even more informations. (default: False)
  --debug               print everything. (default: False)
```

## MySQL: second level CLI

`zabbixbackup mysql --help`
```
usage: zabbixbackup mysql [-h] [-z] [-Z ZBX_CONFIG] [-c] [-C MYSQL_CONFIG]
                          [-D] [-H HOST] [-P PORT] [-S SOCK] [-u USER]
                          [-p PASSWD] [--keep-login-file]
                          [--login-file LOGINFILE] [-d DBNAME] [-n]
                          [--name NAME] [-U {dump,nodata,ignore,fail}]
                          [-M {dump,nodata}] [-N]
                          [--mysqlcompression MYSQLCOMPRESSION] [--save-files]
                          [--files FILES] [-a ARCHIVE] [-o OUTDIR] [-r ROTATE]
                          [-q | -v | -V | --debug]

zabbix dump for mysql inspired and directly translated from...

options:
  -h, --help            show this help message and exit
  -z, --read-zabbix-config
                        try to read database host and credentials from Zabbix
                        config. Implicit if `--zabbix-config` is set.
                        (default: False)
  -Z ZBX_CONFIG, --zabbix-config ZBX_CONFIG
                        Zabbix config file path. Implicit if `--read-zabbix-
                        config` is set. (default:
                        /etc/zabbix/zabbix_server.conf)
  -c, --read-mysql-config
                        Read database host and credentials from MySQL config
                        file. Implicit if `--mysql-config` is set. (default:
                        False)
  -C MYSQL_CONFIG, --mysql-config MYSQL_CONFIG
                        MySQL config file path. Implicit if `--read-mysql-
                        config` is set. (default: /etc/mysql/my.cnf)
  -D, --dry-run         Do not create the actual backup, only show dump
                        commands. Be aware that the database will be queried
                        for tables selection and temporary folders and files
                        will be created. (default: False)

connection options:
  -H HOST, --host HOST  hostname/IP of DBMS server, to specify a blank value
                        pass '-'. (default: 127.0.0.1)
  -P PORT, --port PORT  DBMS port. (default: 3306)
  -S SOCK, --socket SOCK
                        path to DBMS socket file. Alternative to specifying
                        host. (default: None)
  -u USER, --username USER
                        database login user. (default: zabbix)
  -p PASSWD, --passwd PASSWD
                        database login password (specify '-' for an
                        interactive prompt). (default: None)
  --keep-login-file     if a credential file is created (mylogin.cnf) do not
                        delete it on exit. (default: False)
  --login-file LOGINFILE
                        use 'mylogin.cnf' file for the authentication.
                        (default: None)
  -d DBNAME, --database DBNAME
                        database name. (default: zabbix)
  -n, --reverse-lookup  (NOT IMPLEMENTED) perform a reverse lookup of the IP
                        address for the host. (default: True)
  --name NAME           use this name instead of 'host' for the backup name.
                        (allowed alphanum, -, .) (default: None)

dump action options:
  -U {dump,nodata,ignore,fail}, --unknown-action {dump,nodata,ignore,fail}
                        action for unknown tables. (default: ignore)
  -M {dump,nodata}, --monitoring-action {dump,nodata}
                        action for monitoring table (default: nodata)
  -N, --add-columns     add column names in INSERT clauses and quote them as
                        needed. (default: False)

dump level compression options:
  --mysqlcompression MYSQLCOMPRESSION
                        dump level compression. Available formats are xz, gzip
                        and bzip2. Use ':<LEVEL>' to set a compression level.
                        I.e. --archive xz:6. See documentation for the
                        details. (default: gzip:6)

configuration files:
  --save-files          save folders and other files (see --files). (default:
                        False)
  --files FILES         save folders and other files as listed in this file.
                        One line per folder or file, non existant will be
                        ignored. Directory structure is replicated (copied via
                        'cp'). (default: -)

output options:
  -a ARCHIVE, --archive ARCHIVE
                        archive level compression. 'tar' to create a tar
                        archive, '-' to leave the backup uncompressed as a
                        folder. Other available formats are xz, gzip and
                        bzip2. Use ':<LEVEL>' to set a compression level. I.e.
                        --archive xz:6 (default: -)
  -o OUTDIR, --outdir OUTDIR
                        save database dump to 'outdir'. (default: .)
  -r ROTATE, --rotate ROTATE
                        rotate backups while keeping up 'R' old backups.Uses
                        filename to match '0=keep everything'. (default: 0)

verbosity:
  -q, --quiet           don't print anything except unrecoverable errors.
                        (default: False)
  -v, --verbose         print informations. (default: True)
  -V, --very-verbose    print even more informations. (default: False)
  --debug               print everything. (default: False)
```

