"""Tests for ephys.mechanisms"""

import string
import random
import json

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
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.mechanisms.NrnMODMechanism))


@attr('unit')
def test_nrnmod_instantiate():
    """ephys.mechanisms: Testing insert mechanism"""

    test_mech = ephys.mechanisms.NrnMODMechanism(
        'test.pas',
        suffix='pas',
        locations=[simplecell.somatic_loc])

    simple_cell.instantiate(sim=sim)

    test_mech.instantiate(sim=sim, icell=simple_cell.icell)
    test_mech.destroy(sim=sim)

    simple_cell.destroy(sim=sim)


@attr('unit')
def test_pprocess_instantiate():
    """ephys.mechanisms: Testing insert point process"""

    test_pprocess = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[simplecell.somacenter_loc])

    simple_cell.instantiate(sim=sim)

    nt.assert_equal(test_pprocess.pprocesses, None)

    test_pprocess.instantiate(sim=sim, icell=simple_cell.icell)
    nt.assert_equal(len(test_pprocess.pprocesses), 1)
    pprocess = test_pprocess.pprocesses[0]

    nt.assert_true(hasattr(pprocess, 'tau'))

    test_pprocess.destroy(sim=sim)
    nt.assert_equal(test_pprocess.pprocesses, None)

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
