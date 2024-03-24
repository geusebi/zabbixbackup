from subprocess import check_output, CalledProcessError
from pathlib import Path
from shlex import quote as shquote


def quote(s):
    return shquote(str(s))


class CurryCmd(object):
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
    Wrapper for subprocess.check_output.
    
    force 'text' output and returns 'stdout' as a tuple of lines
    where the last line is omitted if empty (it generally is).

    Return None on error (actual error, not the process retvalue)
    """
    if "text" not in kwargs:
        kwargs["text"] = True

    try:
        out = check_output(*args, **kwargs)
    except (CalledProcessError, FileNotFoundError) as e:
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
