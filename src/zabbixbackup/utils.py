import logging
from os import environ
import shutil
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from .tables import zabbix

logger = logging.getLogger()


def quote(s):
    # good enough? shlex.quote alone is adding too many extras
    # must be readable, not immediately reuseable
    r = repr(s)
    if (
        len(r) - 2 != len(s)
        or any(ch in s for ch in " ()|")
    ):
        return r

    return s


def DPopen(*args, **kwargs):
    stderr = kwargs.get("stderr", subprocess.PIPE)
    if logger.isEnabledFor(logging.DEBUG):
        stderr = None

    kwargs["stderr"] = stderr

    return subprocess.Popen(*args, **kwargs)


def process_repr(cmd=None, env=None):
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


class Command(object):
    def __init__(self, command, env_extra={}) -> None:
        self.env_extra = env_extra
        self.env = {**environ, **env_extra}
        self.command = tuple(map(str, command))

    def reprexec(self):
        rargs = map(quote, self.command)

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

    def exec(self, **kwargs):
        """
        Wrapper for subprocess.run.
        
        force 'text' output and returns 'stdout' as a tuple of lines
        where the last line is omitted if empty (it generally is).

        Return None on error (actual error, not the process retvalue)
        """
        if "text" not in kwargs:
            kwargs["text"] = True

        # allow overloading of stdin and stdout
        # stderr is used for logging in case of errors
        stdin  = subprocess.PIPE if "stdin"  not in kwargs else kwargs["stdin"]
        stdout = subprocess.PIPE if "stdout" not in kwargs else kwargs["stdout"]
        stderr = subprocess.PIPE

        if logger.isEnabledFor(logging.DEBUG):
            stderr = None

        try:
            result = subprocess.run(
                self.command, **kwargs,
                env=self.env,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                check=True,
            )
            out = result.stdout

        except subprocess.CalledProcessError as e:
            #logging.debug(e.stderr.rstrip())
            logger.debug("Return code %d", e.returncode)
            return None
        except FileNotFoundError:
            logger.critical("Command not found \"%s\"", self.command[0])
            return None

        if stdout == subprocess.PIPE:
            lines = tuple(map(str.strip, out.split("\n")))
            if lines:
                if lines[-1] == "":
                    return lines[:-1]
            return result.returncode, lines

        return result.returncode, []


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
        #logging.debug(e.stderr.rstrip())
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

    #out = run(("command", "-v", *names))
    #if out is None:
    #    return False
    #return len(out) == len(names)


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


def rlookup(ipaddr):
    try:
        response = socket.gethostbyaddr(ipaddr) # socket.getfqdn?
        host = repr(response[0])
        return host
    except Exception:
        return False


def build_compress_command(profile):
    algo, level, extra = profile

    extension = {"xz": ".xz", "gzip": ".gz", "bzip2": ".bz2"}

    env = {}
    ext = extension[algo]

    if check_binary(algo):
        cmd = (algo, f"-{level}", ) + extra
        pipe = cmd
        return env, ext, cmd, pipe

    if check_binary("7z"):
        cmd = ("7z", "a", f"-t{algo}", )
        pipe = ("7z", "a", f"-t{algo}", "-si", )
        return env, cmd, ext, pipe

    raise NotImplementedError(f"Compression binary not available '{algo}'")


def build_tar_command(profile):
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
    raw_version = query_result[0]
    major = int(raw_version[:-6])
    minor = int(raw_version[-6:-4])
    revision = int(raw_version[-4:])

    version = f"{major}.{minor}.{revision}"

    return version, (major, minor, revision)


def create_name(args):
    dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"zabbix_{args.host}_{dt}"


def preprocess_tables_lists(args, table_list):
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

    #for key, value in dict_args.items():
    #    if key in keys or key == "scope":
    #        continue
    #    str_args.append(f"    {key:<24}: {value}")

    logger.info("\n".join(str_args))
