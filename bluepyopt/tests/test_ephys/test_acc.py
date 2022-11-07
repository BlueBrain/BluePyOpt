"""Unit tests for acc."""

from bluepyopt.ephys.acc import arbor, ArbLabel


import pytest


@pytest.mark.unit
def test_arbor_labels():
    """Test Arbor labels."""

    region_label = ArbLabel(type='region',
                            name='first_branch',
                            s_expr='(branch 0)')

    assert region_label.defn == '(region-def "first_branch" (branch 0))'
    assert region_label.ref == '(region "first_branch")'
    assert region_label.name == 'first_branch'
    assert region_label.loc == '(branch 0)'
    assert region_label == region_label
    assert region_label is not None

    locset_label = ArbLabel(type='locset',
                            name='first_branch_center',
                            s_expr='(location 0 0.5)')

    assert locset_label.defn == \
        '(locset-def "first_branch_center" (location 0 0.5))'
    assert locset_label.ref == '(locset "first_branch_center")'
    assert locset_label.name == 'first_branch_center'
    assert locset_label.loc == '(location 0 0.5)'
    assert locset_label == locset_label
    assert locset_label is not None

    assert locset_label != region_label

    arbor.label_dict({region_label.name: region_label.loc,
                      locset_label.name: locset_label.loc})
