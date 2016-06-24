"""ephys/morphologies.py unit tests"""

import json
import os

import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys
from bluepyopt.ephys.serializer import instantiator

testdata_dir = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'testdata')

simpleswc_morphpath = os.path.join(testdata_dir, 'simple.swc')
simplewrong_morphpath = os.path.join(testdata_dir, 'simple.wrong')


@attr('unit')
def test_morphology_init():
    """ephys.morphologies: testing Morphology constructor"""

    morph = ephys.morphologies.Morphology()
    nt.assert_is_instance(morph, ephys.morphologies.Morphology)


@attr('unit')
def test_nrnfilemorphology_init():
    """ephys.morphologies: testing NrnFileMorphology constructor"""
    sim = ephys.simulators.NrnSimulator()

    # morph = ephys.morphologies.NrnFileMorphology(simple_morphpath)
    # nt.assert_is_instance(morph, ephys.morphologies.NrnFileMorphology)

    morph = ephys.morphologies.NrnFileMorphology('wrong.swc')
    nt.assert_raises(IOError, morph.instantiate, sim=sim)

    morph = ephys.morphologies.NrnFileMorphology(simplewrong_morphpath)
    nt.assert_raises(ValueError, morph.instantiate, sim=sim)

    morph = ephys.morphologies.NrnFileMorphology(
        simpleswc_morphpath,
        do_set_nseg=False)
    morph.instantiate(sim=sim)
    morph.destroy(sim=sim)


def test_serialize():
    """ephys.morphology: testing serialization"""

    morph = ephys.morphologies.NrnFileMorphology(simpleswc_morphpath)
    serialized = morph.to_dict()
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.morphologies.NrnFileMorphology))
    nt.eq_(deserialized.morphology_path, simpleswc_morphpath)
