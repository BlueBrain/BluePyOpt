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

import types
import nose.tools as nt
from nose.plugins.attrib import attr

import mock

import bluepyopt.ephys as ephys


@attr('unit')
def test_nrnsimulator_init():
    """ephys.simulators: test if NrnSimulator constructor works"""

    neuron_sim = ephys.simulators.NrnSimulator()
    nt.assert_is_instance(neuron_sim, ephys.simulators.NrnSimulator)


@attr('unit')
def test_nrnsimulator_init_windows():
    """ephys.simulators: test if NrnSimulator constructor works on Windows"""

    with mock.patch('platform.system', mock.MagicMock(return_value="Windows")):
        neuron_sim = ephys.simulators.NrnSimulator()
        nt.assert_is_instance(neuron_sim, ephys.simulators.NrnSimulator)
        nt.assert_false(neuron_sim.disable_banner)
        nt.assert_false(neuron_sim.banner_disabled)

        neuron_sim.neuron.h.celsius = 34

        nt.assert_false(neuron_sim.disable_banner)
        nt.assert_false(neuron_sim.banner_disabled)


@attr('unit')
def test_nrnsimulator_cvode_minstep():
    """ephys.simulators: test if NrnSimulator constructor works"""

    # Check with minstep specified
    neuron_sim = ephys.simulators.NrnSimulator()
    nt.assert_equal(neuron_sim.cvode.minstep(), 0.0)
    nt.assert_equal(neuron_sim.cvode_minstep, 0.0)

    # Check with minstep specified, before after simulation
    neuron_sim = ephys.simulators.NrnSimulator(cvode_minstep=0.01)
    nt.assert_equal(neuron_sim.cvode.minstep(), 0.01)
    neuron_sim.run(tstop=10)
    nt.assert_equal(neuron_sim.cvode.minstep(), 0.01)

    # Check with minstep specified, before after simulation
    neuron_sim = ephys.simulators.NrnSimulator(cvode_minstep=0.0)
    nt.assert_equal(neuron_sim.cvode.minstep(), 0.0)
    neuron_sim.cvode_minstep = 0.02
    neuron_sim.run(tstop=10)
    nt.assert_equal(neuron_sim.cvode.minstep(), 0.02)


@attr('unit')
def test_neuron_import():
    """ephys.simulators: test if bluepyopt.neuron import was successful"""
    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    nt.assert_is_instance(neuron_sim.neuron, types.ModuleType)


@attr('unit')
def test_nrnsim_run_dt_exception():
    """ephys.simulators: test if run return exception when dt was changed"""

    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    neuron_sim.neuron.h.dt = 1.0
    nt.assert_raises(Exception, neuron_sim.run, 10, cvode_active=False)


@attr('unit')
def test_nrnsim_run_cvodeactive_dt_exception():
    """ephys.simulators: test if run return exception cvode and dt both used"""

    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    neuron_sim.neuron.h.dt = 1.0
    nt.assert_raises(ValueError, neuron_sim.run, 10, dt=0.1, cvode_active=True)


@attr('unit')
@mock.patch('glob.glob')
def test_disable_banner_exception(mock_glob):
    """ephys.simulators: test if disable_banner raises exception"""
    mock_glob.return_value = []

    import warnings
    with warnings.catch_warnings(record=True) as warnings_record:
        ephys.simulators.NrnSimulator._nrn_disable_banner()
        nt.assert_equal(len(warnings_record), 1)
