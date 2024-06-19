"""Tests for create_hoc.py"""

# pylint: disable=W0212

import os

from bluepyopt.ephys.acc import ArbLabel
from bluepyopt.ephys.locations import NrnSomaDistanceCompLocation
from bluepyopt.ephys.parameterscalers import NrnSegmentSomaDistanceScaler
from bluepyopt.ephys.parameterscalers import NrnSegmentSomaDistanceStepScaler

from . import utils
from bluepyopt.ephys import create_acc, create_hoc


import pytest

DEFAULT_LOCATION_ORDER = [
    'all',
    'apical',
    'axonal',
    'basal',
    'somatic',
    'myelinated']


@pytest.mark.unit
def test_generate_channels_by_location():
    """ephys.create_hoc: Test generate_channels_by_location"""
    mech = utils.make_mech()
    public_res = create_hoc.generate_channels_by_location(
        [mech], DEFAULT_LOCATION_ORDER,
    )
    private_res = create_hoc._generate_channels_by_location(
        [mech], DEFAULT_LOCATION_ORDER, create_hoc._loc_desc
    )
    assert public_res == private_res


@pytest.mark.unit
def test__generate_channels_by_location():
    """ephys.create_hoc: Test _generate_channels_by_location"""
    mech = utils.make_mech()
    channels, point_channels = create_hoc._generate_channels_by_location(
        [mech, ], DEFAULT_LOCATION_ORDER, create_hoc._loc_desc)

    assert len(channels['apical']) == 1
    assert len(channels['basal']) == 1

    assert channels['apical'] == ['Ih']
    assert channels['basal'] == ['Ih']

    for loc in point_channels:
        assert len(point_channels[loc]) == 0


@pytest.mark.unit
def test_generate_parameters():
    """ephys.create_hoc: Test generate_parameters"""
    parameters = utils.make_parameters()

    assert create_hoc.generate_parameters(parameters) == \
        create_hoc._generate_parameters(parameters,
                                        DEFAULT_LOCATION_ORDER,
                                        create_hoc._loc_desc)


@pytest.mark.unit
def test__generate_parameters():
    """ephys.create_hoc: Test _generate_parameters"""
    parameters = utils.make_parameters()

    global_params, section_params, range_params, \
        pprocess_params, location_order = \
        create_hoc._generate_parameters(parameters,
                                        DEFAULT_LOCATION_ORDER,
                                        create_hoc._loc_desc)

    assert global_params == {'gSKv3_1bar_SKv3_1': 65}
    assert len(section_params[1]) == 2
    assert len(section_params[4]) == 2
    assert section_params[4][0] == 'somatic'
    assert len(section_params[4][1]) == 2
    assert range_params == []
    for loc, pparams in pprocess_params:
        assert loc in DEFAULT_LOCATION_ORDER
        assert len(pparams) == 0
    assert location_order == DEFAULT_LOCATION_ORDER


@pytest.mark.unit
def test_create_hoc():
    """ephys.create_hoc: Test create_hoc"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    hoc = create_hoc.create_hoc([mech, ], parameters, template_name='CCell')
    assert 'load_file' in hoc
    assert 'CCell' in hoc
    assert 'begintemplate' in hoc
    assert 'endtemplate' in hoc


@pytest.mark.unit
def test_create_hoc_filename():
    """ephys.create_hoc: Test create_hoc template_filename"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()
    custom_param_val = 'printf("Hello world!")'

    hoc = create_hoc.create_hoc([mech, ],
                                parameters, template_name='CCell',
                                template_filename='test.jinja2',
                                template_dir=os.path.join(
                                    os.path.dirname(__file__),
                                    'testdata'),
                                custom_jinja_params={
                                    'custom_param': custom_param_val})
    assert 'load_file' in hoc
    assert 'CCell' in hoc
    assert 'begintemplate' in hoc
    assert 'endtemplate' in hoc
    assert 'Test template' in hoc
    assert custom_param_val in hoc


@pytest.mark.unit
def test_generate_reinitrng():
    """ephys.create_hoc: Test generate_reinitrng"""
    mech = utils.make_mech()
    re_init_rng = create_hoc.generate_reinitrng([mech])
    assert 'func hash_str() {localobj sf strdef right' in re_init_rng
    assert ' hash = (hash * 31 + char_int) % (2 ^ 31 - 1)' in re_init_rng


@pytest.mark.unit
def test_range_exprs_to_hoc():
    """ephys.create_hoc: Test range_exprs_to_hoc"""
    apical_region = ArbLabel("region", "apic", "(tag 4)")
    param_scaler = NrnSegmentSomaDistanceScaler(
        name='soma-distance-scaler',
        distribution='(-0.8696 + 2.087*math.exp(({distance})*0.0031))*{value}'
    )

    range_expr = create_acc.RangeExpr(
        location=apical_region,
        name="gkbar_hh",
        value=0.025,
        value_scaler=param_scaler
    )

    hoc = create_hoc.range_exprs_to_hoc([range_expr])
    assert hoc[0].param_name == 'gkbar_hh'
    val_gt = '(-0.8696 + 2.087*exp((%.17g)*0.0031))*0.025000000000000001'
    assert hoc[0].value == val_gt


@pytest.mark.unit
def test_range_exprs_to_hoc_step_scaler():
    """ephys.create_hoc: Test range_exprs_to_hoc with step scaler"""
    # apical_region = ArbLabel("region", "apic", "(tag 4)")
    apical_location = NrnSomaDistanceCompLocation(
        name='apic100',
        soma_distance=100,
        seclist_name='apical',
    )
    param_scaler = NrnSegmentSomaDistanceStepScaler(
        name='soma-distance-step-scaler',
        distribution='{value} * (0.1 + 0.9 * int('
                     '({distance} > {step_begin}) & ('
                     '{distance} < {step_end})))',
        step_begin=300,
        step_end=500)

    range_expr = create_hoc.RangeExpr(
        location=apical_location,
        name="gCa_LVAstbar_Ca_LVAst",
        value=1,
        value_scaler=param_scaler
    )

    hoc = create_hoc.range_exprs_to_hoc([range_expr])
    assert hoc[0].param_name == 'gCa_LVAstbar_Ca_LVAst'
    val_gt = '1 * (0.1 + 0.9 * int((%.17g > 300) && (%.17g < 500)))'
    assert hoc[0].value == val_gt
