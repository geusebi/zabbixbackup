from collections import namedtuple
from .tablesraw import tablesraw

table_type = namedtuple("TableSpec", ["name", "begin", "end", "data"])

# Table as a dict of TableSpec namedtuple in the form of
# 
#     {"tablename": TableSpec("name", "begin", "end", "data"), ...}
# 
# where begin and end are the first and last release the table has appeared in,
# data specify if the table is data or schemaonly flagged.

tables = dict(
    (spec[0], table_type(*spec))
    for spec in tablesraw
)
