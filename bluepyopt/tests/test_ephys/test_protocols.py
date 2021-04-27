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


import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys
import testmodels.dummycells


@attr("unit")
def test_distloc_exception():
    """ephys.protocols: test if protocol raise dist loc exception"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    dend_loc = ephys.locations.NrnSomaDistanceCompLocation(
        name="dend_loc", soma_distance=800, seclist_name="apical"
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )
    rec_dend = ephys.recordings.CompRecording(
        name="dend.v", location=dend_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    protocol = ephys.protocols.SweepProtocol(
        name="prot", stimuli=[stim], recordings=[rec_soma, rec_dend]
    )

    responses = protocol.run(
        cell_model=dummy_cell, param_values={}, sim=nrn_sim
    )

    nt.assert_not_equal(responses["soma.v"], None)
    nt.assert_equal(responses["dend.v"], None)

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


def run_RuntimeError(
    self, tstop=None, dt=None, cvode_active=None, random123_globalindex=None
):
    """Mock version of run that throws runtimeerror"""
    raise RuntimeError()


def run_NrnSimulatorException(
    self, tstop=None, dt=None, cvode_active=None, random123_globalindex=None
):
    """Mock version of run that throws runtimeerror"""
    raise ephys.simulators.NrnSimulatorException("mock", None)


@attr("unit")
def test_sweepprotocol_init():
    """ephys.protocols: Test SweepProtocol init"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    protocol = ephys.protocols.SweepProtocol(
        name="prot", stimuli=[stim], recordings=[rec_soma]
    )

    nt.assert_true(isinstance(protocol, ephys.protocols.SweepProtocol))
    nt.assert_equal(protocol.total_duration, 50)
    nt.assert_equal(protocol.subprotocols(), {"prot": protocol})

    nt.assert_true("somatic[0](0.5)" in str(protocol))

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr("unit")
def test_sequenceprotocol_init():
    """ephys.protocols: Test SequenceProtocol init"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    sweep_protocol = ephys.protocols.SweepProtocol(
        name="sweep_prot", stimuli=[stim], recordings=[rec_soma]
    )

    seq_protocol = ephys.protocols.SequenceProtocol(
        name="seq_prot", protocols=[sweep_protocol]
    )

    nt.assert_true(isinstance(seq_protocol, ephys.protocols.SequenceProtocol))
    nt.assert_equal(
        seq_protocol.subprotocols(),
        {"seq_prot": seq_protocol, "sweep_prot": sweep_protocol},
    )

    sweep_protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr("unit")
def test_sequenceprotocol_run():
    """ephys.protocols: Test SequenceProtocol run"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    sweep_protocol = ephys.protocols.SweepProtocol(
        name="sweep_prot", stimuli=[stim], recordings=[rec_soma]
    )

    seq_protocol = ephys.protocols.SequenceProtocol(
        name="seq_prot", protocols=[sweep_protocol]
    )

    responses = seq_protocol.run(
        cell_model=dummy_cell, param_values={}, sim=nrn_sim
    )

    nt.assert_true(responses is not None)

    sweep_protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr("unit")
def test_sequenceprotocol_overwrite():
    """ephys.protocols: Test SequenceProtocol overwriting keys"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()

    sweep_protocols = []
    for x in [0.2, 0.5]:
        soma_loc = ephys.locations.NrnSeclistCompLocation(
            name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=x
        )

        rec_soma = ephys.recordings.CompRecording(
            name="soma.v", location=soma_loc, variable="v"
        )

        stim = ephys.stimuli.NrnSquarePulse(
            step_amplitude=0.0,
            step_delay=0.0,
            step_duration=50,
            total_duration=50,
            location=soma_loc,
        )

        sweep_protocols.append(
            ephys.protocols.SweepProtocol(
                name="sweep_prot", stimuli=[stim], recordings=[rec_soma]
            )
        )

    seq_protocol = ephys.protocols.SequenceProtocol(
        name="seq_prot", protocols=sweep_protocols
    )

    nt.assert_raises(
        Exception,
        seq_protocol.run,
        cell_model=dummy_cell,
        param_values={},
        sim=nrn_sim,
    )

    for sweep_protocol in sweep_protocols:
        sweep_protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr("unit")
def test_stepprotocol_init():
    """ephys.protocols: Test StepProtocol init"""

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=5.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )
    hold_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    step_protocol = ephys.protocols.StepProtocol(
        name="step_prot",
        step_stimulus=stim,
        holding_stimulus=hold_stim,
        recordings=[rec_soma],
    )

    nt.assert_equal(step_protocol.step_delay, 5.0)
    nt.assert_equal(step_protocol.step_duration, 50)


@attr("unit")
def test_sweepprotocol_run_unisolated():
    """ephys.protocols: Test SweepProtocol unisolated run"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    unknown_loc = ephys.locations.NrnSomaDistanceCompLocation(
        name="unknown_loc", seclist_name="somatic", soma_distance=100
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )
    rec_unknown = ephys.recordings.CompRecording(
        name="unknown.v", location=unknown_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    protocol = ephys.protocols.SweepProtocol(
        name="prot", stimuli=[stim], recordings=[rec_soma, rec_unknown]
    )

    responses = protocol.run(
        cell_model=dummy_cell, param_values={}, sim=nrn_sim, isolate=False
    )

    nt.assert_true("soma.v" in responses)
    nt.assert_true("unknown.v" in responses)
    nt.assert_equal(responses["unknown.v"], None)

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)


@attr("unit")
def test_nrnsimulator_exception():
    """ephys.protocols: test if protocol raise nrn sim exception"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma_loc", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    rec_soma = ephys.recordings.CompRecording(
        name="soma.v", location=soma_loc, variable="v"
    )

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc,
    )

    protocol = ephys.protocols.SweepProtocol(
        name="prot", stimuli=[stim], recordings=[rec_soma]
    )

    nrn_sim.run = run_RuntimeError

    responses = protocol.run(
        cell_model=dummy_cell, param_values={}, sim=nrn_sim, isolate=False
    )

    nt.assert_equal(responses["soma.v"], None)

    nrn_sim.run = run_NrnSimulatorException

    responses = protocol.run(
        cell_model=dummy_cell, param_values={}, sim=nrn_sim, isolate=False
    )

    nt.assert_equal(responses["soma.v"], None)

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)
