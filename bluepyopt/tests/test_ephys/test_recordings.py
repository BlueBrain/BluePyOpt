"""bluepyopt.ephys.simulators tests"""

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

# pylint:disable=W0612


import pytest

import bluepyopt.ephys as ephys


@pytest.mark.unit
def test_comprecording_init():
    """ephys.recordings: Test CompRecording init"""

    recording = ephys.recordings.CompRecording()

    assert isinstance(recording, ephys.recordings.CompRecording)

    assert recording.response is None

    '''
    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma_loc',
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)

    rec_soma = ephys.recordings.CompRecording(
        name='soma.v',
        location=soma_loc,
        variable='v')

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.0,
        step_delay=0.0,
        step_duration=50,
        total_duration=50,
        location=soma_loc)

    protocol = ephys.protocols.SweepProtocol(
        name='prot',
        stimuli=[stim],
        recordings=[rec_soma])

    assert_true(isinstance(protocol, ephys.protocols.SweepProtocol))
    assert_equal(protocol.total_duration, 50)
    assert_equal(
        protocol.subprotocols(), {'prot': protocol})

    assert_true('somatic[0](0.5)' in str(protocol))

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)
    '''
