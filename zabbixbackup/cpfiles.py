from pathlib import Path
from .utils import run
import logging


def parse_save_files(files):
    with open(files, "r") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("#"):
                continue
            yield Path(line)


def copyfiles(save_files, base_dir):
    items = parse_save_files(save_files)

    for item in items:
        if not item.exists():
            logging.info(f"Filepath not found {item!r}, ignoring...")
            continue
        
        dest = base_dir / item
        if run(["cp", "-r", str(item), str(dest)]) is None:
            logging.warn(f"Cannot copy {item!r}, ignoring...")
        else:
            logging.info(f"Copying {item!r}")
