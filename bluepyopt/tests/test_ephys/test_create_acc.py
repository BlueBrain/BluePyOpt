"""Tests for create_acc.py"""

# pylint: disable=W0212

import os
import sys
import pathlib
import re
import json
import tempfile

from bluepyopt.ephys.acc import arbor, ArbLabel
from bluepyopt.ephys.morphologies import ArbFileMorphology
from bluepyopt.ephys.parameterscalers import NrnSegmentSomaDistanceScaler

from . import utils

from bluepyopt import ephys
from bluepyopt.ephys import create_acc
from bluepyopt.ephys.create_acc import (Nrn2ArbParamFormatter,
                                        Nrn2ArbMechGrouper,
                                        ArbNmodlMechFormatter)

import pytest

DEFAULT_ARBOR_REGION_ORDER = [
    ('soma', 1),
    ('axon', 2),
    ('dend', 3),
    ('apic', 4),
    ('myelin', 5)]


testdata_dir = pathlib.Path(__file__).parent.joinpath(
    'testdata')


@pytest.mark.unit
def test_read_templates():
    """Unit test for _read_templates function."""
    template_dir = testdata_dir / 'acc/templates'
    template_filename = "*_template.jinja2"
    templates = create_acc._read_templates(template_dir, template_filename)
    assert templates.keys() == {'label_dict.acc', 'cell.json', 'decor.acc'}

    with pytest.raises(FileNotFoundError):
        create_acc._read_templates("DOES_NOT_EXIST", template_filename)


@pytest.mark.unit
def test_Nrn2ArbParamFormatter_param_name():
    """Test Neuron to Arbor parameter mapping."""
    # Identity
    mech_param_name = "gSKv3_1bar_SKv3_1"
    assert Nrn2ArbParamFormatter._param_name(mech_param_name) \
        == mech_param_name

    # Non-trivial transformation
    global_property_name = "v_init"
    assert Nrn2ArbParamFormatter._param_name(global_property_name) \
        == "membrane-potential"


@pytest.mark.unit
def test_Nrn2ArbParamFormatter_param_value():
    """Test Neuron to Arbor parameter units conversion."""
    # Identity for region parameter
    mech_param = create_acc.Location(name="gSKv3_1bar_SKv3_1", value="1.025")
    assert Nrn2ArbParamFormatter._param_value(mech_param) == "1.025"

    # Non-trivial name transformation, but identical value/units
    global_property = create_acc.Location(name="v_init", value=-65)
    assert Nrn2ArbParamFormatter._param_value(global_property) == "-65"

    # Non-trivial name and value/units transformation
    global_property = create_acc.Location(name="celsius", value=34)
    assert Nrn2ArbParamFormatter._param_value(global_property) == (
        "307.14999999999998")


