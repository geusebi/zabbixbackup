# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import unittest
import logging
from .. import console_logger
from ..utils import build_compress_command, build_tar_command, check_binary


console_logger.setLevel(logging.ERROR)


class TestBuildCompress(unittest.TestCase):
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


class TestBuildTar(unittest.TestCase):
    def test_build_tar_cli(self):
        with self.subTest("uncompressed tar"):
            profile = ("tar", 6, ("some_params", ))
            result = build_tar_command(profile, check=False)

            expected = (
                {},               # environment
                ".tar",           # extension
                ("tar", "-cf", ), # command
            )

            self.assertTupleEqual(result, expected)


        with self.subTest("xz"):
            profile = ("xz", 6, ("some_params", ))
            result = build_tar_command(profile, check=False)

            expected = (
                {"XZ_OPT": "-6 some_params"}, # environment
                ".tar.xz",                    # extension
                ("tar", "-cJf", ),             # command
            )

            self.assertTupleEqual(result, expected)


        with self.subTest("gzip"):
            profile = ("gzip", 6, ("some_params", ))
            result = build_tar_command(profile, check=False)

            expected = (
                {"GZIP": "-6 some_params"}, # environment
                ".tar.gz",                  # extension
                ("tar", "-czf", ),          # command
            )

            self.assertTupleEqual(result, expected)

        with self.subTest("bzip2"):
            profile = ("bzip2", 6, ("some_params", ))
            result = build_tar_command(profile, check=False)

            expected = (
                {"BZIP2": "-6 some_params"}, # environment
                ".tar.bz2",                  # extension
                ("tar", "-cjf", ),           # command
            )

            self.assertTupleEqual(result, expected)


    def test_tar_not_available_cli(self):
        profile = ("xz", 6, ("some_params", ))

        with self.assertRaises(NotImplementedError):
            build_compress_command(
                profile, check=False, strategy=tuple())