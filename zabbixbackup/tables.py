from collections import namedtuple
from .tablesraw import tablesraw

table_type = namedtuple("TableSpec", ["name", "begin", "end", "data"])

tables = dict(
    (spec[0], table_type(*spec))
    for spec in tablesraw
)
