"""Unit tests for acc_label.py."""

from bluepyopt.ephys.acc.acc_label import ArbLabel


def test_arb_label():
    """Test ArbLabel class."""
    _type = "region"
    name = "all"
    defn = "(all)"

    arb = ArbLabel(type=_type, name=name, defn=defn)

    assert arb.defn == '(%s-def "%s" %s)' % (_type, name, defn)
    assert arb.ref == '(%s "%s")' % (_type, name)
    assert arb.name == name
    assert arb.loc == defn
    assert arb == arb
    assert arb is not None
    assert hash(arb) == hash(arb.defn)
    assert repr(arb) == arb.defn
