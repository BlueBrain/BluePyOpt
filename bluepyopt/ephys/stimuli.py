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
logger = logging.getLogger(__name__)


class Stimulus(object):

    """Stimulus protocol"""
    pass


class NrnCurrentPlayStimulus(Stimulus):

    """Current stimulus based on current amplitude and time series"""

    def __init__(self,
                 time_points=None,
                 current_points=None,
                 location=None):
        """Constructor

        Args:
            time_points(): time series (ms)
            current_points(): current series of injected current amplitudes (nA)
            location(Location): location of stimulus
        """

        super(NrnCurrentPlayStimulus, self).__init__()
        self.time_points = time_points
        self.current_points = current_points
        self.location = location
        self.total_duration = max(time_points)
        self.iclamp = None
        self.current_vec = None
        self.time_vec = None

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

        icell = icell
        icomp = self.location.instantiate(sim=sim, icell=icell)
        logger.debug(
            'Adding current play stimulus to %s', str(self.location))

        self.iclamp = sim.neuron.h.IClamp(
            icomp.x,
            sec=icomp.sec)
        self.current_vec = sim.neuron.h.Vector(self.current_points)
        self.time_vec = sim.neuron.h.Vector(self.time_points)
        self.iclamp.dur = self.total_duration
        self.iclamp.delay = 0
        self.current_vec.play(
            self.iclamp._ref_amp,  # pylint:disable=W0212
            self.time_vec,
            1,
            sec=icomp.sec)

    def destroy(self):
        """Destroy stimulus"""

        self.iclamp = None
        self.time_vec = None
        self.current_vec = None

    def __str__(self):
        """String representation"""

        return "Current play at %s" % (self.location)

# TODO Add 'current' to the name


class NrnSquarePulse(Stimulus):

    """Square pulse current clamp injection"""

    def __init__(self,
                 step_amplitude=None,
                 step_delay=None,
                 step_duration=None,
                 total_duration=None,
                 location=None):
        """Constructor

        Args:
            step_amplitude (float): amplitude (nA)
            step_delay (float): delay (ms)
            step_duration (float): duration (ms)
            total_duration (float): total duration (ms)
            location (Location): stimulus Location
        """

        super(NrnSquarePulse, self).__init__()
        self.step_amplitude = step_amplitude
        self.step_delay = step_delay
        self.step_duration = step_duration
        self.location = location
        self.total_duration = total_duration
        self.iclamp = None

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

        icell = icell
        icomp = self.location.instantiate(sim=sim, icell=icell)
        logger.debug(
            'Adding square step stimulus to %s with delay %f, '
            'duration %f, and amplitude %f',
            str(self.location),
            self.step_delay,
            self.step_duration,
            self.step_amplitude)

        self.iclamp = sim.neuron.h.IClamp(
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
            self.step_amplitude,
            self.step_delay,
            self.step_duration,
            self.total_duration,
            self.location)
