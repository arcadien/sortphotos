#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name='sortphotos',
    version='0.9.2',
    description='Organizes photos and videos into folders using date/time information',
    author='Andrew Ning',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=['exifread>=3.5,<4', 'hachoir>=3.4,<4'],
    license='MIT License',
    entry_points={
        'console_scripts': [
            'sortphotos = sortphotos.cli:main',
        ]
    }
)
