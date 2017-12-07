"""Tests for ephys.mechanisms"""

import string
import random
import json
import difflib

import nose.tools as nt
from nose.plugins.attrib import attr

import utils
from bluepyopt import ephys
import bluepyopt.ephys.examples.simplecell as simplecell

from bluepyopt.ephys.serializer import instantiator

simple_cell = simplecell.cell_model
simple_cell.freeze(simplecell.default_param_values)
sim = simplecell.nrn_sim


@attr('unit')
def test_mechanism_serialize():
    """ephys.mechanisms: Testing serialize"""
    mech = utils.make_mech()
    serialized = mech.to_dict()
    nt.assert_true(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.assert_true(isinstance(deserialized, ephys.mechanisms.NrnMODMechanism))


@attr('unit')
def test_nrnmod_instantiate():
    """ephys.mechanisms: Testing insert mechanism"""

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'test.pas',
        suffix='pas',
        locations=[simplecell.somatic_loc])

    nt.assert_equal(str(test_mech), "test.pas: pas at ['somatic']")

    simple_cell.instantiate(sim=sim)

    test_mech.instantiate(sim=sim, icell=simple_cell.icell)
    test_mech.destroy(sim=sim)

    simple_cell.destroy(sim=sim)

    nt.assert_raises(TypeError, ephys.mechanisms.NrnMODMechanism,
                     'test.pas',
                     suffix='pas',
                     prefix='pas',
                     locations=[simplecell.somatic_loc])

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'test.pas',
        prefix='pas',
        locations=[simplecell.somatic_loc])

    nt.assert_equal(test_mech.suffix, 'pas')

    test_mech.prefix = 'pas2'
    nt.assert_equal(test_mech.suffix, 'pas2')

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'unknown',
        suffix='unknown',
        locations=[simplecell.somatic_loc])

    simple_cell.instantiate(sim=sim)

    nt.assert_raises(
        ValueError,
        test_mech.instantiate,
        sim=sim,
        icell=simple_cell.icell)

    test_mech.destroy(sim=sim)
    simple_cell.destroy(sim=sim)


def compare_strings(s1, s2):
    """Compare two strings"""

    diff = list(difflib.unified_diff(s1.splitlines(1), s2.splitlines(1)))

    if len(diff) > 0:
        print(''.join(diff))
        return False
    else:
        return True


@attr('unit')
def test_nrnmod_reinitrng_block():
    """ephys.mechanisms: Testing reinitrng_block"""

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'stoch',
        suffix='Stoch',
        locations=[simplecell.somatic_loc])

    block = test_mech.generate_reinitrng_hoc_block()
    expected_block = '    forsec somatic { deterministic_Stoch = 1 }\n'

    nt.assert_true(compare_strings(block, expected_block))

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'stoch',
        suffix='Stoch',
        deterministic=False,
        locations=[simplecell.somatic_loc])

    block = test_mech.generate_reinitrng_hoc_block()

    expected_block = \
        """    forsec somatic {
        for (x, 0) {
            setdata_Stoch(x)
            sf.tail(secname(), "\\\\.", name)
            sprint(full_str, "%s.%.19g", name, x)
            if (channel_seed_set) {
                setRNG_Stoch(gid, hash_str(full_str), channel_seed)
            } else {
                setRNG_Stoch(gid, hash_str(full_str))
            }
        }
    }
"""

    nt.assert_true(compare_strings(block, expected_block))


@attr('unit')
def test_nrnmod_determinism():
    """ephys.mechanisms: Testing determinism"""

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'pas',
        suffix='pas',
        deterministic=False,
        locations=[simplecell.somatic_loc])

    simple_cell.instantiate(sim=sim)

    nt.assert_raises(
        TypeError,
        test_mech.instantiate,
        sim=sim,
        icell=simple_cell.icell)
    test_mech.destroy(sim=sim)

    simple_cell.destroy(sim=sim)


@attr('unit')
def test_pprocess_instantiate():
    """ephys.mechanisms: Testing insert point process"""

    test_pprocess = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[simplecell.somacenter_loc])

    nt.assert_equal(
        str(test_pprocess),
        "expsyn: ExpSyn at ['somatic[0](0.5)']")

    simple_cell.instantiate(sim=sim)

    nt.assert_equal(test_pprocess.pprocesses, None)

    test_pprocess.instantiate(sim=sim, icell=simple_cell.icell)
    nt.assert_equal(len(test_pprocess.pprocesses), 1)
    pprocess = test_pprocess.pprocesses[0]

    nt.assert_true(hasattr(pprocess, 'tau'))
    test_pprocess.destroy(sim=sim)

    nt.assert_equal(test_pprocess.pprocesses, None)

    simple_cell.destroy(sim=sim)

    test_pprocess = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='Exp',
        locations=[simplecell.somacenter_loc])

    simple_cell.instantiate(sim=sim)

    nt.assert_raises(
        AttributeError,
        test_pprocess.instantiate,
        sim=sim,
        icell=simple_cell.icell)

    test_pprocess.destroy(sim=sim)
    simple_cell.destroy(sim=sim)


@attr('unit')
def test_string_hash_functions():
    """ephys.mechanisms: Testing string hash function"""

    n_of_strings = 100
    max_size = 50

    random.seed(1)

    test_strings = ['', 'a']
    test_strings += [''.join
                     (random.choice
                      (string.printable)
                      for _ in range(random.choice(range(max_size))))
                     for _ in range(n_of_strings)]
    hashes_py = [
        ephys.mechanisms.NrnMODMechanism.hash_py
        (test_string) for test_string in test_strings]
    hashes_hoc = [
        ephys.mechanisms.NrnMODMechanism.hash_hoc
        (test_string, simplecell.nrn_sim) for test_string in test_strings]

    nt.assert_equal(hashes_py, hashes_hoc)
    nt.assert_equal(hashes_py[:2], [0.0, 97.0])
