"""Import external modules"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

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


# TODO this should be abstracted away in a simulator class

# Import neuron
# Magic provided by M. Hines to disable banner during neuron import
# We need it until M. Hines disables the Neuron
# banner when importing neuron

import os
import imp
import ctypes

hoc_so = os.path.join(imp.find_module('neuron')[1] + '/hoc.so')

nrndll = ctypes.cdll[hoc_so]
ctypes.c_int.in_dll(nrndll, 'nrn_nobanner_').value = 1

import neuron  # NOQA
