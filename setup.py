# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

VERSION = "2.0.0.dev"

with open("README.md", encoding = "utf-8") as f:
    long_description = f.read()

with open("LICENSE", encoding = "utf-8") as f:
    license_data = f.read()


def get_requirements():
    with open("requirements.txt") as fp:
        return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


install_requires = get_requirements()

setup(
        name = "multibajajmgt",
        version = VERSION,
        long_description = long_description,
        long_description_content_type = "text/markdown",
        license = license_data,
        author = "Yohan Avishke",
        classifiers = [  # Optional
            "Development Status :: 2 - Development/Stable",
            "Intended Audience :: Developers",
            "License :: BSD 2-Clause License",
            "Programming Language :: Python :: 3.10.3",
            ],
        package_dir = {"": "src"},
        packages = find_packages("src"),
        python_requires = ">=3.10",
        install_requires = install_requires
        )
