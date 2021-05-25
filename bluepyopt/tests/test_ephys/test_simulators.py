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

import types

import pytest
import numpy

import mock
import numpy

import bluepyopt.ephys as ephys
import bluepyopt.ephys.examples as examples


@pytest.mark.unit
def test_nrnsimulator_init():
    """ephys.simulators: test if NrnSimulator constructor works"""

    neuron_sim = ephys.simulators.NrnSimulator()
    assert isinstance(neuron_sim, ephys.simulators.NrnSimulator)


@pytest.mark.unit
def test_nrnsimulator_init_windows():
    """ephys.simulators: test if NrnSimulator constructor works on Windows"""

    with mock.patch('platform.system', mock.MagicMock(return_value="Windows")):
        neuron_sim = ephys.simulators.NrnSimulator()
        assert isinstance(neuron_sim, ephys.simulators.NrnSimulator)
        assert not neuron_sim.disable_banner
        assert not neuron_sim.banner_disabled

        neuron_sim.neuron.h.celsius = 34

        assert not neuron_sim.disable_banner
        assert not neuron_sim.banner_disabled


@pytest.mark.unit
def test_nrnsimulator_cvode_minstep():
    """ephys.simulators: test if NrnSimulator constructor works"""

    # Check with minstep specified
    neuron_sim = ephys.simulators.NrnSimulator()
    assert neuron_sim.cvode.minstep() == 0.0
    assert neuron_sim.cvode_minstep == 0.0

    # Check default minstep before and after run
    neuron_sim = ephys.simulators.NrnSimulator(cvode_minstep=0.01)
    assert neuron_sim.cvode.minstep() == 0.
    neuron_sim.run(tstop=10)
    assert neuron_sim.cvode.minstep() == 0.

    # Check with that minstep is set back to the original value after run
    neuron_sim = ephys.simulators.NrnSimulator(cvode_minstep=0.0)
    neuron_sim.cvode_minstep = 0.05
    assert neuron_sim.cvode.minstep() == 0.05
    neuron_sim.run(tstop=10)
    assert neuron_sim.cvode.minstep() == 0.05

    # Check that the minstep is effective
    cvode_minstep = 0.012
    params = {'gnabar_hh': 0.10299326453483033,
              'gkbar_hh': 0.027124836082684685}
    simplecell = examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator
    evaluator.cell_model.unfreeze(params.keys())
    evaluator.sim = ephys.simulators.NrnSimulator(cvode_minstep=cvode_minstep)
    responses = evaluator.run_protocols(
        protocols=evaluator.fitness_protocols.values(),
        param_values=params)
    ton = list(evaluator.fitness_protocols.values())[0].stimuli[0].step_delay
    toff = ton + list(evaluator.fitness_protocols.values())[0].stimuli[
        0].step_duration
    t_series = numpy.array(responses['Step1.soma.v']['time'])
    t_series = t_series[((ton + 1.) < t_series) & (t_series < (toff - 1.))]
    min_dt = numpy.min(numpy.ediff1d(t_series))
    assert (min_dt >= cvode_minstep) == 1
    evaluator.cell_model.freeze(params)


@pytest.mark.unit
def test_neuron_import():
    """ephys.simulators: test if bluepyopt.neuron import was successful"""
    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    assert isinstance(neuron_sim.neuron, types.ModuleType)


@pytest.mark.unit
def test_nrnsim_run_dt_exception():
    """ephys.simulators: test if run return exception when dt was changed"""

    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    neuron_sim.neuron.h.dt = 1.0
    pytest.raises(Exception, neuron_sim.run, 10, cvode_active=False)


@pytest.mark.unit
def test_nrnsim_run_cvodeactive_dt_exception():
    """ephys.simulators: test if run return exception cvode and dt both used"""

    from bluepyopt import ephys  # NOQA
    neuron_sim = ephys.simulators.NrnSimulator()
    neuron_sim.neuron.h.dt = 1.0
    pytest.raises(ValueError, neuron_sim.run, 10, dt=0.1, cvode_active=True)


@pytest.mark.unit
@mock.patch('glob.glob')
def test_disable_banner_exception(mock_glob):
    """ephys.simulators: test if disable_banner raises exception"""
    mock_glob.return_value = []

    import warnings
    with warnings.catch_warnings(record=True) as warnings_record:
        ephys.simulators.NrnSimulator._nrn_disable_banner()
        assert len(warnings_record) == 1