@pytest.mark.unit
def test_Nrn2ArbParamFormatter_format():
    """Test Neuron to Arbor parameter reformatting."""
    # Constant mechanism parameter
    mech_param = create_acc.Location(name="gSKv3_1bar_SKv3_1", value="1.025")
    mech = "SKv3_1"
    arb_mech_param = create_acc.Location(name="gSKv3_1bar", value="1.025")
    assert (
        Nrn2ArbParamFormatter.format(
            mech_param, mechs=[mech])
        == (mech, arb_mech_param)
    )

    # Non-unique mapping to mechanisms
    with pytest.raises(create_acc.CreateAccException):
        Nrn2ArbParamFormatter.format(
            mech_param, mechs=["SKv3_1", "1"])

    # Global property with non-trivial transformation
    global_property = create_acc.Location(name="celsius", value="0")
    mech = None
    arb_global_property = create_acc.Location(
        name="temperature-kelvin", value="273.14999999999998")
    # Non-trivial name and value/units transformation
    assert Nrn2ArbParamFormatter.format(global_property, []) == \
        (mech, arb_global_property)

    # Inhomogeneuos mechanism parameter
    apical_region = ArbLabel("region", "apic", "(tag 4)")
    param_scaler = NrnSegmentSomaDistanceScaler(
        name='soma-distance-scaler',
        distribution='(-0.8696 + 2.087*math.exp(({distance})*0.0031))*{value}'
    )

    iexpr_param = create_acc.RangeExpr(
        location=apical_region,
        name="gkbar_hh",
        value="0.025",
        value_scaler=param_scaler
    )
    mech = "hh"
    arb_iexpr_param = create_acc.RangeExpr(
        location=apical_region,
        name="gkbar",
        value="0.025",
        value_scaler=param_scaler,
    )
    assert (
        Nrn2ArbParamFormatter.format(
            iexpr_param, mechs=[mech])
        == (mech, arb_iexpr_param)
    )

    # Point process mechanism parameter
    loc = ephys.locations.ArbLocsetLocation(
        name='somacenter',
        locset='(location 0 0.5)')

    mech = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[loc])

    mech_loc = ephys.locations.NrnPointProcessLocation(
        'expsyn_loc',
        pprocess_mech=mech)

    point_expr_param = create_acc.PointExpr(
        name="tau", value="10", point_loc=[mech_loc])

    arb_point_expr_param = create_acc.PointExpr(
        name="tau", value="10", point_loc=[mech_loc])
    assert (
        Nrn2ArbParamFormatter.format(
            point_expr_param, mechs=[mech])
        == (mech, arb_point_expr_param)
    )


@pytest.mark.unit
def test_Nrn2ArbMechGrouper_format_params_and_group_by_mech():
    """Test grouping of parameters by mechanism."""
    params = [create_acc.Location(name="gSKv3_1bar_SKv3_1", value="1.025"),
              create_acc.Location(name="ena", value="-30")]
    mechs = ["SKv3_1"]
    local_mechs = Nrn2ArbMechGrouper.\
        _format_params_and_group_by_mech(params, mechs)
    assert local_mechs == \
        {None: [create_acc.Location(name="ion-reversal-potential \"na\"",
                                    value="-30")],
         "SKv3_1": [create_acc.Location(name="gSKv3_1bar", value="1.025")]}


@pytest.mark.unit
def test_Nrn2ArbMechGrouper_process_global():
    """Test adapting global parameters from Neuron to Arbor."""
    params = {"ki": 3, "v_init": -65}
    global_mechs = Nrn2ArbMechGrouper.process_global(params)
    assert global_mechs == {
        None: [create_acc.Location(name="ion-internal-concentration \"k\"",
                                   value="3"),
               create_acc.Location(name="membrane-potential",
                                   value="-65")]}


@pytest.mark.unit
def test_Nrn2ArbMechGrouper_is_global_property():
    """Test adapting local parameters from Neuron to Arbor."""
    all_regions = ArbLabel("region", "all_regions", "(all)")
    param = create_acc.Location(name="axial-resistivity", value="1")
    assert Nrn2ArbMechGrouper._is_global_property(
        all_regions, param) is True

    soma_region = ArbLabel("region", "soma", "(tag 1)")
    assert Nrn2ArbMechGrouper._is_global_property(
        soma_region, param) is False


@pytest.mark.unit
def test_separate_global_properties():
    """Test separating global properties from label-specific mechs."""
    all_regions = ArbLabel("region", "all_regions", "(all)")
    mechs = {None: [create_acc.Location(name="axial-resistivity", value="1")],
             "SKv3_1": [create_acc.Location(name="gSKv3_1bar", value="1.025")]}
    local_mechs, global_properties = \
        Nrn2ArbMechGrouper._separate_global_properties(all_regions, mechs)
    assert local_mechs == {None: [], "SKv3_1": mechs["SKv3_1"]}
    assert global_properties == {None: mechs[None]}


