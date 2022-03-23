"""Test neuroml functions"""

import os
import sys

import neuroml
import pytest
from bluepyopt.neuroml import biophys
from bluepyopt.neuroml import morphology

L5PC_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../examples/l5pc")
)

sys.path.insert(0, L5PC_PATH)

import l5pc_model  # NOQA

l5pc_cell = l5pc_model.create()

release_params = {
    "gNaTs2_tbar_NaTs2_t.apical": 0.026145,
    "gSKv3_1bar_SKv3_1.apical": 0.004226,
    "gImbar_Im.apical": 0.000143,
    "gNaTa_tbar_NaTa_t.axonal": 3.137968,
    "gK_Tstbar_K_Tst.axonal": 0.089259,
    "gamma_CaDynamics_E2.axonal": 0.002910,
    "gNap_Et2bar_Nap_Et2.axonal": 0.006827,
    "gSK_E2bar_SK_E2.axonal": 0.007104,
    "gCa_HVAbar_Ca_HVA.axonal": 0.000990,
    "gK_Pstbar_K_Pst.axonal": 0.973538,
    "gSKv3_1bar_SKv3_1.axonal": 1.021945,
    "decay_CaDynamics_E2.axonal": 287.198731,
    "gCa_LVAstbar_Ca_LVAst.axonal": 0.008752,
    "gamma_CaDynamics_E2.somatic": 0.000609,
    "gSKv3_1bar_SKv3_1.somatic": 0.303472,
    "gSK_E2bar_SK_E2.somatic": 0.008407,
    "gCa_HVAbar_Ca_HVA.somatic": 0.000994,
    "gNaTs2_tbar_NaTs2_t.somatic": 0.983955,
    "decay_CaDynamics_E2.somatic": 210.485284,
    "gCa_LVAstbar_Ca_LVAst.somatic": 0.000333,
}


@pytest.mark.unit
def test_get_nml_mech_dir():
    """biophys.get_nml_mech_dir: Test get_nml_mech_dir"""
    channels = [
        "Ih",
        "NaTa_t",
        "NaTs2_t",
        "Nap_Et2",
        "K_Tst",
        "K_Pst",
        "SKv3_1",
        "SK_E2",
        "StochKv_deterministic",
        "KdShu2007",
        "Im",
        "Ca",
        "Ca_HVA",
        "Ca_LVAst",
        "pas",
    ]

    for channel in channels:
        assert os.path.isfile(
            os.path.join(biophys.get_nml_mech_dir(), f"{channel}.channel.nml")
        )
    assert os.path.isfile(
        os.path.join(biophys.get_nml_mech_dir(), "baseCaDynamics_E2_NML2.nml")
    )


@pytest.mark.unit
def test_get_channel_from_param_name():
    """biophys.get_channel_from_param_name: Test get_channel_from_param_name"""
    # 3 underscores case
    assert biophys.get_channel_from_param_name("gNaTs2_tbar_NaTs2_t") == "NaTs2_t"
    # 2 underscores case
    assert biophys.get_channel_from_param_name("gamma_CaDynamics_E2") == "CaDynamics_E2"
    # 1 underscore case
    assert biophys.get_channel_from_param_name("gIhbar_Ih") == "Ih"


@pytest.mark.unit
def test_format_dist_fun():
    """biophys.format_dist_fun: Test format_dist_fun"""
    raw_expr = "(-0.8696 + 2.087*math.exp(({distance})*0.0031))*{value}"
    formatted_expr = "(-0.8696 + 2.087*exp(p*0.0031))*8e-05"
    assert biophys.format_dist_fun(raw_expr, 8e-05, None) == formatted_expr


@pytest.mark.unit
def test_add_nml_channel_to_nml_cell_file():
    """biophys.add_nml_channel_to_nml_cell_file: Test add_nml_channel_to_nml_cell_file"""
    empty_cell_doc = neuroml.NeuroMLDocument(id="test_nml_cell")
    included_channels = []

    pytest.raises(
        ValueError,
        biophys.add_nml_channel_to_nml_cell_file,
        empty_cell_doc,
        included_channels,
    )

    channel_name = "K_Pst"
    biophys.add_nml_channel_to_nml_cell_file(
        empty_cell_doc,
        included_channels,
        channel_name=channel_name,
        skip_channels_copy=True,
    )
    assert len(empty_cell_doc.includes) == 1
    assert channel_name in str(empty_cell_doc.includes[0].href)
    assert len(included_channels) == 1
    assert f"{channel_name}.channel.nml" in included_channels

    # test that we cannot add the same channel twice
    biophys.add_nml_channel_to_nml_cell_file(
        empty_cell_doc,
        included_channels,
        channel_name=channel_name,
        skip_channels_copy=True,
    )
    assert len(empty_cell_doc.includes) == 1
    assert len(included_channels) == 1


