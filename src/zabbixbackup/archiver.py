from pathlib import Path
from .utils import run
from .utils import CurryCommand
from os import environ
from copy import deepcopy
from shutil import rmtree
import logging


def parse_save_files(files):
    """
    Read a list of files and directories.
    
    One item per line.
    Spaces are trimmed and blank lines or lines starting with a # are ignored.
    """
    with open(files, "r") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("#"):
                continue
            yield Path(line)


def save_files(args):
    """
    Copy files and directories as per user arguments.
    
    Default file list: (module) zabbixbackup/assets/files.
    """
    if args.save_files is True:
        files = args.files
        if files == "-":
            files = Path(__file__).parent / "assets" / "files"

        copy_files(files, args.scope["tmp_dir"] / "root")


def copy_files(save_files, base_dir):
    """
    Copy a list of files or directories in base_dir.

    Directory structure is replicated.
    """
    base_dir = base_dir.absolute()
    items = parse_save_files(save_files)

    for item in items:
        if not item.exists():
            logging.info(f"Filepath not found {item}, ignoring...")
            continue

        dest = base_dir / item.absolute().relative_to("/")
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
            # TODO: copy permission on entire directory tree?

        if run(["cp", "-a", str(item), str(dest)]) is None:
            logging.warning(f"Cannot copy {item}, ignoring...")
        else:
            logging.info(f"Copying {item}")


def archive(args):
    """
    Create the actual archive file.

    Based on user arguments it will be compressed accordingly.
    """
    scope = args.scope
    tmp_dir: Path = args.scope["tmp_dir"]
    

    archive_dir = args.outdir / args.scope["name"]
    tmp_dir.rename(archive_dir)

    if scope["archive_command"] != None:
        archive_name = (
            archive_dir.parent /
            (archive_dir.name + scope["archive_extension"])
        )

        env = deepcopy(environ)
        compress = CurryCommand(
            scope["archive_command"] + [archive_name, archive_dir],
            env, scope["archive_env"]
            )
        logging.debug(f"Compress command: \n{compress.reprexec()}")

        result = compress.exec()
        if result is not None:
            rmtree(archive_dir)
    else:
        # Leave as plain directory
        pass