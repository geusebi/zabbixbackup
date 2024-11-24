import logging
import subprocess
from pathlib import Path
from datetime import datetime
from .tables import zabbix
#from shlex import quote as shquote


def quote(s):
    # good enough? shlex.quote was adding too many extras
    r = repr(s)
    if (
        len(r) - 2 != len(s)
        or any(ch in s for ch in " ()|")
    ):
        return r
    
    return s


class CurryCommand(object):
    def __init__(self, cmd, env, env_extra):
        merged_env = {**env, **env_extra}
        self.cmd, self.env, self.env_extra = (
            list(map(str, cmd)),
            merged_env,
            env_extra,
        )

    def exec(self, *args):
        command = self.cmd + list(args)
        return run(command, env=self.env)

    def reprexec(self, *args):
        rargs = map(quote, self.cmd + list(args))

        str_env = " ".join((
            f"{key}={quote(value)}"
            for key, value
            in self.env_extra.items()))

        # Good enough
        output = ""
        if str_env:
            output += str_env + " \\\n"

        output += " ".join((
            f"\\\n    {line}" if line.startswith("-") else line for line in rargs
        ))
        
        return output

    __repr__ = reprexec


def run(*args, **kwargs):
    """
    Wrapper for subprocess.run.
    
    force 'text' output and returns 'stdout' as a tuple of lines
    where the last line is omitted if empty (it generally is).

    Return None on error (actual error, not the process retvalue)
    """
    if "text" not in kwargs:
        kwargs["text"] = True

    stderr = subprocess.PIPE
    try:
        logger = logging.getLogger()
        if logger.isEnabledFor(logging.DEBUG):
            stderr = None
    except Exception:
        pass

    try:
        result = subprocess.run(
            *args, **kwargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=stderr)
        out = result.stdout

    except subprocess.CalledProcessError as e:
        #logging.debug(e.stderr.rstrip())
        logging.debug(f"return code {e.returncode}")
        return None
    except FileNotFoundError:
        logging.critical(f"Command not found \"{args[0]}\"")
        return None

    lines = tuple(map(str.strip, out.split("\n")))
    if lines:
        if lines[-1] == "":
            return lines[:-1]

    return lines


def check_binary(*names):
    """Checks whether 'names' are all valid commands in the current shell."""
    out = run(("command", "-v", *names))

    if out is None:
        return False

    return len(out) == len(names)


def try_find_sockets(search, port):
    """Try to locate available postgresql sockets."""
    if not check_binary("netstat"):
        return tuple()

    out = run(("netstat", "-lxn"))
    sockets = []
    for line in out:
        # not perfect but it works reasonably enough
        try:
            path = Path(line.split()[-1])
        except IndexError:
            pass
            folder = path.parent
            name = path.name
            if search not in folder or str(port) not in name:
                continue

            sockets.append(path)

    return tuple(sockets)


def rlookup(ip):
    output = run(["dig", "+noall", "+answer", "-x", ip])
    if not output:
        return None

    parts = list(map(str.strip, output.split()))
    if len(parts) == 0:
        return None
    dn = parts[-1]

    subdomains = dn.split(".")
    if len(subdomains) == 0:
        return None

    return subdomains[0]


def parse_zabbix_version(query_result):
    raw_version = query_result[0]
    major = int(raw_version[:-6])
    minor = int(raw_version[-6:-4])
    revision = int(raw_version[-4:])
    
    version = f"{major}.{minor}.{revision}"

    return version, (major, minor, revision)


def create_name(args, version):
    dt = datetime.now().strftime("%Y%m%d-%H%M")
    name = f"zabbix_{args.host}_{dt}_{version}"

    return name


def preprocess_tables_lists(args, table_list):
    logging.debug(f"Table list: {table_list!r}")
    logging.verbose(f"Tables found: {len(table_list)}")

    tables = set(table_list)
    config = tables.intersection(zabbix.config)
    monitoring = tables.intersection(zabbix.monitoring)
    unknown = tables.difference(config, monitoring)

    logging.verbose(f"Config tables: {len(config)}")
    logging.verbose(f"Monitoring tables: {len(monitoring)}")
    logging.verbose(f"Unknown tables: {len(unknown)}")

    nodata, ignore, fail = [], [], []
    if args.monitoring == "nodata":
        nodata += monitoring

    if args.unknown == "nodata":
        nodata += unknown
    elif args.unknown == "ignore":
        ignore += unknown 
    elif args.unknown == "fail":
        fail += unknown

    return sorted(ignore), sorted(nodata), sorted(fail)


def pretty_log_args(args):
    """Print arguments via 'logging.info' in a readable way"""

    keys = args._keys

    str_args = ["Arguments:"]
    for key in keys:
        value = getattr(args, key, None)
        #if value is None:
        #    continue
        if key == "passwd" and value is not None:
            value = "[omissis]"

        str_args.append(f"    {key:<24}: {value}")

    #for key, value in dict_args.items():
    #    if key in keys or key == "scope":
    #        continue
    #    str_args.append(f"    {key:<24}: {value}")

    logging.verbose("\n".join(str_args))