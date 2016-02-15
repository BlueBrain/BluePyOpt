"""Tests of the main bluepyopt module"""

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

# pylint:disable=W0612

import types
import nose.tools as nt


def test_import():
    """BluePyOpt: test importing bluepyopt"""
    import bluepyopt  # NOQA


def test_neuron_import():
    """BluePyOpt: test if bluepyopt.neuron import was successful"""
    import bluepyopt.importer  # NOQA
    nt.assert_is_instance(bluepyopt.importer.neuron, types.ModuleType)
