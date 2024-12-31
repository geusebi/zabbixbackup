# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import unittest
import logging
from types import SimpleNamespace as NS
from .. import console_logger
from ..parser_post import _handle_archiving, _handle_mysqlcompression, _parse_compression


console_logger.setLevel(logging.ERROR)


class TestParserPost(unittest.TestCase):
    def setUp(self):
        self.mock_parser = NS()

        def _error(msg):
            raise ValueError(msg)
        self.mock_parser.error = _error

        return super().setUp()


    def test__parse_compression(self):
        in_out_pairs = (
            ("5",       ("gzip",  "5", tuple())),
            ("gzip",    ("gzip",  "6", tuple())),
            ("xz",      ("xz",    "6", tuple())),
            ("xz:7",    ("xz",    "7", tuple())),
            ("xz:7e",   ("xz",    "7", ("--extreme", ))),
            ("bzip2",   ("bzip2", "6", tuple())),
            ("bzip2:1", ("bzip2", "1", tuple())),
        )

        for param, expected in in_out_pairs:
            with self.subTest(f"input: {param!r}"):
                result = _parse_compression(self.mock_parser, param)
                self.assertTupleEqual(expected, result)


    def test__parse_compression_error(self):
        inputs = (
            "",
            "0",
            "xz:0",
            "gzip:0",
            "bzip2:0",
            "bzip2:6e",
            "something",
        )

        for param in inputs:
            with self.subTest(f"input: {param!r}"), self.assertRaises(ValueError):
                _parse_compression(self.mock_parser, param)


    def test__handle_mysqlcompression(self):
        # other params combinations are tested in '_parse_compression'
        # just checks whether there is an output or not
        inputs = (
            "xz",
            "gzip",
            "bzip2",
        )

        mock_args = NS(scope={"parser": self.mock_parser}, mysqlcompression=None)
        for param in inputs:
            with self.subTest(f"input: {param!r}"):
                mock_args.mysqlcompression = param
                mock_args.scope["mysqlcompression"] = None

                _handle_mysqlcompression(mock_args)

                self.assertNotEqual(None, mock_args.scope["mysqlcompression"])

        with self.subTest(f"input: {'-'!r}"):
            mock_args.mysqlcompression = "-"
            mock_args.scope["mysqlcompression"] = None

            _handle_mysqlcompression(mock_args)

            self.assertEqual(None, mock_args.scope["mysqlcompression"])

    def test__handle_archiving(self):
        # other params combinations are tested in '_parse_compression'
        # just checks whether there is an output or not
        inputs = (
            "tar",
            "xz",
            "gzip",
            "bzip2",
        )

        mock_args = NS(scope={"parser": self.mock_parser}, archive=None)
        for param in inputs:
            with self.subTest(f"input: {param!r}"):
                mock_args.archive = param
                mock_args.scope["archive"] = None

                _handle_archiving(mock_args)

                self.assertNotEqual(None, mock_args.scope["archive"])

        with self.subTest(f"input: {'-'!r}"):
            mock_args.archive = "-"
            mock_args.scope["archive"] = None

            _handle_archiving(mock_args)

            self.assertEqual(None, mock_args.scope["archive"])
