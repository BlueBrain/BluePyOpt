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

from . import base  # NOQA
from . import simulators  # NOQA
from . import models  # NOQA
from . import evaluators  # NOQA
from . import mechanisms  # NOQA
from . import locations  # NOQA
from . import parameterscalers  # NOQA
from . import parameters  # NOQA
from . import morphologies  # NOQA
from . import efeatures  # NOQA
from . import objectives  # NOQA
from . import protocols  # NOQA
from . import responses  # NOQA
from . import recordings  # NOQA
from . import objectivescalculators  # NOQA
from . import stimuli  # NOQA

# TODO create all the necessary abstract methods
# TODO check inheritance structure
# TODO instantiate using 'simulation env' as parameter, instead of cell
