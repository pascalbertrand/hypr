#!/usr/bin/env python3

"""
hypr
====

A RESTful microservice framework with the simplicity and security in mind.
"""


import os, re
from setuptools import setup, find_packages

# read the version number from package
f = open(os.path.join(os.path.dirname(__file__), 'hypr', '__init__.py'))
v, = re.search('.*__version__ = \'(.*)\'.*', f.read(), re.MULTILINE).groups()


setup(

    name='hypr',
    version=v,

    author='Morgan Delahaye-Prat',
    author_email='mdp@m-del.net',
    maintainer='Morgan Delahaye-Prat',
    maintainer_email='mdp@m-del.net',

    url='https://project-hypr.github.io',
    description=__doc__,
    long_description=open('README.rst').read(),

    install_requires=open('requirements.txt').read().splitlines(),
    tests_require=['pytest', 'pytest-cov', 'coveralls'],

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=[],

    license='BSD',
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]

)
