"""Tests for create_hoc.py"""

# pylint: disable=W0212

import os

from . import utils
from bluepyopt.ephys import create_hoc


import pytest
import numpy

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
