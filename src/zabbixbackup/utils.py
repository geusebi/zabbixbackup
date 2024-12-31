"""
Helper functions for zabbixbackup.
"""
import logging
import shutil
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from .tables import zabbix

logger = logging.getLogger()


def quote(s):
    """Loosely quote parameters."""
    # good enough? shlex.quote alone is adding too many extras
    # must be readable, not immediately reuseable
    r = repr(s)
    if (
        len(r) - 2 != len(s)
        or any(ch in s for ch in " ()|")
    ):
        return r

    return s


def DPopen(*args, **kwargs): # pylint: disable=C0103:invalid-name
    """Execute a command via `Popen`."""
    stderr = kwargs.get("stderr", subprocess.PIPE)
    if logger.isEnabledFor(logging.DEBUG):
        stderr = None

    kwargs["stderr"] = stderr

    return subprocess.Popen(*args, **kwargs)


def process_repr(cmd=None, env=None):
    """Loosely format a command and its environment as a string."""
    if cmd is None:
        return "None"

    rargs = map(quote, cmd)

    str_env = " ".join((
        f"{key}={quote(value)}"
        for key, value
        in env.items()))

    # Good enough
    output = ""
    if str_env:
        output += str_env + " \\\n"

    output += " ".join((
        f"\\\n    {line}" if line.startswith("-") else line for line in rargs
    ))

    return output


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
    if logger.isEnabledFor(logging.DEBUG):
        stderr = None

    try:
        result = subprocess.run(
            *args, **kwargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=stderr)
        out = result.stdout

    except subprocess.CalledProcessError as e:
        logger.debug("Return code %d", e.returncode)
        return None
    except FileNotFoundError:
        logger.critical("Command not found \"%s\"", args[0])
        return None

    lines = tuple(map(str.strip, out.split("\n")))
    if lines:
        if lines[-1] == "":
            return lines[:-1]

    return lines


def check_binary(*names):
    """Checks whether 'names' are all valid commands in the current shell."""

    for name in names:
        if shutil.which(name) is None:
            return False
    return True


def try_find_sockets(search: str, port):
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

        folder = str(path.parent)
        name = path.name
        if search not in folder or str(port) not in name:
            continue

        sockets.append(path)

    return tuple(sockets)


def rlookup(ipaddr):
    """Perform a reverse address lookup."""

    hosts = socket.gethostbyaddr(ipaddr) # socket.getfqdn?
    if len(hosts):
        return repr(hosts[0])
    return None


def build_compress_command(profile, check=True, strategy=("standard", "fallback")):
    """Helper function to prepare a compress command."""
    algo, level, extra = profile

    extension = {"xz": ".xz", "gzip": ".gz", "bzip2": ".bz2"}

    env = {}
    ext = extension[algo]

    if "standard" in strategy and (not check or check_binary(algo)):
        cmd = (algo, f"-{level}", ) + extra
        pipe = cmd
        return env, ext, cmd, pipe

    if "fallback" in strategy and (not check or check_binary("7z")):
        cmd = ("7z", "a", f"-t{algo}", )
        pipe = ("7z", "a", f"-t{algo}", "-si", )
        return env, ext, cmd, pipe

    raise NotImplementedError(f"Compression binary not available '{algo}'")


def build_tar_command(profile):
    """Helper function to prepare a tar/compress command."""
    if not check_binary("tar"):
        raise NotImplementedError("Missing tar command")

    algo, level, extra = profile

    if algo == "tar":
        return {}, ("tar", "-cf", ), ".tar"

    extension = {"xz": ".tar.xz", "gzip": ".tar.gz", "bzip2": ".tar.bz2"}
    env_map = {"xz": "XZ_OPT", "gzip": "GZIP", "bzip2": "BZIP2"}
    tar_map = {"xz": "J", "gzip": "z", "bzip2": "j"}

    compr_env_var = env_map[algo]
    compr_flags = " ".join((f"-{level}", ) + extra)
    tar_flag = tar_map[algo]

    env = {compr_env_var: compr_flags}
    ext = extension[algo]
    cmd = ("tar", f"-c{tar_flag}f", )

    return env, cmd, ext


def parse_zabbix_version(query_result):
    """Parse zabbix version from `dbversion` value."""
    raw_version = query_result[0]
    major = int(raw_version[:-6])
    minor = int(raw_version[-6:-4])
    revision = int(raw_version[-4:])

    version = f"{major}.{minor}.{revision}"

    return version, (major, minor, revision)


def create_name(args):
    """Create a suitable name for a backup."""
    dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.name is not None:
        return f"zabbix_{args.name}_{dt}"
    return f"zabbix_{args.host}_{dt}"


def preprocess_tables_lists(args, table_list):
    """
    Partition tables as
        ignore tables,
        schema-only tables,
        and data-tables.
    """
    logger.debug("Table list: %r", table_list)
    logger.info("Tables found: %r", len(table_list))

    tables = set(table_list)
    config = tables.intersection(zabbix.config)
    monitoring = tables.intersection(zabbix.monitoring)
    unknown = tables.difference(config, monitoring)

    logger.info("Config tables: %d", len(config))
    logger.info("Monitoring tables: %d", len(monitoring))
    logger.info("Unknown tables: %d", len(unknown))

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

    keys = args._keys # pylint: disable=W0212:protected-access

    str_args = ["Arguments:"]
    for key in keys:
        value = getattr(args, key, None)
        #if value is None:
        #    continue
        if key == "passwd" and value is not None:
            value = "[omissis]"

        str_args.append(f"    {key:<24}: {value}")

    logger.info("\n".join(str_args))
