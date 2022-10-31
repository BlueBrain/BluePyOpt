"""Tests for create_acc.py"""

# pylint: disable=W0212

import os
from pathlib import Path
import re
import json
import tempfile

from bluepyopt import _arbor as arbor
from bluepyopt.ephys.acc.acc_label import ArbLabel
from bluepyopt.ephys.morphologies import ArbFileMorphology

from .. import utils

from bluepyopt import ephys
from bluepyopt.ephys.acc import create_acc


import pytest

DEFAULT_ARBOR_REGION_ORDER = [
    ('soma', 1),
    ('axon', 2),
    ('dend', 3),
    ('apic', 4),
    ('myelin', 5)]


testdata_dir = (Path(__file__).parent.parent) / "testdata"


@pytest.mark.unit
def test_read_templates():
    """Unit test for _read_templates function."""
    template_dir = testdata_dir / 'acc' / 'templates'
    template_filename = "*_template.jinja2"
    templates = create_acc.read_templates(template_dir, template_filename)
    assert templates.keys() == {'label_dict.acc', 'cell.json', 'decor.acc'}

    with pytest.raises(FileNotFoundError):
        create_acc.read_templates("DOES_NOT_EXIST", template_filename)


@pytest.mark.unit
def test_arb_load_mech_catalogue_meta():
    """Unit test for _arb_load_mech_catalogue_meta function."""
    mech_catalogue_meta = create_acc._arb_load_mech_catalogue_meta(None)
    assert isinstance(mech_catalogue_meta, dict)
    assert mech_catalogue_meta.keys() == {'BBP', 'default', 'allen'}
    assert "Ca_HVA" in mech_catalogue_meta['BBP']


@pytest.mark.unit
def test_populate_label_dict():
    """Unit test for _populate_label_dict."""
    mechs_1 = {ArbLabel("region", "all", "(all)"): {}}
    mechs_2 = {ArbLabel("region", "tag1", "(tag 1)"): {}}
    mechs_3 = {}
    result = create_acc._populate_label_dict(mechs_1, mechs_2, mechs_3)
    assert result.keys() == {"tag1", "all"}

    with pytest.raises(LookupError):
        mechs_4 = {ArbLabel("region", "all", "(tag 1)"): {}}
        create_acc._populate_label_dict(mechs_1, mechs_2, mechs_4)


@pytest.mark.unit
def test_create_acc():
    """ephys.create_acc: Test create_acc"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    acc = create_acc.create_acc([mech, ], parameters,
                                morphology='CCell.swc',
                                template_name='CCell')

    ref_dir = testdata_dir / 'acc/CCell'
    cell_json = "CCell.json"
    decor_acc = "CCell_decor.acc"
    label_dict_acc = "CCell_label_dict.acc"

    # Testing keys
    assert cell_json in acc
    cell_json_dict = json.loads(acc[cell_json])
    assert 'cell_model_name' in cell_json_dict
    assert 'produced_by' in cell_json_dict
    assert 'morphology' in cell_json_dict
    assert 'label_dict' in cell_json_dict
    assert 'decor' in cell_json_dict
    # Testing values
    with open(ref_dir / cell_json) as f:
        ref_cell_json = json.load(f)
    for k in ref_cell_json:
        if k != 'produced_by':
            assert ref_cell_json[k] == cell_json_dict[k]

    # Testing building blocks
    assert decor_acc in acc
    assert acc[decor_acc].startswith('(arbor-component')
    assert '(decor' in acc[decor_acc]
    # Testing values
    with open(ref_dir / decor_acc) as f:
        ref_decor = f.read()
    assert ref_decor == acc[decor_acc]  # decor data not exposed in Python

    # Testing building blocks
    assert label_dict_acc in acc
    assert acc[label_dict_acc].startswith('(arbor-component')
    assert '(label-dict' in acc[label_dict_acc]
    matches = re.findall(r'\(region-def "(?P<loc>\w+)" \(tag (?P<tag>\d+)\)\)',
                         acc[label_dict_acc])
    for pos, loc_tag in enumerate(DEFAULT_ARBOR_REGION_ORDER):
        assert matches[pos][0] == loc_tag[0]
        assert matches[pos][1] == str(loc_tag[1])
    # Testing values
    ref_labels = arbor.load_component(
        ref_dir / label_dict_acc).component
    with tempfile.TemporaryDirectory() as test_dir:
        test_labels_filename = os.path.join(test_dir, label_dict_acc)
        with open(test_labels_filename, 'w') as f:
            f.write(acc[label_dict_acc])
        test_labels = arbor.load_component(test_labels_filename).component
    assert dict(ref_labels.items()) == dict(test_labels.items())


@pytest.mark.unit
def test_create_acc_filename():
    """ephys.create_acc: Test create_acc template_filename"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()
    custom_param_val = str(__file__)

    acc = create_acc.create_acc(
        [mech, ],
        parameters, morphology='CCell.asc',
        template_name='CCell',
        template_filename='acc/templates/*_template.jinja2',
        template_dir=testdata_dir,
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


@pytest.mark.unit
def test_create_acc_replace_axon():
    """ephys.create_acc: Test create_acc with axon replacement"""
    mech = utils.make_mech()
    parameters = utils.make_parameters()

    replace_axon_st = arbor.segment_tree()
    latest_seg = arbor.mnpos

    for prox_x, dist_x in [(5, 35), (35, 65)]:
        latest_seg = replace_axon_st.append(
            latest_seg,
            arbor.mpoint(prox_x, 0, 0, 0.5),
            arbor.mpoint(dist_x, 0, 0, 0.5),
            ArbFileMorphology.tags['axon']
        )

    replace_axon = arbor.morphology(replace_axon_st)

    try:
        acc = create_acc.create_acc([mech, ], parameters,
                                    morphology_dir=testdata_dir,
                                    morphology='simple.swc',
                                    template_name='CCell',
                                    replace_axon=replace_axon)
    except Exception as e:  # fail with an older Arbor version
        assert isinstance(e, NotImplementedError)
        assert len(e.args) == 1 and e.args[0] == \
            "Need a newer version of Arbor for axon replacement."
        return

    cell_json = "CCell.json"
    cell_json_dict = json.loads(acc[cell_json])
    assert 'replace_axon' in cell_json_dict['morphology']

    with open((testdata_dir / "acc/CCell/simple_axon_replacement.acc")) as f:
        replace_axon_ref = f.read()

    assert acc[cell_json_dict['morphology']['replace_axon']] == \
        replace_axon_ref


def make_cell(replace_axon):
    morph_filename = testdata_dir / 'simple_ax2.swc'
    morph = ephys.morphologies.NrnFileMorphology(morph_filename,
                                                 do_replace_axon=replace_axon)
    somatic_loc = ephys.locations.NrnSeclistLocation(
        'somatic', seclist_name='somatic')
    mechs = [ephys.mechanisms.NrnMODMechanism(
        name='hh', suffix='hh', locations=[somatic_loc])]
    gkbar_hh_scaler = '(-0.62109375 + 0.546875*math.log(' \
                      '({distance})*0.421875 + 1.25))*{value}'
    params = [
        ephys.parameters.NrnSectionParameter(
            name='gnabar_hh',
            param_name='gnabar_hh',
            locations=[somatic_loc]),
        ephys.parameters.NrnRangeParameter(
            name='gkbar_hh',
            param_name='gkbar_hh',
            value_scaler=ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
                distribution=gkbar_hh_scaler),
            locations=[somatic_loc])]
    return ephys.models.CellModel(
        'simple_ax2',
        morph=morph,
        mechs=mechs,
        params=params)


