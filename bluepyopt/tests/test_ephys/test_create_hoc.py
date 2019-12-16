"""Tests for create_hoc.py"""

# pylint: disable=W0212

import os

import utils
from bluepyopt.ephys import create_hoc

import nose.tools as nt
from nose.plugins.attrib import attr

DEFAULT_LOCATION_ORDER = [
    'all',
    'apical',
    'axonal',
    'basal',
    'somatic',
    'myelinated']


@attr('unit')
def test__generate_channels_by_location():
    """ephys.create_hoc: Test _generate_channels_by_location"""
    mech = utils.make_mech()
    channels = create_hoc._generate_channels_by_location(
        [mech, ], DEFAULT_LOCATION_ORDER)

    nt.assert_equal(len(channels['apical']), 1)
    nt.assert_equal(len(channels['basal']), 1)

    nt.assert_equal(channels['apical'], ['Ih'])
    nt.assert_equal(channels['basal'], ['Ih'])


@attr('unit')
def test__generate_parameters():
    """ephys.create_hoc: Test _generate_parameters"""
    parameters = utils.make_parameters()

    global_params, section_params, range_params, location_order = \
        create_hoc._generate_parameters(parameters)

    nt.assert_equal(global_params, {'NrnGlobalParameter': 65})
    nt.assert_equal(len(section_params[1]), 2)
    nt.assert_equal(len(section_params[4]), 2)
    nt.assert_equal(section_params[4][0], 'somatic')
    nt.assert_equal(len(section_params[4][1]), 2)
    nt.assert_equal(range_params, [])
    nt.assert_equal(location_order, DEFAULT_LOCATION_ORDER)


@attr('unit')
def test_create_hoc():
    """ephys.create_hoc: Test create_hoc"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    hoc = create_hoc.create_hoc([mech, ], parameters, template_name='CCell')
    nt.ok_('load_file' in hoc)
    nt.ok_('CCell' in hoc)
    nt.ok_('begintemplate' in hoc)
    nt.ok_('endtemplate' in hoc)


@attr('unit')
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
    nt.ok_('load_file' in hoc)
    nt.ok_('CCell' in hoc)
    nt.ok_('begintemplate' in hoc)
    nt.ok_('endtemplate' in hoc)
    nt.ok_('Test template' in hoc)
    nt.ok_(custom_param_val in hoc)
