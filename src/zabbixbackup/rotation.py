from pathlib import Path
from shutil import rmtree
import re
import logging
from .parser_defaults import PSqlArgs, MySqlArgs

logger = logging.getLogger(__name__)


re_cfg = re.compile(r"""
    zabbix_                             # suffix
    (?P<host>[^_]+?)_                   # host name
    (?P<year>[0-9]{4})                  # yearmonthday-hourminutesecond
    (?P<month>[0-9]{2})                 #
    (?P<day>[0-9]{2})-                  #
    (?P<hour>[0-9]{2})                  #
    (?P<minute>[0-9]{2})                #
    (?P<second>[0-9]{2})                #
    #(?P<version>([0-9][.])+?[0-9]+?)    # zabbix version and eol
    (?P<ext>([.]tar([.](gz|xz|bz2))?))? # extension (empty if plain folder)
""", re.VERBOSE)


def rotate(args: PSqlArgs|MySqlArgs):
    """
    Perform an archive rotation keeping the last 'args.n' archives.
    """
    n = args.rotate

    if n <= 0:
        return

    host = args.host

    # create a list of tuples in the form of [(datetime as int, folder)]
    # in order to being able to sort it naturally
    backups = []
    for archive in Path(".").iterdir():
        if match := re_cfg.fullmatch(archive.name):
            d = match.groupdict()
            if d["host"] == host:
                int_dt = int(
                    f"{d['year']}{d['month']}{d['day']}"
                    f"{d['hour']}{d['minute']}{d['second']}"
                )
                backups.append((int_dt, archive))

    backups = sorted(backups)
    remove, keep = backups[:-n], backups[-n:]

    logger.info("Rotate backups")
    logger.info("Found %d backup/s", len(backups))
    logger.info("Deleting %d and keeping %d backup/s", len(remove), len(keep))

    for _, item in remove:
        logger.verbose(f"    deleting backup '{item}'")
        if not args.dry_run:
            if item.is_file():
                item.unlink()
            else:
                rmtree(item)

    for _, item in keep:
        logger.debug("    keeping backup 'item'", %s)
