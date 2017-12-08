#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages

base_path = os.path.dirname(__file__)

with open(os.path.join(base_path, 'requirements.txt')) as reqs:
    install_requires = [r.strip() for r in reqs.readlines() if not r.startswith('#')]

is_build = len(sys.argv) > 1 and sys.argv[1] in ['sdist', 'bdist']

setup(
    name="schrodinger",
    version="0.1",
    packages=find_packages(),
    author="Shaun Kruger",
    author_email="shaun.kruger@gmail.com",
    description="Tools to improve visibility into the running state of your code",
    url="http://stormsherpa.com",
    license="LGPL",
    include_package_data=True,
    install_requires=install_requires,
)
