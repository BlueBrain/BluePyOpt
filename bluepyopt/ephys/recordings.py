"""Recording classes"""

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


import logging

from .importer import neuron
from . import responses

logger = logging.getLogger(__name__)


class Recording(object):

    """Response to stimulus"""

    def __init__(self, name=None, value=None, frozen=None):
        """Constructor"""

        self.name = name
        self.value = value
        self.frozen = frozen


class CompRecording(Recording):

    """Response to stimulus"""

    def __init__(
            self,
            name=None,
            value=None,
            frozen=None,
            location=None,
            variable='v'):
        """Constructor"""

        super(CompRecording, self).__init__(name=name, value=value, frozen=frozen)
        self.location = location
        self.variable = variable

        self.varvector = None
        self.tvector = None

        self.time = None
        self.voltage = None

        self.instantiated = False

    @property
    def response(self):
        """Return recording response"""

        if not self.instantiated:
            raise Exception(
                'Recording not instantiated before requesting response')

        return responses.TimeVoltageResponse(self.name,
                                             self.tvector.to_python(),
                                             self.varvector.to_python())

    def instantiate(self, sim=None, icell=None):
        """Instantiate recording"""

        logger.debug('Adding compartment recording of %s at %s',
                     self.variable, self.location)

        self.varvector = neuron.h.Vector()
        seg = self.location.instantiate(sim=sim, icell=icell)
        self.varvector.record(getattr(seg, '_ref_%s' % self.variable))

        self.tvector = neuron.h.Vector()
        self.tvector.record(neuron.h._ref_t)  # pylint: disable=W0212

        self.instantiated = True

    def destroy(self):
        """Destroy recording"""

        self.varvector = None
        self.tvector = None
        self.instantiated = False

    def __str__(self):
        """String representation"""

        return '%s: %s at %s' % (self.name, self.variable, self.location)
