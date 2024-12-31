# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring
# pylint: disable=unused-import
import os
import unittest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree
from types import SimpleNamespace as NS
import logging
from .. import console_logger
from ..rotation import rotate


console_logger.setLevel(logging.ERROR)


class TestRotation(unittest.TestCase):
    def setUp(self):
        self.root = Path(".").absolute()

        # pylint: disable-next=consider-using-with
        self.tmp_dir = mkdtemp(prefix="test_rotate_", dir=self.root)
        self.test_root = Path(self.tmp_dir).absolute()

    def tearDown(self):
        os.chdir(self.root)
        rmtree(self.test_root)
        return super().tearDown()

    def test_rotate_keep_everything(self):
        test_bed = self.test_root / "keep_everything"
        test_bed.mkdir()

        os.chdir(test_bed)

        testbed = Path(".")

        (test_bed / "zabbix_127.0.0.1_19700101-000001").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000002").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000003.tar").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000004.tar").touch()

        args = NS(host="127.0.0.1", name=None, rotate=0)

        rotate(args)

        items = tuple(testbed.iterdir())

        self.assertEqual(len(items), 4, f"Expected 4 items: {items}")


    def test_rotate_keep_one(self):
        test_bed = self.test_root / "keep_one"
        test_bed.mkdir()

        os.chdir(test_bed)

        testbed = Path(".")

        (test_bed / "zabbix_127.0.0.1_19700101-000001").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000002").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000003.tar").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000004.tar").touch()
        (test_bed / "zabbix_127.0.0.2_19700101-000003.tar").touch()

        args = NS(host="127.0.0.1", name=None, rotate=1, dry_run=False)

        rotate(args)

        items = sorted(map(str, testbed.iterdir()))

        expected = [
            "zabbix_127.0.0.1_19700101-000004.tar",
            "zabbix_127.0.0.2_19700101-000003.tar",
        ]

        self.assertListEqual(items, expected)


    def test_rotate_keep_many(self):
        test_bed = self.test_root / "keep_many"
        test_bed.mkdir()

        os.chdir(test_bed)

        testbed = Path(".")

        (test_bed / "zabbix_127.0.0.1_19700101-000001").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000002").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000003.tar").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000004.tar").touch()
        (test_bed / "zabbix_127.0.0.2_19700101-000003.tar").touch()

        args = NS(host="127.0.0.1", name=None, rotate=3, dry_run=False)

        rotate(args)

        items = sorted(map(str, testbed.iterdir()))

        expected = [
            "zabbix_127.0.0.1_19700101-000002",
            "zabbix_127.0.0.1_19700101-000003.tar",
            "zabbix_127.0.0.1_19700101-000004.tar",
            "zabbix_127.0.0.2_19700101-000003.tar",
        ]

        self.assertListEqual(items, expected)


    def test_rotate_multiple_formats(self):
        test_bed = self.test_root / "keep_many"
        test_bed.mkdir()

        os.chdir(test_bed)

        testbed = Path(".")

        (test_bed / "zabbix_127.0.0.1_19700101-000001").mkdir()
        (test_bed / "zabbix_127.0.0.1_19700101-000002.tar").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000003.tar.gz").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000004.tar.xz").touch()
        (test_bed / "zabbix_127.0.0.1_19700101-000005.tar.bz2").touch()
        (test_bed / "zabbix_127.0.0.2_19700101-000005.tar").touch()

        args = NS(host="127.0.0.1", name=None, rotate=1, dry_run=False)

        rotate(args)

        items = sorted(map(str, testbed.iterdir()))

        expected = [
            "zabbix_127.0.0.1_19700101-000005.tar.bz2",
            "zabbix_127.0.0.2_19700101-000005.tar",
        ]

        self.assertListEqual(items, expected)


class TestRotationRegex(unittest.TestCase):
    def test_rotate_valid(self):
        self.assertEqual(True, True)


    def test_rotate_invalid(self):
        self.assertEqual(True, True)
