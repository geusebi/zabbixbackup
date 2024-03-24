"""Zabbix database backup utility for postgres and mysql"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")


setup(
    name="zabbixbackup",
    version="0.0.1a1",
    description=__doc__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/",  TODO: add gitlab or github repo homepage (see also project_urls)
    author="Giampaolo Eusebi",
    author_email="giampaolo.eusebi@gmail.com",
    classifiers=[  # https://pypi.org/classifiers/
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Database",
        "Topic :: System :: Recovery Tools",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="zabbix, backup, configuration, postgresql, postgre, psql, mysql",
    packages=["zabbixbackup"],
    python_requires=">=3.7, <4",
    install_requires=[],
    extras_require={},
    package_data={
        "zabbixbackup": ["assets/zabbix_server.conf"],
    },
    entry_points={
        "console_scripts": [
            "zabbixbackup=zabbixbackup:main",
        ],
    },
    project_urls={  # Optional
        # "Bug Reports": "https://github.com/pypa/sampleproject/issues",
        # "Say Thanks!": "http://saythanks.io/to/example",
        "Source": "https://github.com/pypa/sampleproject/",
    },
)