@pytest.mark.unit
def test_Nrn2ArbMechGrouper_process_local():
    """Test adapting local parameters from Neuron to Arbor."""
    all_regions = ArbLabel("region", "all_regions", "(all)")
    soma_region = ArbLabel("region", "soma", "(tag 1)")
    params = [
        (all_regions,
         [create_acc.Location(name="cm", value="100")]),
        (soma_region,
         [create_acc.Location(name="v_init", value="-65"),
          create_acc.Location(name="gSKv3_1bar_SKv3_1", value="1.025")])
    ]
    channels = {all_regions: [], soma_region: ["SKv3_1"]}
    local_mechs, global_properties = \
        Nrn2ArbMechGrouper.process_local(params, channels)
    assert local_mechs.keys() == {all_regions, soma_region}
    assert local_mechs[all_regions] == {None: []}
    assert local_mechs[soma_region] == {
        None: [create_acc.Location(name="membrane-potential", value="-65")],
        "SKv3_1": [create_acc.Location(name="gSKv3_1bar", value="1.025")]
    }
    assert global_properties == {
        None: [create_acc.Location(name="membrane-capacitance", value="1")]}


@pytest.mark.unit
def test_ArbNmodlMechFormatter_load_mech_catalogue_meta():
    """Test loading Arbor built-in mech catalogue metadata."""
    nmodl_formatter = ArbNmodlMechFormatter(None)

    assert isinstance(nmodl_formatter.cats, dict)
    assert nmodl_formatter.cats.keys() == {'BBP', 'default', 'allen'}
    assert "Ca_HVA" in nmodl_formatter.cats['BBP']


@pytest.mark.unit
def test_ArbNmodlMechFormatter_mech_name():
    """Test mechanism name translation."""
    assert ArbNmodlMechFormatter._mech_name("Ca_HVA") == "Ca_HVA"
    assert ArbNmodlMechFormatter._mech_name("ExpSyn") == "expsyn"


@pytest.mark.unit
def test_ArbNmodlMechFormatter_translate_density():
    """Test NMODL GLOBAL parameter handling in mechanism translation."""
    mechs = {
        "hh": [
            create_acc.Location(name="gnabar", value="0.10000000000000001"),
            create_acc.RangeIExpr(
                name="gkbar",
                value="0.029999999999999999",
                scale=(
                    "(add (scalar -0.62109375) (mul (scalar 0.546875) "
                    "(log (add (mul (distance (region \"soma\"))"
                    " (scalar 0.421875) ) (scalar 1.25) ) ) ) )"
                ),
            ),
        ],
        "pas": [
            create_acc.Location(name="e", value="0.25"),
            create_acc.RangeIExpr(
                name="g",
                value="0.029999999999999999",
                scale=(
                    "(add (scalar -0.62109375) (mul (scalar 0.546875) "
                    "(log (add (mul (distance (region \"soma\"))"
                    " (scalar 0.421875) ) (scalar 1.25) ) ) ) )"
                ),
            ),
        ],
    }
    nmodl_formatter = ArbNmodlMechFormatter(None)
    translated_mechs = nmodl_formatter.translate_density(mechs)
    assert translated_mechs.keys() == {"default::hh",
                                       "default::pas/e=0.25"}
    assert translated_mechs["default::hh"] == mechs["hh"]
    assert translated_mechs["default::pas/e=0.25"] == mechs["pas"][1:]


