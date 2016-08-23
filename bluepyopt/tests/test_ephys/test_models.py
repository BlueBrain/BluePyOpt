"""Test ephys model objects"""

import os
import tempfile

from os.path import join as joinp

import nose.tools as nt
from nose.plugins.attrib import attr

from contextlib import contextmanager

import bluepyopt.ephys as ephys

sim = ephys.simulators.NrnSimulator()
TESTDATA_DIR = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
MORPHOLOGY_PATH = joinp(TESTDATA_DIR, 'simple.swc')

test_morph = ephys.morphologies.NrnFileMorphology(MORPHOLOGY_PATH)


@contextmanager
def yield_blank_hoc(template_name):
    """Create blank hoc template"""
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    temp_file = tempfile.NamedTemporaryFile(suffix='test_models')
    with temp_file as fd:
        fd.write(hoc_template.encode('utf-8'))
        fd.flush()
        yield temp_file.name


@attr('unit')
def test_create_empty_template():
    """ephys.models: Test creation of empty template"""
    template_name = 'FakeTemplate'
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    sim.neuron.h(hoc_template)
    nt.assert_true(hasattr(sim.neuron.h, template_name))


@attr('unit')
def test_model():
    """ephys.models: Test Model class"""
    model = ephys.models.Model('test_model')
    model.instantiate(sim=None)
    model.destroy(sim=None)
    nt.assert_true(isinstance(model, ephys.models.Model))


@attr('unit')
def test_cellmodel():
    """ephys.models: Test CellModel class"""
    model = ephys.models.CellModel('test_model', morph=test_morph, mechs=[])
    model.instantiate(sim=sim)
    model.destroy(sim=sim)
    nt.assert_true(isinstance(model, ephys.models.CellModel))


@attr('unit')
def test_cellmodel_namecheck():
    """ephys.models: Test CellModel class name checking"""

    # Test valid name
    for name in ['test3', 'test_3']:
        ephys.models.CellModel(name, morph=test_morph, mechs=[])

    # Test invalid names
    for name in ['3test', '', 'test$', 'test 3']:
        nt.assert_raises(
            TypeError,
            ephys.models.CellModel,
            name,
            morph=test_morph,
            mechs=[])


@attr('unit')
def test_load_hoc_template():
    """ephys.models: Test loading of hoc template"""

    template_name = 'test_load_hoc'
    with yield_blank_hoc(template_name) as hoc_path:
        ephys.models.load_hoc_template(sim, hoc_path)
    nt.assert_true(hasattr(sim.neuron.h, template_name))


@attr('unit')
def test_HocCellModel():
    """ephys.models: Test HOCCellModel class"""
    template_name = 'test_HocCellModel'
    with yield_blank_hoc(template_name) as hoc_path:
        hoc_cell = ephys.models.HocCellModel(
            'test_hoc_model',
            MORPHOLOGY_PATH,
            hoc_path)
        hoc_cell.instantiate(sim)
        nt.assert_true(hoc_cell.icell is not None)
        nt.assert_true(hoc_cell.cell is not None)

        nt.assert_true('simple.swc' in str(hoc_cell))

        # these should be callable, but don't do anything
        hoc_cell.freeze(None)
        hoc_cell.unfreeze(None)
        hoc_cell.check_nonfrozen_params(None)
        hoc_cell.params_by_names(None)

        hoc_cell.destroy(sim=sim)


@attr('unit')
def test_CellModel_create_empty_cell():
    """ephys.models: Test create_empty_cell"""
    template_name = 'create_empty_cell'
    cell = ephys.models.CellModel.create_empty_cell(template_name, sim)
    nt.assert_true(callable(cell))
    nt.assert_true(hasattr(sim.neuron.h, template_name))


@attr('unit')
def test_CellModel_destroy():
    """ephys.models: Test CellModel destroy"""
    morph0 = ephys.morphologies.NrnFileMorphology(MORPHOLOGY_PATH)
    cell_model0 = ephys.models.CellModel('CellModel_destroy',
                                         morph=morph0,
                                         mechs=[],
                                         params=[])
    morph1 = ephys.morphologies.NrnFileMorphology(MORPHOLOGY_PATH)
    cell_model1 = ephys.models.CellModel('CellModel_destroy',
                                         morph=morph1,
                                         mechs=[],
                                         params=[])

    nt.assert_true(not hasattr(sim.neuron.h, 'CellModel_destroy'))

    cell_model0.instantiate(sim=sim)
    nt.assert_true(hasattr(sim.neuron.h, 'CellModel_destroy'))
    nt.assert_equal(1, len(sim.neuron.h.CellModel_destroy))

    cell_model1.instantiate(sim=sim)
    nt.assert_equal(2, len(sim.neuron.h.CellModel_destroy))

    # make sure cleanup works
    cell_model0.destroy(sim=sim)
    nt.assert_equal(1, len(sim.neuron.h.CellModel_destroy))

    cell_model1.destroy(sim=sim)
    nt.assert_equal(0, len(sim.neuron.h.CellModel_destroy))
