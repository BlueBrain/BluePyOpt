#!/usr/bin/env python
"""BluePyOpt  setup """

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of eFEL <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import setuptools

# try:
#     from setuptools import setup, Extension
# except ImportError:
# from distutils.core import setup, Extension  # pylint: disable=E0611,F0401

setuptools.setup(
    name="bluepyopt",
    version="0.0.1",
    # install_requires=['numpy>=1.6'],
    install_requires=[],
    packages=setuptools.find_packages(),
    author="BlueBrain Project, EPFL",
    author_email="werner.vangeit@epfl.ch",
    description="Bluebrain Python Optimisation Library (bluepyopt)",
    long_description="Bluebrain Python Optimisation Library (bluepyopt)",
    license="LGPLv3",
    keywords=(
        'optimisation',
        'neuroscience',
        'BlueBrainProject'),
    url='https://github.com/BlueBrain/BluePyOpt',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public '
        'License v3 (LGPLv3)',
        'Programming Language :: Python :: 2.7',
        'Operating System :: POSIX',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities'],
    package_data={})
