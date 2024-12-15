"""
Zabbix backup utility to dump the database and save the configuration files.
"""
import logging


VERSION = 1

logging.basicConfig(format='[%(levelname)-8s] %(message)s', level=logging.DEBUG)

logger = logging.getLogger()

# Remove default logger handlers
for handler in logger.handlers:
    logger.removeHandler(handler)

# Add a logger handler for the console:
# Console logger level will be set in during argument parsing.
# An additional handler will be attached in __main__.py with
# level set to DEBUG for logfile storing
console_logger = logging.StreamHandler()
logger.addHandler(console_logger)
