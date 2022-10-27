"""Unit tests for the neuron_to_arbor module."""

import pytest

from bluepyopt.ephys.acc.neuron_to_arbor import (
    Nrn2ArbAdapter,
    _arb_nmodl_translate_mech,
    _arb_nmodl_translate_density,
    _find_mech_and_convert_param_name,
    _arb_convert_params_and_group_by_mech_global,
    _arb_convert_params_and_group_by_mech_local,
    RangeIExpr
)
from bluepyopt.ephys.acc import create_acc
from bluepyopt.ephys.create_hoc import RangeExpr, PointExpr, Location


@pytest.mark.unit
def test_nrn2arbor_adapter_name():
    """Test the Nrn2ArbAdapter's name adapter."""
    nonmapped_name = "gSKv3_1bar_SKv3_1"
    assert Nrn2ArbAdapter.var_name(nonmapped_name) == nonmapped_name
    mapped_name = "v_init"
    assert Nrn2ArbAdapter.var_name(mapped_name) == "membrane-potential"


@pytest.mark.unit
def test_nrn2arbor_adapter_value():
    """Test the Nrn2ArbAdapter's value adapter."""
    nonmapped_loc = Location(name="gSKv3_1bar_SKv3_1", value=65)
    mapped_loc = Location(name="v_init", value=-65)
    mapped_loc_with_conv = Location(name="celsius", value=0)

    assert Nrn2ArbAdapter.var_value(nonmapped_loc) == 65
    assert Nrn2ArbAdapter.var_value(mapped_loc) == -65
    assert Nrn2ArbAdapter.var_value(mapped_loc_with_conv) == "273.14999999999998"


@pytest.mark.unit
def test_nrn2arbor_adapter_parameter():
    """Test the Nrn2ArbAdapter's parameter adapter."""
    location_param = Location(name="gSKv3_1bar_SKv3_1", value=65)
    range_expr_param = RangeExpr(
        location="ArbLabel_obj",
        name="gkbar_hh",
        value=0.03,
        value_scaler="NrnSegmentSomaDistanceScaler_obj",
    )
    point_expr_param = PointExpr(name="gkbar_hh", value=0.03, point_loc="pl")
    assert (
        Nrn2ArbAdapter.parameter(location_param, name=location_param.name)
        == location_param
    )
    assert (
        Nrn2ArbAdapter.parameter(range_expr_param, name=range_expr_param.name)
        == range_expr_param
    )
    assert (
        Nrn2ArbAdapter.parameter(point_expr_param, name=point_expr_param.name)
        == point_expr_param
    )


@pytest.mark.unit
def test_nrn2arbor_mech_name():
    """Test the Nrn2ArbAdapter's mechanism name adapter."""
    assert Nrn2ArbAdapter.mech_name("Ca_HVA") == "Ca_HVA"
    assert Nrn2ArbAdapter.mech_name("ExpSyn") == "expsyn"


@pytest.mark.unit
def test__arb_nmodl_translate_mech():
    """Unit test for the _arb_nmodl_translate_mech function."""
    mech_name = "hh"
    mech_params = [
        Location(name="gnabar", value="0.10000000000000001"),
        RangeIExpr(
            name="gkbar",
            value="0.029999999999999999",
            scale=(
                "(add (scalar -0.62109375) (mul (scalar 0.546875) "
                '(log (add (mul (distance (region "soma")) (scalar 0.421875) ) '
                "(scalar 1.25) ) ) ) )"
            ),
        ),
    ]
    arb_cats = create_acc._arb_load_mech_catalogue_meta(None)
    result = _arb_nmodl_translate_mech(mech_name, mech_params, arb_cats)
    assert result[0] == 'default::hh'
    assert result[1][0] == mech_params[0]
    assert result[1][1] == mech_params[1]


@pytest.mark.unit
def test_arb_nmodl_translate_density():
    """Unit test for the _arb_nmodl_translate_density function."""
    mechs = {None: [Location(name='gSKv3_1bar_SKv3_1', value=65)]}
    arb_cats = create_acc._arb_load_mech_catalogue_meta(None)
    result = _arb_nmodl_translate_density(mechs, arb_cats)
    assert result == mechs


@pytest.mark.unit
def test_find_mech_and_convert_param_name():
    """Unit test for the _find_mech_and_convert_param_name function."""
    param = Location(name='gSKv3_1bar_SKv3_1', value=65)
    mechs = []
    result = _find_mech_and_convert_param_name(param, mechs)
    assert result == (None, Location(name='gSKv3_1bar_SKv3_1', value=65))


@pytest.mark.unit
def test_arb_convert_params_and_group_by_mech_global():
    """Unit test for the _arb_convert_params_and_group_by_mech function."""
    params = {'gSKv3_1bar_SKv3_1': 65}
    result = _arb_convert_params_and_group_by_mech_global(params)
    assert result == {None: [Location(name='gSKv3_1bar_SKv3_1', value=65)]}
