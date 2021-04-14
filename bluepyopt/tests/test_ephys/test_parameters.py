"""ephys.parameters tests"""

import json


import pytest
import numpy

from . import utils
from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator

import bluepyopt.ephys.examples.simplecell


@pytest.mark.unit
def test_pprocessparam_instantiate():
    """ephys.parameters: Testing point process parameter"""

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    simple_cell = simplecell.cell_model
    simple_cell.freeze(simplecell.default_param_values)
    sim = simplecell.nrn_sim

    expsyn_mech = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[simplecell.somacenter_loc])

    expsyn_loc = ephys.locations.NrnPointProcessLocation(
        'expsyn_loc',
        pprocess_mech=expsyn_mech)

    expsyn_tau_param = ephys.parameters.NrnPointProcessParameter(
        name='expsyn_tau',
        param_name='tau',
        value=2,
        locations=[expsyn_loc])

    simple_cell.mechanisms.append(expsyn_mech)
    simple_cell.params[expsyn_tau_param.name] = expsyn_tau_param
    simple_cell.instantiate(sim=sim)

    assert expsyn_mech.pprocesses[0].tau == 2

    simple_cell.destroy(sim=sim)


@pytest.mark.unit
def test_serialize():
    """ephys.parameters: Test serialize"""
    parameters = utils.make_parameters()

    for param in parameters:
        serialized = param.to_dict()
        assert isinstance(json.dumps(serialized), str)
        deserialized = instantiator(serialized)
        assert isinstance(deserialized, param.__class__)
        assert deserialized.name == param.__class__.__name__


@pytest.mark.unit
def test_metaparameter():
    """ephys.parameters: Test MetaParameter"""

    dist = "({A} + {B} * math.exp({distance} * {C}) * {value}"

    scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        distribution=dist, dist_param_names=['A', 'B', 'C'])

    scaler.A = -0.9
    scaler.B = 2
    scaler.C = 0.003

    meta_param = ephys.parameters.MetaParameter('Param A', scaler, 'A', -1)

    assert meta_param.attr_name == 'A'
    assert meta_param.value == -1
    assert scaler.A == -1
