"""
Helper functions for saving configuration files
and to create a compressed tar archive.
"""
from os import environ
from pathlib import Path
from shutil import rmtree
import logging

from .utils import DPopen, run
from .utils import build_tar_command, process_repr

logger = logging.getLogger()


def parse_save_files(files):
    """
    Read a list of files and directories.
    
    One item per line.
    Spaces are trimmed and blank lines or lines starting with a # are ignored.
    """
    with open(files, "r", encoding="utf-8") as fh:
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

        copy_files(files, Path("host_root"))


def copy_files(files_index, base_dir):
    """
    Copy a list of files or directories in base_dir.

    Directory structure is replicated.
    """
    base_dir = base_dir.absolute()
    items = parse_save_files(files_index)

    for item in items:
        if not item.exists():
            logger.info("Filepath not found %s, ignoring...", item)
            continue

        dest = base_dir / item.absolute().relative_to("/")
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
            # TODO: copy permission on entire directory tree?

        # TODO: remove dependency on cp?
        if run(["cp", "-a", str(item), str(dest)]) is None:
            logger.warning("Cannot copy %s, ignoring...", item)
        else:
            logger.info("Copying %s", item)


def archive(archive_dir, args):
    """
    Create the actual archive file.

    Based on user arguments it will be compressed accordingly.
    """
    scope = args.scope
    profile = scope["archive"]

    if profile is not None:
        env, cmd, ext = build_tar_command(profile)
        name = archive_dir.name
        name_ext = name + ext
        tar_cmd = cmd + (name_ext, name, )
        tar_env = {**environ, **env}

        logger.debug("Archive command: \n%s\n", process_repr(tar_cmd, env))

        archive_exec = DPopen(tar_cmd, env=tar_env)
        archive_exec.communicate()

        if archive_exec.returncode == 0:
            logger.debug("Delete plain folder archive: %s\n", archive_dir)
            rmtree(archive_dir)

        return Path(name_ext).absolute()

    # Leave as plain directory
    return Path(archive_dir).absolute()
