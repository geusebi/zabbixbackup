# Zabbix backup python script

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

## Postgres SQL: second level CLI

`zabbixbackup psql --help`
```
usage: zabbixbackup psql [-h] [-z] [-Z ZBX_CONFIG] [-D] [-H HOST] [-P PORT]
                         [-u USER] [-p PASSWD] [--keep-login-file]
                         [--login-file LOGINFILE] [-d DBNAME] [-s SCHEMA] [-n]
                         [--name NAME] [-U {dump,nodata,ignore,fail}]
                         [-M {dump,nodata}] [-N] [-x PGCOMPRESSION]
                         [-f {custom,plain,directory,tar}] [--save-files]
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
  -f {custom,plain,directory,tar}, --pgformat {custom,plain,directory,tar}
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

