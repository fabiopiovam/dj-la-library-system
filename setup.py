#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path and open files
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

try:
    REQUIREMENTS = open('requirements.txt').read()
except:
    REQUIREMENTS = None

try:
    DEPENDENCY_LINKS = [i.strip() for i in open("dependency_links.txt").readlines()]
except:
    DEPENDENCY_LINKS = None

try:
    README = open('README.md').read()
except:
    README = None

try:
    LICENSE = open('LICENSE').read()
except:
    LICENSE = None

setup(
    name='dj-la-library-system',
    version="v0.4.0",
    description=(
        'Django Library System Application'
    ),
    long_description=README,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCY_LINKS,
    license=LICENSE,
    author='Fábio Piovam Elias',
    author_email='fabio@laborautonomo.org',
    url='https://github.com/laborautonomo/dj-la-library-system/',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
