#!/usr/bin/env python3

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

with open("version.py","r", encoding="utf-8") as latest:
    version = latest.read().split('"')[1]

setuptools.setup(
    name="showcues",
    version=version,
    author="Adrian of Doom.",
    author_email="spam@iodisco.com",
    description="showcues displays HLS CUE-IN and CUE-OUT tags with wallclock time",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/futzu/showcues",
    install_requires=[
        'new_reader >= 0.1.7',
        'm3ufu >= 0.0.73',
        'threefive >= 2.4.9',
    ],
    py_modules=["showcues"],
    scripts=['bin/showcues'],
    platforms='all',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.6",
)
