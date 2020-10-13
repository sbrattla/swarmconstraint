# -*- coding: utf-8 -*-

# Learn more: https://github.com/sbrattla/swarmconstraint/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='swarmconstraint',
    version='0.1.0',
    description='Docker Swarm soft placement constraint management application',
    long_description=readme,
    author='Stian Brattland',
    author_email='stian@octetnest.no',
    url='https://github.com/sbrattla/swarmconstraint',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
