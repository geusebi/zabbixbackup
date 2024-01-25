

if __name__ == "__main__":
    from sys import argv, stderr
    from pprint import pprint
    from .parser import parse
    from .backup import backup_postgresql, backup_mysql
    
    args = parse(argv[1:])

    dict_args = vars(args)
    keys = (
        "type", "read_zabbix_config", "zabbix_config", "read_mysql_config", "mysql_config",
        "dry_run", "host", "port", "sock", "user", "passwd", "dbname", "schema",
        "rlookup", "unknown", "columns", "compression", "format", "rotate", "outdir", "verbosity"
    )

    print("Arguments:", file=stderr)
    for key in keys:
        value = getattr(args, key, None)
        if value is None:
            continue
        if key == "passwd":
            print(f"    {key:<24}: [omissis]", file=stderr)
        else:
            print(f"    {key:<24}: {value}", file=stderr)

    for key, value in dict_args.items():
        if key in keys:
            continue
        print(f"    {key:<24}: {value}", file=stderr)

    if args.type == "psql":
        backup_postgresql(args)
    elif args.type == "mysql":
        backup_mysql(args)

    if args.rotate > 0:
        pass
