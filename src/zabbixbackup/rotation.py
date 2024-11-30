from shutil import rmtree
import re
import logging
from .parser_defaults import PSqlArgs, MySqlArgs


re_cfg = re.compile(r"""
    zabbix_                           # suffix
    (?P<host>[^_]+?)_                 # host name
    (?P<year>[0-9]{4})                # yearmonthday-hourminute
    (?P<month>[0-9]{2})               #
    (?P<day>[0-9]{2})-                #
    (?P<hour>[0-9]{2})                #
    (?P<minute>[0-9]{2})_             #
    (?P<second>[0-9]{2})_             #
    #(?P<version>([0-9][.])+?[0-9]+?)  # zabbix version and eol
    (?P<ext>([.]tar[.](gz|xz|bz2)))?  # extension (empty if plain folder)
""", re.VERBOSE)


def rotate(args: PSqlArgs|MySqlArgs):
    """
    Perform an archive rotation keeping the last 'args.n' archives.
    """
    n = args.rotate
    
    if n <= 0:
        return
    
    outdir, host = args.outdir, args.host

    folders = [
        item
        for item in outdir.iterdir()
    ]

    # create a list of tuples in the form of [(datetime as int, folder)]
    # in order to being able to sort it naturally
    backups = []
    for folder in folders:
        if match := re_cfg.fullmatch(folder.name):
            d = match.groupdict()
            if d["host"] == host:
                int_dt = int(
                    f"{d['year']}{d['month']}{d['day']}"
                    f"{d['hour']}{d['minute']}{d['second']}"
                )
                backups.append((int_dt, folder))

    backups = sorted(backups)
    remove, keep = backups[:-n], backups[-n:]

    logging.info("Rotate backups")
    logging.info(f"Found {len(backups)} backup/s")
    logging.info(f"Deleting {len(remove)} and keeping {len(keep)} backup/s")

    for _, item in remove:
        logging.verbose(f"    deleting backup '{item}'")
        if not args.dry_run:
            if item.is_file():
                item.unlink()
            else:
                rmtree(item)

    for _, item in keep:
        logging.debug(f"    keeping backup '{item}'")
