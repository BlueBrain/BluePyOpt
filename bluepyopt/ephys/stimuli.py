"""Stimuli classes"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

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

import numpy as np
import logging

from bluepyopt.ephys.acc import arbor

logger = logging.getLogger(__name__)


class Stimulus(object):

    """Stimulus protocol"""
    pass


class SynapticStimulus(Stimulus):

    """Synaptic stimulus protocol"""
    pass


class LFPStimulus(Stimulus):

    """Base class for stimulus supporting LFPy cells."""

    def instantiate(self, sim=None, lfpy_cell=None):
        """Run stimulus"""
        raise NotImplementedError


class NrnCurrentPlayStimulus(Stimulus):

    """Current stimulus based on current amplitude and time series"""

    def __init__(self,
                 time_points=None,
                 current_points=None,
                 location=None):
        """Constructor

        Args:
            time_points(): time series (ms)
            current_points(): current series of injected current amplitudes(nA)
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

    def envelope(self):
        """Stimulus envelope"""

        envelope = list(zip(self.time_points, self.current_points))

        return envelope

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

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

    def destroy(self, sim=None):
        """Destroy stimulus"""

        self.iclamp = None
        self.time_vec = None
        self.current_vec = None

    def __str__(self):
        """String representation"""

        return "Current play at %s" % (self.location)


class NrnNetStimStimulus(SynapticStimulus):

    """Current stimulus based on current amplitude and time series"""

    def __init__(self,
                 locations=None,
                 total_duration=None,
                 interval=None,
                 number=None,
                 start=None,
                 noise=0,
                 weight=1):
        """Constructor

        Args:
            location: synapse point process location to connect to
            interval: time between spikes (ms)
            number: average number of spikes
            start: most likely start time of first spike (ms)
            noise: fractional randomness (0 deterministic,
                   1 negexp interval distribution)
        """

        super(NrnNetStimStimulus, self).__init__()
        if total_duration is None:
            raise ValueError(
                'NrnNetStimStimulus: Need to specify a total duration')
        else:
            self.total_duration = total_duration

        self.locations = locations
        self.interval = interval
        self.number = number
        self.start = start
        self.noise = noise
        self.weight = weight
        self.connections = {}

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

        for location in self.locations:
            self.connections[location.name] = []
            for synapse in location.instantiate(sim=sim, icell=icell):
                netstim = sim.neuron.h.NetStim()
                netstim.interval = self.interval
                netstim.number = self.number
                netstim.start = self.start
                netstim.noise = self.noise
                netcon = sim.neuron.h.NetCon(netstim, synapse)
                netcon.weight[0] = self.weight

                self.connections[location.name].append((netcon, netstim))

    def destroy(self, sim=None):
        """Destroy stimulus"""

        self.connections = {}

    def acc_events(self):
        event_generators = []

        for loc in self.locations:
            if self.noise == 0.:
                schedule = arbor.explicit_schedule(
                    [self.start + i * self.interval
                     for i in range(self.number)])
            elif self.noise == 1.:
                schedule = arbor.poisson_schedule(
                    tstart=self.start,
                    freq=1. / self.interval,
                    seed=0,
                    tstop=self.start + self.number * self.interval)
            else:
                raise ValueError(
                    'Only noise = 0 or 1 for NrnNetStimStimulus'
                    ' supported in Arbor.')

            event_generators.append(
                arbor.event_generator(target=loc.pprocess_mech.name,
                                      weight=self.weight,
                                      sched=schedule))

        return event_generators

    def __str__(self):
        """String representation"""

        return "Netstim at %s" % ','.join(
            location
            for location in self.locations) \
            if self.locations is not None else "Netstim"

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

    def envelope(self):
        """Stimulus envelope"""

        envelope = [(0., 0.),
                    (self.step_delay, 0.),
                    (self.step_delay, self.step_amplitude),
                    (self.step_delay + self.step_duration,
                        self.step_amplitude),
                    (self.step_delay + self.step_duration, 0.),
                    (self.total_duration, 0.)]

        return envelope

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

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

    def destroy(self, sim=None):
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