@pytest.mark.unit
def test_arb_populate_label_dict():
    """Unit test for _populate_label_dict."""
    local_mechs = {ArbLabel("region", "all", "(all)"): {}}
    local_scaled_mechs = {
        ArbLabel("region", "first_branch", "(branch 0)"): {}}
    pprocess_mechs = {}

    label_dict = create_acc._arb_populate_label_dict(local_mechs,
                                                     local_scaled_mechs,
                                                     pprocess_mechs)
    assert label_dict.keys() == {"all", "first_branch"}

    with pytest.raises(create_acc.CreateAccException):
        other_pprocess_mechs = {
            ArbLabel("region", "first_branch", "(branch 1)"): {}}
        create_acc._arb_populate_label_dict(local_mechs,
                                            local_scaled_mechs,
                                            other_pprocess_mechs)


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
        test_labels_filename = pathlib.Path(test_dir).joinpath(label_dict_acc)
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

    with open(testdata_dir / 'acc/CCell/simple_axon_replacement.acc') as f:
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
def test_cell_model_write_and_read_acc():
    """ephys.create_acc: Test write_acc and read_acc w/o axon replacement"""
    cell = make_cell(replace_axon=False)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with tempfile.TemporaryDirectory() as acc_dir:
        cell.write_acc(acc_dir, param_values)
        cell_json, arb_morph, arb_decor, arb_labels = \
            create_acc.read_acc(
                pathlib.Path(acc_dir).joinpath(cell.name + '.json'))
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


@pytest.mark.unit
def test_cell_model_write_and_read_acc_replace_axon():
    """ephys.create_acc: Test write_acc and read_acc w/ axon replacement"""
    cell = make_cell(replace_axon=True)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with tempfile.TemporaryDirectory() as acc_dir:
        try:
            nrn_sim = ephys.simulators.NrnSimulator()
            cell.write_acc(acc_dir, param_values,
                           sim=nrn_sim)
        except Exception as e:  # fail with an older Arbor version
            assert isinstance(e, NotImplementedError)
            assert len(e.args) == 1 and e.args[0] == \
                "Need a newer version of Arbor for axon replacement."
            return
        finally:
            cell.destroy(nrn_sim)

        # Axon replacement implemented in installed Arbor version
        cell_json, arb_morph, arb_decor, arb_labels = \
            create_acc.read_acc(
                pathlib.Path(acc_dir).joinpath(cell.name + '.json'))

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


@pytest.mark.unit
def test_cell_model_create_acc_replace_axon_without_instantiate():
    """ephys.create_acc: Test write_acc and read_acc w/ axon replacement"""
    cell = make_cell(replace_axon=True)
    param_values = {'gnabar_hh': 0.1,
                    'gkbar_hh': 0.03}

    with pytest.raises(ValueError,
                       match='Need an instance of NrnSimulator in sim'
                             ' to instantiate morphology in order to'
                             ' create JSON/ACC-description with'
                             ' axon replacement.'):
        cell.create_acc(param_values)


def check_acc_dir(test_dir, ref_dir):
    assert os.listdir(ref_dir) == os.listdir(test_dir)

    for file in os.listdir(ref_dir):
        if file.endswith('.json'):
            with open(os.path.join(test_dir, file)) as f:
                cell_json_dict = json.load(f)
            with open(ref_dir / file) as f:
                ref_cell_json = json.load(f)
            for k in ref_cell_json:
                if k != 'produced_by':
                    assert ref_cell_json[k] == cell_json_dict[k]
        else:
            with open(os.path.join(test_dir, file)) as f:
                test_file = f.read()
            with open(ref_dir / file) as f:
                ref_file = f.read()
            assert ref_file == test_file


@pytest.mark.unit
def test_write_acc_simple():
    SIMPLECELL_PATH = str((pathlib.Path(__file__).parent /
                          '../../../examples/simplecell').resolve())
    sys.path.insert(0, SIMPLECELL_PATH)
    ref_dir = (testdata_dir / 'acc/simplecell').resolve()
    old_cwd = os.getcwd()
    try:
        os.chdir(SIMPLECELL_PATH)
        import simplecell_model
        param_values = {
            'gnabar_hh': 0.10299326453483033,
            'gkbar_hh': 0.027124836082684685
        }

        cell = simplecell_model.create(do_replace_axon=True)
        nrn_sim = ephys.simulators.NrnSimulator()
        cell.instantiate_morphology_3d(nrn_sim)

        with tempfile.TemporaryDirectory() as test_dir:
            cell.write_acc(test_dir,
                           param_values,
                           # ext_catalogues=ext_catalogues,
                           create_mod_morph=True)

            check_acc_dir(test_dir, ref_dir)
    except Exception as e:  # fail with an older Arbor version
        assert isinstance(e, NotImplementedError)
        assert len(e.args) == 1 and e.args[0] == \
            "Need a newer version of Arbor for axon replacement."
    finally:
        cell.destroy(nrn_sim)
        os.chdir(old_cwd)
        sys.path.pop(0)


