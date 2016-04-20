"""Init script"""

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

# pylint: disable=W0611

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .api import *  # NOQA
import bluepyopt.optimisations
import bluepyopt.deapext.optimisations

# Add some backward compatibility for the time when DEAPoptimisation not in
# deapext yet
# TODO deprecate this
bluepyopt.optimisations.DEAPOptimisation = \
    bluepyopt.deapext.optimisations.DEAPOptimisation

import bluepyopt.evaluators
import bluepyopt.objectives
import bluepyopt.parameters  # NOQA

# TODO let objects read / write themselves using json
# TODO create 'Variables' class
# TODO use 'locations' instead of 'location'
# TODO add island functionality to optimiser
# TODO add plotting functionality
# TODO show progress bar during optimisation
