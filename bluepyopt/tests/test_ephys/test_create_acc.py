"""Tests for create_acc.py"""

# pylint: disable=W0212

import os
import re
import json

from . import utils
from bluepyopt.ephys import create_acc


import pytest

DEFAULT_ARBOR_REGION_ORDER = [
    ('apic', 4),
    ('axon', 2),
    ('dend', 3),
    ('soma', 1)]


@pytest.mark.unit
def test_create_acc():
    """ephys.create_hoc: Test create_hoc"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    acc = create_acc.create_acc([mech, ], parameters,  
                                morphology='CCell.swc', 
                                template_name='CCell')

    cell_json = "CCell.json"
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
    matches = re.findall(r'\(region-def "(?P<loc>\w+)" \(tag (?P<tag>\d+)\)\)', 
                         acc[label_dict_acc])
    for pos, loc_tag in enumerate(DEFAULT_ARBOR_REGION_ORDER):
        assert matches[pos][0] == loc_tag[0]
        assert matches[pos][1] == str(loc_tag[1])


@pytest.mark.unit
def test_create_acc_filename():
    """ephys.create_hoc: Test create_acc template_filename"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()
    custom_param_val = str(__file__)

    acc = create_acc.create_acc([mech, ],
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
    matches = re.findall(r'\(region-def "(?P<loc>\w+)" \(tag (?P<tag>\d+)\)\)', 
                         acc[label_dict_acc])
    for pos, loc_tag in enumerate(DEFAULT_ARBOR_REGION_ORDER):
        assert matches[pos][0] == loc_tag[0]
        assert matches[pos][1] == str(loc_tag[1])

    assert '(meta-data (info "test-decor"))' in acc[decor_acc]
    assert '(meta-data (info "test-label-dict"))' in acc[label_dict_acc]
    assert custom_param_val in cell_json_dict['produced_by']
