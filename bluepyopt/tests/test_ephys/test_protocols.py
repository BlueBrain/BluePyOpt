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


@attr('unit')
def test_distloc_exception():
    """ephys.protocols: test if protocol raise dist loc exception"""

    nrn_sim = ephys.simulators.NrnSimulator()
    dummy_cell = testmodels.dummycells.DummyCellModel1()
    # icell = dummy_cell.instantiate(sim=nrn_sim)
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma_loc',
        seclist_name='somatic',
        sec_index=0,
        comp_x=.5)
    dend_loc = ephys.locations.NrnSomaDistanceCompLocation(
        name='dend_loc',
        soma_distance=800,
        seclist_name='apical')

    rec_soma = ephys.recordings.CompRecording(
        name='soma.v',
        location=soma_loc,
        variable='v')
    rec_dend = ephys.recordings.CompRecording(
        name='dend.v',
        location=dend_loc,
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
        recordings=[
            rec_soma,
            rec_dend])

    responses = protocol.run(
        cell_model=dummy_cell,
        param_values={},
        sim=nrn_sim)

    nt.assert_not_equal(responses['soma.v'], None)
    nt.assert_equal(responses['dend.v'], None)

    protocol.destroy(sim=nrn_sim)
    dummy_cell.destroy(sim=nrn_sim)