class NrnRampPulse(Stimulus):

    """Ramp current clamp injection"""

    def __init__(self,
                 ramp_amplitude_start=None,
                 ramp_amplitude_end=None,
                 ramp_delay=None,
                 ramp_duration=None,
                 total_duration=None,
                 location=None):
        """Constructor

        Args:
            ramp_amplitude_start (float): amplitude at start of ramp (nA)
            ramp_amplitude_start (float): amplitude at end of ramp (nA)
            ramp_delay (float): delay of ramp (ms)
            ramp_duration (float): duration oframp (ms)
            total_duration (float): total duration (ms)
            location (Location): stimulus Location
        """

        super(NrnRampPulse, self).__init__()
        self.ramp_amplitude_start = ramp_amplitude_start
        self.ramp_amplitude_end = ramp_amplitude_end
        self.ramp_delay = ramp_delay
        self.ramp_duration = ramp_duration
        self.location = location
        self.total_duration = total_duration
        self.iclamp = None
        self.persistent = []  # TODO move this into higher abstract classes

    def envelope(self):
        """Stimulus envelope"""

        envelope = [
            # at time 0.0, current is 0.0
            (0.0, 0.0),

            # until time ramp_delay, current is 0.0
            (self.ramp_delay, 0.0),

            # at time ramp_delay, current is ramp_amplitude_start
            (self.ramp_delay, self.ramp_amplitude_start),

            # at time ramp_delay+ramp_duration, current is ramp_amplitude_end
            (self.ramp_delay + self.ramp_duration,
             self.ramp_amplitude_end),

            # after ramp, current is set 0.0
            (self.ramp_delay + self.ramp_duration, 0.0),

            (self.total_duration, 0.0)
        ]

        return envelope

    def instantiate(self, sim=None, icell=None):
        """Run stimulus"""

        icomp = self.location.instantiate(sim=sim, icell=icell)
        logger.debug(
            'Adding ramp stimulus to %s with delay %f, '
            'duration %f, amplitude at start %f and end %f',
            str(self.location),
            self.ramp_delay,
            self.ramp_duration,
            self.ramp_amplitude_start,
            self.ramp_amplitude_end
        )

        times, amps = zip(*self.envelope())

        # create vector to store the times at which stim amp changes
        times = sim.neuron.h.Vector(times)
        # create vector to store to which stim amps over time
        amps = sim.neuron.h.Vector(amps)

        # create a current clamp
        self.iclamp = sim.neuron.h.IClamp(
            icomp.x,
            sec=icomp.sec)
        self.iclamp.dur = self.total_duration

        # play the above current amplitudes into the current clamp
        amps.play(self.iclamp._ref_amp, times, 1)  # pylint: disable=W0212

        # Make sure the following objects survive after instantiation
        self.persistent.append(times)
        self.persistent.append(amps)

    def destroy(self, sim=None):
        """Destroy stimulus"""

        # Destroy all persistent objects
        self.persistent = []
        self.iclamp = None

    def __str__(self):
        """String representation"""

        return "Ramp pulse amp_start %f amp_end %f delay %f duration %f " \
            "totdur %f at %s" % (
                self.ramp_amplitude_start,
                self.ramp_amplitude_end,
                self.ramp_delay,
                self.ramp_duration,
                self.total_duration,
                self.location)


class LFPySquarePulse(LFPStimulus):

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

        super(LFPySquarePulse, self).__init__()
        self.step_amplitude = step_amplitude
        self.step_delay = step_delay
        self.step_duration = step_duration
        self.location = location
        self.total_duration = total_duration
        self.iclamp = None

    def instantiate(self, sim=None, lfpy_cell=None):
        """Run stimulus"""
        import LFPy
        from .locations import NrnSomaDistanceCompLocation

        if hasattr(self.location, "sec_index"):
            sec_index = self.location.sec_index
        elif isinstance(self.location, NrnSomaDistanceCompLocation):
            # compute sec_index closest to soma_distance
            cell_seg_locs = np.array([lfpy_cell.x, lfpy_cell.y, lfpy_cell.z]).T
            soma_loc = lfpy_cell.somapos
            dist_from_soma = np.array(
                [np.linalg.norm(loc - soma_loc) for loc in cell_seg_locs]
            )
            sec_index = np.argmin(
                np.abs(dist_from_soma - self.location.soma_distance)
            )
        else:
            raise NotImplementedError(
                f"{type(self.location)} is currently not implemented "
                "with the LFPy backend"
            )

        self.iclamp = LFPy.StimIntElectrode(
            cell=lfpy_cell,
            idx=sec_index,
            pptype="IClamp",
            amp=self.step_amplitude,
            delay=self.step_delay,
            dur=self.step_duration,
            record_current=True
        )
        logger.debug(
            "Adding square step stimulus to %s with delay %f, "
            "duration %f, and amplitude %f",
            str(self.location),
            self.step_delay,
            self.step_duration,
            self.step_amplitude,
        )

    def destroy(self, sim=None):
        """Destroy stimulus"""

        self.iclamp = None

    def __str__(self):
        """String representation"""

        return "Square pulse amp %f delay %f duration %f totdur %f at %s" % (
            self.step_amplitude,
            self.step_delay,
            self.step_duration,
            self.total_duration,
            self.location,
        )