def run_short_sim(cable_cell):
    # Create cell model
    arb_cell_model = arbor.single_cell_model(cable_cell)
    arb_cell_model.properties.catalogue = arbor.catalogue()
    arb_cell_model.properties.catalogue.extend(
        arbor.default_catalogue(), "default::")
    arb_cell_model.properties.catalogue.extend(
        arbor.bbp_catalogue(), "BBP::")

    # Run a very short simulation to test mechanism instantiation
    arb_cell_model.run(tfinal=0.1)


@pytest.mark.unit
def test_cell_model_output_and_read_acc():
    """ephys.create_acc: Test output_acc and read_acc w/o axon replacement"""
    cell = make_cell(replace_axon=False)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with tempfile.TemporaryDirectory() as acc_dir:
        create_acc.output_acc(acc_dir, cell, param_values)
        cell_json, arb_morph, arb_decor, arb_labels = \
            create_acc.read_acc(
                os.path.join(acc_dir, cell.name + '.json'))
    assert 'replace_axon' not in cell_json['morphology']

    cable_cell = arbor.cable_cell(morphology=arb_morph,
                                  decor=arb_decor,
                                  labels=arb_labels)
    assert isinstance(cable_cell, arbor.cable_cell)
    assert len(cable_cell.cables('"soma"')) == 1
    assert len(cable_cell.cables('"axon"')) == 1
    assert len(arb_morph.branch_segments(
        cable_cell.cables('"soma"')[0].branch)) == 5
    assert len(arb_morph.branch_segments(
        cable_cell.cables('"axon"')[0].branch)) == 5

    run_short_sim(cable_cell)


def test_cell_model_output_and_read_acc_replace_axon():
    """ephys.create_acc: Test output_acc and read_acc w/ axon replacement"""
    cell = make_cell(replace_axon=True)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with tempfile.TemporaryDirectory() as acc_dir:
        try:
            create_acc.output_acc(acc_dir, cell, param_values,
                                  sim=ephys.simulators.NrnSimulator())
        except Exception as e:  # fail with an older Arbor version
            assert isinstance(e, NotImplementedError)
            assert len(e.args) == 1 and e.args[0] == \
                "Need a newer version of Arbor for axon replacement."
            return
        # Axon replacement implemented in installed Arbor version
        cell_json, arb_morph, arb_decor, arb_labels = \
            create_acc.read_acc(
                os.path.join(acc_dir, cell.name + '.json'))

    assert 'replace_axon' in cell_json['morphology']
    cable_cell = arbor.cable_cell(morphology=arb_morph,
                                  decor=arb_decor,
                                  labels=arb_labels)
    assert isinstance(cable_cell, arbor.cable_cell)
    assert len(cable_cell.cables('"soma"')) == 1
    assert len(cable_cell.cables('"axon"')) == 1
    assert len(arb_morph.branch_segments(
        cable_cell.cables('"soma"')[0].branch)) == 6
    assert len(arb_morph.branch_segments(
        cable_cell.cables('"axon"')[0].branch)) == 6
    assert cable_cell.cables('"soma"')[0].prox == 0.
    assert abs(cable_cell.cables('"soma"')[0].dist -
               cable_cell.cables('"axon"')[0].prox) < 1e-6
    assert cable_cell.cables('"axon"')[0].dist == 1.

    run_short_sim(cable_cell)


def test_cell_model_create_acc_replace_axon_without_instantiate():
    """ephys.create_acc: Test output_acc and read_acc w/ axon replacement"""
    cell = make_cell(replace_axon=True)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with pytest.raises(ValueError,
                       match='Need an instance of NrnSimulator in sim'
                             ' to instantiate morphology in order to'
                             ' create JSON/ACC-description with'
                             ' axon replacement.'):
        cell.create_acc(param_values)
