"""Tests for ephys.mechanisms"""

import string
import random
import json

import nose.tools as nt
from nose.plugins.attrib import attr

import utils
from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


@attr('unit')
def test_mechanism_serialize():
    """ephys.mechanisms: Testing serialize"""
    mech = utils.make_mech()
    serialized = mech.to_dict()
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.mechanisms.NrnMODMechanism))


@attr('unit')
def test_string_hash_functions():
    """ephys.mechanisms: Testing string hash function"""

    nrn_sim = ephys.simulators.NrnSimulator()

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
        (test_string, nrn_sim) for test_string in test_strings]

    nt.assert_equal(hashes_py, hashes_hoc)
    nt.assert_equal(hashes_py[:3], [0.0, 97.0, 504588430.0])
