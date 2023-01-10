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
def test_NrnSegmentSectionDistanceScaler_eval_dist_with_dict():
    """ephys.parameterscalers: eval_dist of NrnSegmentSectionDistanceScaler"""

    dist = '{param1_somatic} + (1 - (abs({distance} - 8) / 4)) * {value}'

    scaler = ephys.parameterscalers.NrnSegmentSectionDistanceScaler(
        distribution=dist)

    _values = {'value': 1, 'param1_somatic': 0.5}

    assert (scaler.eval_dist(values=_values, distance=10)
            == '0.5 + (1 - (abs(10 - 8) / 4)) * 1')


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


@pytest.mark.unit
def test_parameterscalers_iexpr_generator():
    """ephys.parameterscalers: Test iexpr generation from python expression"""

    value = 2.125
    value_scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        name='soma_distance_scaler',
        distribution='(0.62109375 - math.log( math.pi ) * math.exp('
                     '({distance}) / 0.421875)) * {value}')

    iexpr = value_scaler.acc_scale_iexpr(
        value=value, constant_formatter=lambda v: '%.9g' % v)

    assert iexpr == '(sub (scalar 0.62109375) ' \
                    '(mul (log (pi) ) ' \
                    '(exp (div (distance (region "soma")) ' \
                    '(scalar 0.421875) ) ) ) )'


@pytest.mark.unit
def test_parameterscalers_iexpr_generator_non_existent_op():
    """ephys.parameterscalers: Test iexpr generation from python expression
    with invalid node"""

    value = 2.125
    value_scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        name='soma_distance_scaler',
        distribution='(0.62109375 - math.log( math.pi ) * non_existent_func('
                     '({distance}) / 0.421875)) * {value}')

    with pytest.raises(ValueError,
                       match='Arbor iexpr generation failed - '
                             'unsupported function non_existent_func.'):
        iexpr = value_scaler.acc_scale_iexpr(
            value=value, constant_formatter=lambda v: '%.9g' % v)


@pytest.mark.unit
def test_parameterscalers_iexpr_generator_unsupported_attr():
    """ephys.parameterscalers: Test iexpr generation from python expression
    with invalid node"""

    value = 2.125
    value_scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        name='soma_distance_scaler',
        distribution='(0.62109375 - math.log( math.pi )* math.tau.hex('
                     '({distance}) / 0.421875)) * {value}')

    with pytest.raises(ValueError,
                       match='Arbor iexpr generation failed - '
                             'unsupported attribute tau.'):
        iexpr = value_scaler.acc_scale_iexpr(
            value=value, constant_formatter=lambda v: '%.9g' % v)
