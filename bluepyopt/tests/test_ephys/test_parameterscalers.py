"""Test ephys.parameterscalers"""

import json


import pytest


from bluepyopt.ephys.parameterscalers import (NrnSegmentLinearScaler,
                                              NrnSegmentSomaDistanceScaler, )
from bluepyopt.ephys.serializer import instantiator

import bluepyopt.ephys as ephys


@pytest.mark.unit
def test_NrnSegmentSomaDistanceScaler_dist_params():
    """ephys.parameterscalers: dist_params of NrnSegmentSomaDistanceScaler"""

    dist = "({A} + {B} * math.exp({distance} * {C}) * {value}"

    scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        distribution=dist, dist_param_names=['A', 'B', 'C'])

    assert hasattr(scaler, 'A')
    assert hasattr(scaler, 'B')
    assert hasattr(scaler, 'C')
    scaler.A = -0.9
    assert scaler.A == -0.9
    scaler.B = 2
    assert scaler.B == 2
    scaler.C = 0.003
    assert scaler.C == 0.003

    assert (scaler.eval_dist(1.0, 1.0)
            == '(-0.9 + 2 * math.exp(1 * 0.003) * 1')


@pytest.mark.unit
def test_serialize():
    """ephys.parameterscalers: test serialization"""

    multiplier, offset, distribution = 12.12, 3.58, '1 + {distance}'
    paramscalers = (
        NrnSegmentLinearScaler(
            'NrnSegmentLinearScaler',
            multiplier,
            offset),
        NrnSegmentSomaDistanceScaler(
            'NrnSegmentSomaDistanceScaler',
            distribution),
    )

    for ps in paramscalers:
        serialized = ps.to_dict()
        assert isinstance(json.dumps(serialized), str)
        deserialized = instantiator(serialized)
        assert isinstance(deserialized, ps.__class__)
        assert deserialized.name == ps.__class__.__name__
