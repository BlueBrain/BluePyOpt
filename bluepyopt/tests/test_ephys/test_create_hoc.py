"""Tests for create_hoc.py"""

# pylint: disable=W0212

import os
import re
import json

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
def test__generate_channels_by_location():
    """ephys.create_hoc: Test _generate_channels_by_location"""
    mech = utils.make_mech()
    channels = create_hoc._generate_channels_by_location(
        [mech, ], DEFAULT_LOCATION_ORDER)

    assert len(channels['apical']) == 1
    assert len(channels['basal']) == 1

    assert channels['apical'] == ['Ih']
    assert channels['basal'] == ['Ih']


@pytest.mark.unit
def test__generate_parameters():
    """ephys.create_hoc: Test _generate_parameters"""
    parameters = utils.make_parameters()

    global_params, section_params, range_params, location_order = \
        create_hoc._generate_parameters(parameters)

    assert global_params == {'NrnGlobalParameter': 65}
    assert len(section_params[1]) == 2
    assert len(section_params[4]) == 2
    assert section_params[4][0] == 'somatic'
    assert len(section_params[4][1]) == 2
    assert range_params == []
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
def test_create_acc():
    """ephys.create_hoc: Test create_hoc"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    acc = create_hoc.create_acc([mech, ], parameters,  morphology='CCell.swc', template_name='CCell')

    cell_json = "CCell_cell.json"
    decor_acc = "CCell_decor.acc"
    label_dict_acc = "CCell_label_dict.acc"

    assert cell_json in acc
    cell_json_dict = json.loads(acc[cell_json])
    assert 'cell_model_name' in cell_json_dict
    assert 'produced_by' in cell_json_dict
    assert 'morphology' in cell_json_dict
    assert 'label_dict' in cell_json_dict
    assert 'decor' in cell_json_dict

    assert decor_acc in acc
    assert acc[decor_acc].startswith('(arbor-component')
    assert '(decor' in acc[decor_acc]

    assert label_dict_acc in acc
    assert acc[label_dict_acc].startswith('(arbor-component')
    assert '(label-dict' in acc[label_dict_acc]
    matches = re.findall(r'\(region-def "(?P<loc>\w+)" \(tag (?P<tag>\d+)\)\)', acc[label_dict_acc])
    for tag, loc in enumerate(DEFAULT_LOCATION_ORDER):
        assert matches[tag][0] == loc
        assert matches[tag][1] == str(tag)


@pytest.mark.unit
def test_create_acc_filename():
    """ephys.create_hoc: Test create_acc template_filename"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()
    custom_param_val = str(__file__)

    acc = create_hoc.create_acc([mech, ],
                                parameters, morphology='CCell.asc',
                                template_name='CCell',
                                template_filename='acc/*_template.jinja2',
                                template_dir=os.path.join(
                                    os.path.dirname(__file__),
                                    'testdata'),
                                custom_jinja_params={
                                    'custom_param': custom_param_val})
    cell_json = "CCell_cell.json"
    decor_acc = "CCell_decor.acc"
    label_dict_acc = "CCell_label_dict.acc"

    assert cell_json in acc
    cell_json_dict = json.loads(acc[cell_json])
    assert 'cell_model_name' in cell_json_dict
    assert 'produced_by' in cell_json_dict
    assert 'morphology' in cell_json_dict
    assert 'label_dict' in cell_json_dict
    assert 'decor' in cell_json_dict

    assert decor_acc in acc
    assert acc[decor_acc].startswith('(arbor-component')
    assert '(decor' in acc[decor_acc]

    assert label_dict_acc in acc
    assert acc[label_dict_acc].startswith('(arbor-component')
    assert '(label-dict' in acc[label_dict_acc]
    matches = re.findall(r'\(region-def "(?P<loc>\w+)" \(tag (?P<tag>\d+)\)\)', acc[label_dict_acc])
    for tag, loc in enumerate(DEFAULT_LOCATION_ORDER):
        assert matches[tag][0] == loc
        assert matches[tag][1] == str(tag)

    assert '(meta-data (info "test-decor"))' in acc[decor_acc]
    assert '(meta-data (info "test-label-dict"))' in acc[label_dict_acc]
    assert custom_param_val in cell_json_dict['produced_by']
