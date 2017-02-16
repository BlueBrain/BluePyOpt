"""Test ephys.parameterscalers"""

import json

import nose.tools as nt
from nose.plugins.attrib import attr


from bluepyopt.ephys.parameterscalers import (NrnSegmentLinearScaler,
                                              NrnSegmentSomaDistanceScaler, )
from bluepyopt.ephys.serializer import instantiator

import bluepyopt.ephys as ephys


@attr('unit')
def test_NrnSegmentSomaDistanceScaler_dist_params():
    """ephys.parameterscalers: dist_params of NrnSegmentSomaDistanceScaler"""

    dist = "({A} + {B} * math.exp({distance} * {C}) * {value}"

    scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        distribution=dist, dist_param_names=['A', 'B', 'C'])

    nt.assert_true(hasattr(scaler, 'A'))
    nt.assert_true(hasattr(scaler, 'B'))
    nt.assert_true(hasattr(scaler, 'C'))
    scaler.A = -0.9
    nt.assert_equal(scaler.A, -0.9)
    scaler.B = 2
    nt.assert_equal(scaler.B, 2)
    scaler.C = 0.003
    nt.assert_equal(scaler.C, 0.003)

    nt.assert_equal(scaler.eval_dist(1.0, 1.0),
                    '(-0.9 + 2 * math.exp(1 * 0.003) * 1')


@attr('unit')
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
        nt.ok_(isinstance(json.dumps(serialized), str))
        deserialized = instantiator(serialized)
        nt.ok_(isinstance(deserialized, ps.__class__))
        nt.eq_(deserialized.name, ps.__class__.__name__)
