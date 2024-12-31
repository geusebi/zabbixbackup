# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import unittest
import logging
from types import SimpleNamespace as NS
from .. import console_logger
from ..utils import (
    build_compress_command, build_tar_command, create_name, parse_zabbix_version
)


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


class TestParseZabbixVersion(unittest.TestCase):
    def test_parse_zabbix_version(self):
        in_out_pairs = (
            ("07020001", "7.2.1", ),
            ("06040010", "6.4.10", ),
            ("05020011", "5.2.11", ),
        )

        for raw, expected in in_out_pairs:
            with self.subTest(f"version {raw!r}"):
                result, _ = parse_zabbix_version((raw, ))
                self.assertEqual(result, expected)


class TestCreateName(unittest.TestCase):
    def test_create_name(self):
        args = NS(name=None, host="127.0.0.1")
        in_out_pairs = (
            (1735658751, "zabbix_127.0.0.1_20241231-162551", ),
            (1234567890, "zabbix_127.0.0.1_20090214-003130", ),
            (0, "zabbix_127.0.0.1_19700101-010000", ),
        )

        for ts, expected in in_out_pairs:
            with self.subTest(f"timestamp {ts!r}"):
                result = create_name(args, ts=ts)
                self.assertEqual(result, expected)
