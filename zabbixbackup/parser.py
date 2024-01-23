from .parsercli import build_parser
from .parserpost import postprocess

from pathlib import Path
from types import SimpleNamespace as NS


# Script default values
# (these are important to allow to separate user provided values during parsing)
# 'dest' name actions in parsing must be the same as in this namespace
defaults = NS()
defaults.type                 = "psql"

defaults.read_zabbix_config   = True
defaults.zabbix_config        = "/etc/zabbix/zabbix_server.conf"

defaults.read_mysql_config    = False
defaults.mysql_config         = Path("/etc/mysql/my.cnf")
defaults.dry_run              = False

defaults.host                 = "127.0.0.1"
defaults.port                 = "mysql=3306 or psql=5432" # handled manually
defaults.sock                 = None
defaults.user                 = "zabbix"
defaults.passwd               = "-"
defaults.dbname               = "zabbix"
defaults.schema               = "public"
defaults.rlookup              = True

defaults.unknown              = "ignore"
defaults.columns              = False

defaults.compression          = "gzip"
defaults.format               = "custom"
defaults.rotate               = 0
defaults.outdir               = Path(".")

defaults.quiet                = False
defaults.verbose              = True
defaults.very_verbose         = False
defaults.debug                = False


def parse(argv):
    """
    Parse arguments from the command line and return a Namespace.

    Arguments are handled and adjusted according to zabbix behaviour and
    user selection (see @postprocess function).
    """
    # The double call to 'parse_args' is for properly separating user provided values from
    # script default values. In order to keep it working as expected *every* value in the parser
    # must have a default (otherwise the next line will prompt the help screen to the user without
    # regardless of real arguments). TODO: use default dict at the top and avoid this double call?
    parser = build_parser(defaults)

    temp_args = parser.parse_args(argv)

    try:
        _defaults = temp_args.__dict__
        _blanks = dict((key, None) for key in temp_args.__dict__.keys())

        parser.set_defaults(**_blanks)
        uargs = parser.parse_args(argv)
        parser.set_defaults(**_defaults)

    except Exception:
        raise ValueError(
            "Parse error: should never happen here."
            "Really.. something is wrong.")

    return postprocess(parser, uargs, defaults)
