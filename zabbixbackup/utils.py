from subprocess import check_output, CalledProcessError
from pathlib import Path


def exec(*args, **kwargs):
    """
    Wrapper for subprocess.check_output.
    
    force 'text' output and returns 'stdout' as a tuple of lines
    where the last line is omitted if empty (it generally is).

    Return None on error (actual error, not the process retvalue)
    """
    if "text" not in kwargs:
        kwargs["text"] = True

    try:
        out = check_output(*args)
    except (CalledProcessError, FileNotFoundError):
        return None

    lines = tuple(map(str.strip, out.split("\n")))
    if lines:
        if lines[-1] == "":
            return lines[:-1]

    return lines


def check_binary(*names):
    """Checks wether 'names' are all valid commands in the current shell."""
    out = exec(("command", "-v", *names))

    if out is None:
        return False

    return len(out) == len(names)


def try_find_sockets(search, port):
    """Try to locate available postgresql sockets."""
    if not check_binary("netstat"):
        return tuple()

    out = exec(("netstat", "-lxn"))
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
