# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import unittest
import logging
from .. import console_logger
from ..utils import build_compress_command


console_logger.setLevel(logging.ERROR)


class TestUtils(unittest.TestCase):
    def test_compress_standard_cli(self):
        profile = ("xz", 6, ("some_params", ))
        result = build_compress_command(
            profile, check=False, strategy=("standard", ))

        expected = (
            {},                            # environment
            ".xz",                         # extension
            ("xz", "-6", "some_params", ), # command
            ("xz", "-6", "some_params", )  # pipe
        )

        self.assertTupleEqual(result, expected)

        profile = ("gzip", 6, ("some_params", ))
        result = build_compress_command(
            profile, check=False, strategy=("standard", ))

        expected = (
            {},                              # environment
            ".gz",                           # extension
            ("gzip", "-6", "some_params", ), # command
            ("gzip", "-6", "some_params", )  # pipe
        )

        self.assertTupleEqual(result, expected)

        profile = ("bzip2", 6, ("some_params", ))
        result = build_compress_command(
            profile, check=False, strategy=("standard", ))

        expected = (
            {},                               # environment
            ".bz2",                           # extension
            ("bzip2", "-6", "some_params", ), # command
            ("bzip2", "-6", "some_params", )  # pipe
        )


    def test_compress_fallback_cli(self):
        profile = ("xz", 6, ("some_params", ))
        result = build_compress_command(
            profile, check=False, strategy=("fallback", ))

        expected = (
            {},                          # environment
            ".xz",                       # extension
            ("7z", "a", "-txz", ),       # command
            ("7z", "a", "-txz", "-si", ) # pipe
        )

        self.assertTupleEqual(result, expected)


    def test_compress_not_available_cli(self):
        profile = ("xz", 6, ("some_params", ))

        with self.assertRaises(NotImplementedError):
            build_compress_command(
                profile, check=False, strategy=tuple())