@pytest.mark.unit
def test_get_arguments():
    """biophys.get_arguments: Test get_arguments"""
    parameter_name = "gSKv3_1bar_SKv3_1"
    section_list = "somatic"
    channel = "SKv3_1"
    variable_parameters = None
    cond_density = "0.303472 S_per_cm2"
    arguments, channel_class = biophys.get_arguments(
        l5pc_cell.params,
        parameter_name,
        section_list,
        channel,
        channel,
        variable_parameters,
        cond_density,
        release_params,
    )
    assert arguments["ion"] == "k"
    assert arguments["segment_groups"] == section_list
    assert arguments["erev"] == "-85.0 mV"
    assert arguments["id"] == "somatic_gSKv3_1bar_SKv3_1"
    assert arguments["ion_channel"] == channel
    assert arguments["cond_density"] == cond_density
    assert "variable_parameters" not in arguments
    assert channel_class == "ChannelDensity"

    # pas case
    parameter_name = "g_pas"
    section_list = "all"
    channel = "pas"
    cond_density = "3e-05 S_per_cm2"
    arguments, channel_class = biophys.get_arguments(
        l5pc_cell.params,
        parameter_name,
        section_list,
        channel,
        channel,
        variable_parameters,
        cond_density,
        release_params,
    )
    assert arguments["ion"] == "non_specific"
    assert arguments["segment_groups"] == section_list
    assert arguments["erev"] == "-75 mV"
    assert arguments["id"] == "all_g_pas"
    assert arguments["ion_channel"] == channel
    assert arguments["cond_density"] == cond_density
    assert "variable_parameters" not in arguments
    assert channel_class == "ChannelDensity"

    # nernst case
    parameter_name = "gCa_HVAbar_Ca_HVA"
    section_list = "axonal"
    channel = "Ca_HVA"
    cond_density = "0.00099 S_per_cm2"
    arguments, channel_class = biophys.get_arguments(
        l5pc_cell.params,
        parameter_name,
        section_list,
        channel,
        channel,
        variable_parameters,
        cond_density,
        release_params,
    )
    assert arguments["ion"] == "ca"
    assert arguments["segment_groups"] == section_list
    assert "erev" not in arguments
    assert arguments["id"] == "axonal_gCa_HVAbar_Ca_HVA"
    assert arguments["ion_channel"] == channel
    assert arguments["cond_density"] == cond_density
    assert "variable_parameters" not in arguments
    assert channel_class == "ChannelDensityNernst"


@pytest.mark.unit
def test_extract_parameter_value():
    """biophys.extract_parameter_value: Test extract_parameter_value"""
    # uniform parameter case
    param_name = "gSKv3_1bar_SKv3_1"
    section_list = "apical"
    channel = "SKv3_1"
    cond_density, variable_parameters = biophys.extract_parameter_value(
        l5pc_cell.params[".".join((param_name, section_list))], section_list, channel, True, release_params
    )
    assert cond_density == "0.004226 S_per_cm2"
    assert variable_parameters is None

    # skipped non uniform parameter case
    param_name = "gIhbar_Ih"
    section_list = "apical"
    channel = "Ih"
    cond_density, variable_parameters = biophys.extract_parameter_value(
        l5pc_cell.params[".".join((param_name, section_list))], section_list, channel, True, release_params
    )
    assert cond_density is None
    assert variable_parameters is None

    # non uniform parameter case (unskipped)
    param_name = "gIhbar_Ih"
    section_list = "apical"
    channel = "Ih"
    cond_density, variable_parameters = biophys.extract_parameter_value(
        l5pc_cell.params[".".join((param_name, section_list))], section_list, channel, False, release_params
    )
    assert cond_density is None
    assert variable_parameters[0].segment_groups == section_list
    assert variable_parameters[0].parameter == "condDensity"
    assert (
        variable_parameters[0].inhomogeneous_value.inhomogeneous_parameters
        == "PathLengthOver_apical"
    )
    assert (
        variable_parameters[0].inhomogeneous_value.value
        == "(-0.8696 + 2.087*exp(p*0.0031))*8e-05"
    )


