#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015-2016 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from setuptools import setup
from codecs import open
from os import path
import sys


def file_contents(*relpath):
    with open(path.join(path.dirname(__file__), *relpath), "rU",
            encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        name="intheam",
        version="0.0.3",
        description="Wrapper around the inthe.am API",
        long_description=file_contents("README.rst"),
        author="Adrián Pérez de Castro",
        author_email="adrian@perezdecastro.org",
        url="https://github.com/aperezdc/intheam-python",
        py_modules=["intheam"],
        scripts=["intheam-cli"],
        install_requires=[
            "gnarl>=0.1.0a3",
            "aiohttp>=0.16.0",
        ],
        extras_require={
            "cli": ["click>=4.0.0"],
        },
        license="MIT",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python",
            "Operating System :: OS Independent"
        ],
        test_suite="test",
    )
