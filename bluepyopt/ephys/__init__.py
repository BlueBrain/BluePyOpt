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

# pylint: disable=W0511

import simulators  # NOQA
import models  # NOQA
import evaluators  # NOQA
import mechanisms  # NOQA
import locations  # NOQA
import parameterscalers  # NOQA
import parameters  # NOQA
import morphologies  # NOQA
import efeatures  # NOQA
import objectives  # NOQA
import protocols  # NOQA
import responses  # NOQA
import recordings  # NOQA
import objectivescalculators  # NOQA
import stimuli  # NOQA

# TODO create all the necessary abstract methods
# TODO check inheritance structure
# TODO instantiate using 'simulation env' as parameter, instead of cell
