# zabbixbackup

zabbix dump for mysql and psql inspired and directly translated from @nopotorino et al

## Install
```
pip install zabbixbackup
```

## Usage

```
usage: zabbixdump [-h] [-t {mysql,psql}] [-z] [-Z ZBX_CONFIG] [-c] [-C MYSQL_CONFIG] [-D] [-H HOST] [-P PORT]
                  [-S SOCK] [-u USER] [-p PASSWD] [-d DBNAME] [-s SCHEMA] [-n] [-U {dump,schema,ignore,fail}]
                  [-N] [-x {gzip,xz,none}] [-f FORMAT] [-r ROTATE] [-o OUTDIR] [-q | -v | -V | --debug]
```

### General options
`-t {mysql,psql}, --type {mysql,psql}`

Database connection or autofetch via zabbix configuration file. (default: `psql`)

`-z, --read-zabbix-config`

Try to read database host and credentials from Zabbix config. (default: `False`)

`-Z ZBX_CONFIG, --zabbix-config ZBX_CONFIG`

Zabbix config file path. (default: `/etc/zabbix/zabbix_server.conf`)

`-c, --read-mysql-config`

MySQL specific: Read database host and credentials from MySQL config file. (default: `False`)

`-C MYSQL_CONFIG, --mysql-config MYSQL_CONFIG`

MySQL specific: MySQL config file path. (default: `\etc\mysql\my.cnf`)

`-D, --dry-run`

Do not create the actual backup, only show dump commands. Be aware that the database will be queried
for tables selection. (default: False)

### Connection options

`-H HOST, --host HOST`

Hostname/IP of database server DBMS, to specify a blank value pass '-'. (default: `127.0.0.1`)

`-P PORT, --port PORT`

DBMS port. (default: mysql=`3306` or psql=`5432`)
  
`-S SOCK, --socket SOCK`

Path to DBMS socket file. Alternative to specifying host. (default: `None`)
  
`-u USER, --username USER`

Database login user. (default: `zabbix`)

`-p PASSWD, --passwd PASSWD`

Database login password (specify '-' for a prompt). (default: `-`)
  
`-d DBNAME, --database DBNAME`

Database name. (default: `zabbix`)

`-s SCHEMA, --schema SCHEMA`

PostgreSQL specific: database schema. (default: `public`)

`-n, --reverse-lookup`

Perform a reverse lookup of IP address for the host. (default: True)

### Dump options

`-U {dump,schema,ignore,fail}, --unknown-action {dump,schema,ignore,fail}`

Ingore unknown tables (don't include them into the backup) (default: `ignore`)

`-N, --add-columns`

Add column names in INSERT clauses and quote them as needed. (default: `False`)

### Output options

`-x {gzip,xz,none}, --compression {gzip,xz,none}`

Set compression algorithm. xz will take longer and consume more CPU time but the       
backup will be smaller of the same dump compressed using gzip. (default: `gzip`)
  
`-f FORMAT, --format FORMAT`

PostgreSQL specific: custom dump format (default: `custom`)

`-r ROTATE, --rotate ROTATE`

Rotate backups while keeping up to 'R' old backups. Uses filename to match '0=keep everything'. (default: `0`)

`-o OUTDIR, --outdir OUTDIR`

Save database dump to 'outdir'. (default: .)

### Verbosity

`-q, --quiet`

Don't print anything except unrecoverable errors. (default: `False`)

`-v, --verbose`

Print informations (default: `True`)

`-V, --very-verbose`

Print even more informations (default: `False`)

`--debug`               

Print everything (default: `False`)
