
if __name__ == "__main__":
    from sys import argv
    from pprint import pprint
    from .parser import parse
    from .backup import backup_postgresql, backup_mysql

    args = parse(argv[1:])

    if args.type == "psql":
        backup_postgresql(args)
    elif args.type == "mysql":
        backup_mysql(args)

    if args.rotate > 0:
        pass

    pprint(args)