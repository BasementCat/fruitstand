#!/usr/bin/env python
import os
from setuptools import setup

def read(filen):
    with open(os.path.join(os.path.dirname(__file__), filen), "r") as fp:
        return fp.read()
 
setup (
    name = "fruitstand",
    version = "0.1",
    description = "Web-based digital signage (designed for the RPi + Raspbian)",
    long_description = read("README.md"),
    author = "Alec Elton",
    author_email = "alec.elton@gmail.com",
    url = "https://github.com/BasementCat/fruitstand",
    packages = ["fruitstand", "tests"],
    test_suite = "nose.collector",
    install_requires = ["bottle"],
    tests_require = ["nose"]
)