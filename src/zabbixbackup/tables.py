from types import SimpleNamespace as NS
from collections import namedtuple
from .tablesraw import raw_tables, CONFIG, MONITORING

TableType = namedtuple("TableSpec", ["name", "begin", "end", "data"])

# Table as a dict of TableSpec namedtuple in the form of
#
#     {"tablename": TableSpec("name", "begin", "end", "data"), ...}
#
# where begin and end are the first and last release the table has appeared in,
# data specify if the table is data or schemaonly flagged.

tables_spec = dict(
    (spec[0], TableType(*spec))
    for spec in raw_tables
)

all_tables = set(tables_spec.keys())

config = set(
    name
    for name, spec in tables_spec.items()
    if spec.data == CONFIG
)

monitoring = set(
    name
    for name, spec in tables_spec.items()
    if spec.data == MONITORING
)

zabbix = NS(config=config, monitoring=monitoring, tables=all_tables)
