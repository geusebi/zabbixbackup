# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import datetime


class TZUTC(datetime.tzinfo):
    """Dummy timezone to test deterministically."""
    # pylint: disable=unused-argument
    _offset = datetime.timedelta(0)
    _dst = datetime.timedelta(0)
    _name = "UTC"

    def utcoffset(self, *args):
        return self.__class__._offset

    def dst(self, *args):
        return self.__class__._dst

    def tzname(self, *args):
        return self.__class__._name
