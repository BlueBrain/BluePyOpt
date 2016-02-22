"""Stimuli classes"""

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

logger = logging.getLogger(__name__)


class Stimulus(object):

    """Stimulus protocol"""

    def __init__(self):
        """Constructor"""
        pass

# TODO Add 'current' to the name


class NrnSquarePulse(Stimulus):

    """Stimulus protocol"""

    def __init__(self,
                 step_amplitude=None,
                 step_delay=None,
                 step_duration=None,
                 total_duration=None,
                 location=None):
        """Constructor"""

        Stimulus.__init__(self)
        self.step_amplitude = step_amplitude
        self.step_delay = step_delay
        self.step_duration = step_duration
        self.location = location
        self.total_duration = total_duration
        self.iclamp = None

    def instantiate(self, cell):
        """Run stimulus"""

        icomp = self.location.instantiate(cell)
        logger.debug(
            'Adding square step stimulus to %s with delay %f, '
            'duration %f, and amplitude %f',
            str(self.location),
            self.step_delay,
            self.step_duration,
            self.step_amplitude)

        self.iclamp = neuron.h.IClamp(
            icomp.x,
            sec=icomp.sec)
        self.iclamp.dur = self.step_duration
        self.iclamp.amp = self.step_amplitude
        self.iclamp.delay = self.step_delay

    def destroy(self):
        """Destroy stimulus"""

        self.iclamp = None

    def __str__(self):
        """String representation"""

        return "Square pulse amp %f delay %f duration %f totdur %f at %s" % (
            self.
            step_amplitude,
            self.
            step_delay,
            self.
            step_duration,
            self.
            total_duration,
            self.
            location)