@pytest.mark.unit
def test_get_density():
    """biophys.get_density: Test get_density"""
    empty_cell_doc = neuroml.NeuroMLDocument(id="test_nml_cell")
    param_name = "gSK_E2bar_SK_E2"
    section_list = "axonal"
    density, channel_class = biophys.get_density(
        empty_cell_doc,
        l5pc_cell,
        l5pc_cell.params[".".join((param_name, section_list))],
        section_list,
        included_channels=[],
        skip_non_uniform=True,
        release_params=release_params,
        skip_channels_copy=True,
    )

    assert channel_class == "ChannelDensity"
    assert density.id == "axonal_gSK_E2bar_SK_E2"
    assert density.ion_channel == "SK_E2"
    assert density.cond_density == "0.007104 S_per_cm2"
    assert density.erev == "-85.0 mV"
    assert density.segment_groups == "axonal"
    assert density.ion == "k"


@pytest.mark.unit
def test_get_specific_capacitance():
    """biophys.get_specific_capacitance: Test get_specific_capacitance"""
    # case: default
    specific_capacitances = biophys.get_specific_capacitance({})
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="axonal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="somatic") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="basal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="apical") in specific_capacitances

    # case: all
    specific_capacitances = biophys.get_specific_capacitance({"all": "2.0 uF_per_cm2"})
    assert neuroml.SpecificCapacitance(value="2.0 uF_per_cm2", segment_groups="axonal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="2.0 uF_per_cm2", segment_groups="somatic") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="2.0 uF_per_cm2", segment_groups="basal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="2.0 uF_per_cm2", segment_groups="apical") in specific_capacitances

    # case: specific section(s)
    specific_capacitances = biophys.get_specific_capacitance(
        {"somatic": "2.0 uF_per_cm2", "axonal": "3.0 uF_per_cm2"}
    )
    assert neuroml.SpecificCapacitance(value="3.0 uF_per_cm2", segment_groups="axonal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="2.0 uF_per_cm2", segment_groups="somatic") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="basal") in specific_capacitances
    assert neuroml.SpecificCapacitance(value="1.0 uF_per_cm2", segment_groups="apical") in specific_capacitances


@pytest.mark.unit
def test_get_biophys():
    """biophys.get_biophys: Test get_biophys"""
    empty_cell_doc = neuroml.NeuroMLDocument(id="test_nml_cell")
    bio_prop = biophys.get_biophys(
        l5pc_cell,
        empty_cell_doc,
        release_params,
        skip_non_uniform=True,
        skip_channels_copy=True,
    )

    assert bio_prop.id == "biophys"
    assert bio_prop.membrane_properties.init_memb_potentials[0].value == "-65 mV"
    assert len(bio_prop.membrane_properties.specific_capacitances) == 4
    assert len(bio_prop.membrane_properties.channel_density_nernsts) == 4
    assert len(bio_prop.membrane_properties.channel_densities) == 15
    assert bio_prop.intracellular_properties.resistivities[0].value == "100 ohm_cm"
    assert len(bio_prop.intracellular_properties.species) == 2


@pytest.mark.unit
def test_add_segment_groups():
    """morphology.add_segment_groups: Test add_segment_groups"""
    # creates a neuroml cell with a morphology
    cell = neuroml.Cell(id="nml_cell")
    morph = neuroml.Morphology(id="test_nml_cell_morph")
    for loc in ["soma", "axon", "dend", "apic"]:
        seg = neuroml.Segment(id=0, name=loc)
        morph.segments.append(seg)
    cell.morphology = morph

    morphology.add_segment_groups(cell)
    segment_group_names = [group.id for group in cell.morphology.segment_groups]
    assert "somatic" in segment_group_names
    assert "axonal" in segment_group_names
    assert "basal" in segment_group_names
    assert "apical" in segment_group_names
    assert "soma_group" in segment_group_names
    assert "axon_group" in segment_group_names
    assert "dendrite_group" in segment_group_names
