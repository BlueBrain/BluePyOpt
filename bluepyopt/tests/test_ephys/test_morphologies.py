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
simpleswc_ax1_morphpath = os.path.join(testdata_dir, 'simple_ax1.swc')
simpleswc_ax2_morphpath = os.path.join(testdata_dir, 'simple_ax2.asc')
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

    morph = ephys.morphologies.NrnFileMorphology('wrong.swc')
    nt.assert_raises(IOError, morph.instantiate, sim=sim)

    morph = ephys.morphologies.NrnFileMorphology(simplewrong_morphpath)

    nt.assert_equal(str(morph), simplewrong_morphpath)

    nt.assert_raises(ValueError, morph.instantiate, sim=sim)

    morph = ephys.morphologies.NrnFileMorphology(
        simpleswc_morphpath,
        do_set_nseg=False)

    morph.instantiate(sim=sim)
    morph.destroy(sim=sim)


@attr('unit')
def test_nrnfilemorphology_replace_axon():
    """ephys.morphologies: testing NrnFileMorphology replace_axon"""
    sim = ephys.simulators.NrnSimulator()

    morph = ephys.morphologies.NrnFileMorphology(
        simpleswc_morphpath,
        do_replace_axon=True)

    cell = ephys.models.CellModel(name='cell_replace')
    icell = cell.create_empty_cell(
        cell.name,
        sim=sim,
        seclist_names=cell.seclist_names,
        secarray_names=cell.secarray_names)

    morph.instantiate(sim=sim, icell=icell)

    nt.assert_equal(len([sec for sec in icell.axon]), 2)

    morph.destroy(sim=sim)
    icell.destroy()


@attr('unit')
def test_nrnfilemorphology_replace_axon_ax1():
    """ephys.morphologies: testing NrnFileMorphology replace_axon with ax1"""
    sim = ephys.simulators.NrnSimulator()

    morph = ephys.morphologies.NrnFileMorphology(
        simpleswc_ax1_morphpath,
        do_replace_axon=True)

    cell = ephys.models.CellModel(name='cell_ax1')
    icell = cell.create_empty_cell(
        cell.name,
        sim=sim,
        seclist_names=cell.seclist_names,
        secarray_names=cell.secarray_names)

    morph.instantiate(sim=sim, icell=icell)

    nt.assert_equal(len([sec for sec in icell.axon]), 2)

    morph.destroy(sim=sim)
    icell.destroy()


@attr('unit')
def test_nrnfilemorphology_replace_axon_ax2():
    """ephys.morphologies: testing NrnFileMorphology replace_axon with ax2"""
    sim = ephys.simulators.NrnSimulator()

    morph = ephys.morphologies.NrnFileMorphology(
        simpleswc_ax2_morphpath,
        do_replace_axon=True)

    cell = ephys.models.CellModel(name='cell_ax2')
    icell = cell.create_empty_cell(
        cell.name,
        sim=sim,
        seclist_names=cell.seclist_names,
        secarray_names=cell.secarray_names)

    morph.instantiate(sim=sim, icell=icell)

    nt.assert_equal(len([sec for sec in icell.axon]), 2)

    morph.destroy(sim=sim)
    icell.destroy()


@attr('unit')
def test_serialize():
    """ephys.morphology: testing serialization"""

    morph = ephys.morphologies.NrnFileMorphology(simpleswc_morphpath)
    serialized = morph.to_dict()
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.morphologies.NrnFileMorphology))
    nt.eq_(deserialized.morphology_path, simpleswc_morphpath)