@pytest.mark.unit
def test_write_acc_l5pc():
    L5PC_PATH = str((pathlib.Path(__file__).parent /
                    '../../../examples/l5pc').resolve())
    sys.path.insert(0, L5PC_PATH)
    ref_dir = (testdata_dir / 'acc/l5pc').resolve()
    old_cwd = os.getcwd()
    try:
        import l5pc_model
        param_values = {
            'gNaTs2_tbar_NaTs2_t.apical': 0.026145,
            'gSKv3_1bar_SKv3_1.apical': 0.004226,
            'gImbar_Im.apical': 0.000143,
            'gNaTa_tbar_NaTa_t.axonal': 3.137968,
            'gK_Tstbar_K_Tst.axonal': 0.089259,
            'gamma_CaDynamics_E2.axonal': 0.002910,
            'gNap_Et2bar_Nap_Et2.axonal': 0.006827,
            'gSK_E2bar_SK_E2.axonal': 0.007104,
            'gCa_HVAbar_Ca_HVA.axonal': 0.000990,
            'gK_Pstbar_K_Pst.axonal': 0.973538,
            'gSKv3_1bar_SKv3_1.axonal': 1.021945,
            'decay_CaDynamics_E2.axonal': 287.198731,
            'gCa_LVAstbar_Ca_LVAst.axonal': 0.008752,
            'gamma_CaDynamics_E2.somatic': 0.000609,
            'gSKv3_1bar_SKv3_1.somatic': 0.303472,
            'gSK_E2bar_SK_E2.somatic': 0.008407,
            'gCa_HVAbar_Ca_HVA.somatic': 0.000994,
            'gNaTs2_tbar_NaTs2_t.somatic': 0.983955,
            'decay_CaDynamics_E2.somatic': 210.485284,
            'gCa_LVAstbar_Ca_LVAst.somatic': 0.000333,
        }

        cell = l5pc_model.create(do_replace_axon=True)
        nrn_sim = ephys.simulators.NrnSimulator()
        cell.instantiate_morphology_3d(nrn_sim)

        with tempfile.TemporaryDirectory() as test_dir:
            cell.write_acc(test_dir,
                           param_values,
                           # ext_catalogues=ext_catalogues,
                           create_mod_morph=True)

            check_acc_dir(test_dir, ref_dir)
    except Exception as e:  # fail with an older Arbor version
        assert isinstance(e, NotImplementedError)
        assert len(e.args) == 1 and e.args[0] == \
            "Need a newer version of Arbor for axon replacement."
    finally:
        cell.destroy(nrn_sim)
        os.chdir(old_cwd)
        sys.path.pop(0)


@pytest.mark.unit
def test_write_acc_expsyn():
    EXPSYN_PATH = str((pathlib.Path(__file__).parent /
                      '../../../examples/expsyn').resolve())
    sys.path.insert(0, EXPSYN_PATH)
    ref_dir = (testdata_dir / 'acc/expsyn').resolve()
    old_cwd = os.getcwd()
    try:
        import expsyn
        param_values = {'expsyn_tau': 10.0}

        cell = expsyn.create_model(sim='arb', do_replace_axon=False)

        with tempfile.TemporaryDirectory() as test_dir:
            cell.write_acc(test_dir,
                           param_values,
                           # ext_catalogues=ext_catalogues,
                           create_mod_morph=True)

            check_acc_dir(test_dir, ref_dir)
    finally:
        os.chdir(old_cwd)
        sys.path.pop(0)
