from pathlib import Path
from shutil import rmtree
import re
import logging


re_cfg = re.compile(r"""
    zabbix_cfg_            # suffix
    (?P<host>[^_]+?)_      # host name
    (?P<year>[0-9]{4})     # yearmonthday-hourminute
    (?P<month>[0-9]{2})    #
    (?P<day>[0-9]{2})-     #
    (?P<hour>[0-9]{2})     #
    (?P<minute>[0-9]{2})_  #
    (?P<version>[.0-9]+?)  # zabbix version and eol
""", re.VERBOSE)


def rotate(args, data):
    n = args.rotate
    outdir, host, version = Path(args.outdir), args.host, data.version

    folders = [
        item
        for item in outdir.iterdir()
        if item.is_dir()
    ]

    # create a list of tuples in the form of [(datetime as int, folder)]
    # in order to being able to sort it naturally
    backups = []
    for folder in folders:
        if match := re_cfg.fullmatch(folder.name):
            d = match.groupdict()
            if d["host"] == host and d["version"] == version:
                int_dt = int(
                    f"{d['year']}{d['month']}{d['day']}"
                    f"{d['hour']}{d['minute']}"
                )
                backups.append((int_dt, folder))

    backups = sorted(backups)
    remove, keep = backups[:-n], backups[-n:]

    logging.info("Rotate backups")
    logging.info(f"Found {len(backups)} backup/s")
    logging.info(f"Deleting {len(remove)} and keeping {len(keep)} backup/s")

    for item in remove:
        logging.verbose(f"    deleting backup '{item[1]}'")
        rmtree(item[1])

    for item in keep:
        logging.debug(f"    keeping backup '{item[1]}'")
