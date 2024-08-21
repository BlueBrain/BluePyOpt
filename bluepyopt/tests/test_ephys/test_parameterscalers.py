"""Test ephys.parameterscalers"""

import json
import pathlib
import tempfile
import arbor

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
def test_NrnSegmentSomaDistanceStepScaler_eval_dist_with_dict():
    """ephys.parameterscalers: eval_dist of NrnSegmentSomaDistanceStepScaler"""

    dist = '{value} * (0.1 + 0.9 * int(' \
           '({distance} > {step_begin}) & ({distance} < {step_end})))'

    scaler = ephys.parameterscalers.NrnSegmentSomaDistanceStepScaler(
        distribution=dist, step_begin=300, step_end=500)

    _values = {'value': 1}

    assert (scaler.eval_dist(values=_values, distance=10)
            == '1 * (0.1 + 0.9 * int((10 > 300) & (10 < 500)))')


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


@pytest.mark.unit
def test_parameterscalers_iexpr():
    """ephys.parameterscalers: Test iexpr"""
    # iexpr from bluepyopt/tests/test_ephys/test_parameterscalers.py
    iexpr = '(sub (scalar 0.62109375) ' \
            '(mul (log (pi) ) ' \
            '(exp (div (distance (region "soma")) ' \
            '(scalar 0.421875) ) ) ) )'

    # modified decor as in
    # bluepyopt/tests/test_ephys/testdata/acc/simplecell/simple_cell_decor.acc
    simple_cell_decor_with_iexpr = \
        '(arbor-component\n' \
        '  (meta-data (version "0.9-dev"))\n' \
        '  (decor\n' \
        '    (paint (region "soma") ' \
        '(membrane-capacitance 0.01 (scalar 1.0)))\n' \
        '    (paint (region "soma") ' \
        '(scaled-mechanism (density (mechanism "default::hh" ' \
        '("gnabar" 0.10299326453483033) ("gkbar" 0.027124836082684685))) ' \
        f'("gkbar" {iexpr})))))'

    with tempfile.TemporaryDirectory() as test_dir:
        decor_filename = pathlib.Path(test_dir).joinpath("decor.acc")
        with open(decor_filename, "w") as f:
            f.write(simple_cell_decor_with_iexpr)
        test_decor = arbor.load_component(decor_filename).component
        assert test_decor.defaults() == []
        assert test_decor.placements() == []
        assert len(test_decor.paintings()) == 2
        assert test_decor.paintings()[0][0] == '(region "soma")'
        assert str(test_decor.paintings()[0][1]) == 'Cm=0.01'
        assert test_decor.paintings()[1][0] == '(region "soma")'
        scaled_mech_str = "<arbor.scaled_mechanism<density> " \
            "(mechanism('default::hh', %s), " \
            '{"gkbar": (sub (scalar 0.621094) (mul (log (scalar 3.14159)) ' \
            '(exp (div (distance 1 (region "soma")) ' \
            '(scalar 0.421875)))))})>'
        str1 = scaled_mech_str % '{"gkbar": 0.0271248, "gnabar": 0.102993}'
        str2 = scaled_mech_str % '{"gnabar": 0.102993, "gkbar": 0.0271248}'
        assert str(test_decor.paintings()[1][1]) in [str1, str2]
