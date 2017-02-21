"""bluepyopt.ephys.simulators tests"""

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

# pylint:disable=W0612

import numpy

import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys
import testmodels.dummycells


@attr('unit')
def test_stimulus_init():
    """ephys.stimuli: test if Stimulus constructor works"""

    stim = ephys.stimuli.Stimulus()
    nt.assert_is_instance(stim, ephys.stimuli.Stimulus)


@attr('unit')
def test_NrnNetStimStimulus_init():
    """ephys.stimuli: test if NrnNetStimStimulus constructor works"""

    nt.assert_raises(ValueError, ephys.stimuli.NrnNetStimStimulus)

    stim = ephys.stimuli.NrnNetStimStimulus(total_duration=100)
    nt.assert_is_instance(stim, ephys.stimuli.NrnNetStimStimulus)

    nt.assert_equal(str(stim), 'Netstim')


@attr('unit')
def test_NrnNetStimStimulus_instantiate():
    """ephys.stimuli: test if NrnNetStimStimulus instantiate works"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    icell = dummy_cell.instantiate(sim=nrn_sim)

    somacenter_loc = ephys.locations.NrnSeclistCompLocation(
        name=None,
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)

    expsyn_mech = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[somacenter_loc])

    expsyn_mech.instantiate(sim=nrn_sim, icell=icell)

    expsyn_loc = ephys.locations.NrnPointProcessLocation(
        'expsyn_loc',
        pprocess_mech=expsyn_mech)

    netstim = ephys.stimuli.NrnNetStimStimulus(
        total_duration=200,
        number=5,
        interval=5,
        start=20,
        weight=5e-4,
        locations=[expsyn_loc])

    netstim.instantiate(sim=nrn_sim, icell=icell)

    nrn_sim.run(netstim.total_duration)

    expsyn_mech.destroy(sim=nrn_sim)
    netstim.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr('unit')
def test_NrnCurrentPlayStimulus_instantiate():
    """ephys.stimuli: test if NrnNetStimStimulus instantiate works"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    icell = dummy_cell.instantiate(sim=nrn_sim)

    somacenter_loc = ephys.locations.NrnSeclistCompLocation(
        name=None,
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)

    time_points = [10, 50]
    current_points = [0.1, 0.2]
    current_stim = ephys.stimuli.NrnCurrentPlayStimulus(
        time_points=time_points,
        current_points=current_points,
        location=somacenter_loc)

    nt.assert_equal(current_stim.time_points, time_points)
    nt.assert_equal(current_stim.current_points, current_points)
    nt.assert_equal(str(current_stim), 'Current play at somatic[0](0.5)')
    current_stim.instantiate(sim=nrn_sim, icell=icell)

    nrn_sim.run(100)

    current_stim.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr('unit')
def test_NrnRampPulse_init():
    """ephys.stimuli: test if NrnRampPulse constructor works"""
    stim = ephys.stimuli.NrnRampPulse()
    nt.assert_is_instance(stim, ephys.stimuli.NrnRampPulse)


@attr('unit')
def test_NrnRampPulse_instantiate():
    """ephys.stimuli: test if NrnRampPulse injects correct current"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name=None,
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)
    recording = ephys.recordings.CompRecording(
        location=soma_loc,
        variable='v')

    ramp_amplitude_start = 0.1
    ramp_amplitude_end = 1.0
    ramp_delay = 20.0
    ramp_duration = 20.0
    total_duration = 50.0

    stim = ephys.stimuli.NrnRampPulse(
        ramp_amplitude_start=ramp_amplitude_start,
        ramp_amplitude_end=ramp_amplitude_end,
        ramp_delay=ramp_delay,
        ramp_duration=ramp_duration,
        total_duration=total_duration,
        location=soma_loc)

    nt.assert_equal(
        str(stim),
        'Ramp pulse amp_start 0.100000 amp_end 1.000000 '
        'delay 20.000000 duration 20.000000 totdur 50.000000'
        ' at somatic[0](0.5)')
    stim.instantiate(sim=nrn_sim, icell=icell)

    recording.instantiate(sim=nrn_sim, icell=icell)

    stim_i_vec = nrn_sim.neuron.h.Vector()
    stim_i_vec.record(stim.iclamp._ref_i)  # pylint: disable=W0212
    nrn_sim.run(stim.total_duration)

    current = numpy.array(stim_i_vec.to_python())
    time = numpy.array(recording.response['time'])
    voltage = numpy.array(recording.response['voltage'])

    # make sure current is 0 before stimulus
    nt.assert_equal(numpy.max(
        current[numpy.where((0 <= time) & (time < ramp_delay))]), 0)

    # make sure voltage stays at v_init before stimulus
    nt.assert_equal(numpy.max(
        voltage[
            numpy.where((0 <= time)
                        & (time < ramp_delay))]), nrn_sim.neuron.h.v_init)

    # make sure current is at right amp at end of stimulus
    nt.assert_equal(
        current[numpy.where(time == ramp_delay)][-1],
        ramp_amplitude_start)
    # make sure current is at right amp at end of stimulus
    nt.assert_equal(
        current[numpy.where(time == (ramp_delay + ramp_duration))][0],
        ramp_amplitude_end)

    # make sure current is 0 after stimulus
    nt.assert_equal(numpy.max(
        current[
            numpy.where(
                (ramp_delay + ramp_duration < time)
                & (time <= total_duration))]), 0)

    # make sure voltage is correct after stimulus
    nt.assert_almost_equal(numpy.mean(
        voltage[
            numpy.where(
                (ramp_delay + ramp_duration < time)
                & (time <= total_duration))]), -57.994437612124869)
    recording.destroy(sim=nrn_sim)
    stim.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)
