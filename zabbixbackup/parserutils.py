from pathlib import Path

__all__ = ["zabbix_try_read_defaults", "zabbix_try_read_config", "map_clean_vars"]


def zabbix_try_read_defaults(path, defaults=None):
    """
    Try reading default values from comments.
    
    Empty values are skipped silently.
    If a line starts with "# Default" the next line is probed for a key, value pair.
    """
    if defaults is None:
        defaults = {}

    with path.open("r") as fh:
        try_read = False
    
        for line in map(str.strip, fh):
            if line == "":
                continue
            
            if try_read:
                try_read = False

                if not line.startswith("#"):
                    continue

                line = line.strip("#").strip()
                key, eq, value = map(str.strip, line.partition("="))
                if eq == "=" and len(key) and len(value):
                    defaults[key] = value
                continue

            if line.startswith("# Default"):
                try_read = True
                continue

    return defaults


def zabbix_try_read_config(path, config=None):
    """
    Try reading key value pairs from zabbix config file.
    
    Empty values are skipped silently.
    The defaults from the last shipped version are used as a base. Then are
    overriden by defaults from 'path' and, lastly, from the actual specified values.
    """
    last_shipped_config = Path(__file__).parent / "assets" / "zabbix_server.conf"

    package_defaults = zabbix_try_read_defaults(last_shipped_config, config)
    
    actual_config = zabbix_try_read_defaults(path, package_defaults)

    with path.open("r") as fh:
        for line in map(str.strip, fh):
            if line == "" or line.startswith("#"):
                continue
            
            key, eq, value = map(str.strip, line.partition("="))
            if eq == "=" and len(key) and len(value):
                actual_config[key] = value

    return actual_config


def map_clean_vars(config, map_clean_var):
    return dict((
        (new_name, type(config[key]))
        for key, new_name, type in map_clean_var
        if key in config
    ))
