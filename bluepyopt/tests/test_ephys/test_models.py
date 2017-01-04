"""Test ephys model objects"""

import os
import tempfile
import contextlib

import nose.tools as nt
from nose.plugins.attrib import attr

from bluepyopt import ephys

sim = ephys.simulators.NrnSimulator()
TESTDATA_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'testdata')
simple_morphology_path = os.path.join(TESTDATA_DIR, 'simple.swc')


@contextlib.contextmanager
def yield_blank_hoc(template_name):
    """Create blank hoc template"""
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    temp_file = tempfile.NamedTemporaryFile(suffix='test_models')
    with temp_file as fd:
        fd.write(hoc_template.encode('utf-8'))
        fd.flush()
        yield temp_file.name

test_morph = ephys.morphologies.NrnFileMorphology(simple_morphology_path)


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
    hoc_string = ephys.models.CellModel.create_empty_template(template_name)
    ephys.models.HocCellModel.load_hoc_template(sim, hoc_string)
    nt.ok_(hasattr(sim.neuron.h, template_name))


@attr('unit')
def test_HocCellModel():
    """ephys.models: Test HOCCellModel class"""
    template_name = 'test_HocCellModel'
    hoc_string = ephys.models.CellModel.create_empty_template(template_name)
    hoc_cell = ephys.models.HocCellModel(
        'test_hoc_model', simple_morphology_path, hoc_string=hoc_string)
    hoc_cell.instantiate(sim)
    nt.ok_(hoc_cell.icell is not None)
    nt.ok_(hoc_cell.cell is not None)

    nt.ok_('simple.swc' in str(hoc_cell))

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
def test_CellModel_create_hoc():
    """ephys.models: Test create_hoc"""

    morph0 = ephys.morphologies.NrnFileMorphology(
        simple_morphology_path,
        do_replace_axon=True)

    cell_model = ephys.models.CellModel('CellModel',
                                        morph=morph0,
                                        mechs=[],
                                        params=[])

    hoc_string = cell_model.create_hoc({})
    nt.assert_true('begintemplate CellModel' in hoc_string)
    nt.assert_true('proc replace_axon()' in hoc_string)
    cell_model_hoc = ephys.models.HocCellModel(
        'CellModelHOC',
        simple_morphology_path,
        hoc_string=hoc_string)

    nt.assert_true(isinstance(cell_model_hoc, ephys.models.HocCellModel))


@attr('unit')
def test_CellModel_destroy():
    """ephys.models: Test CellModel destroy"""
    morph0 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
    cell_model0 = ephys.models.CellModel('CellModel_destroy',
                                         morph=morph0,
                                         mechs=[],
                                         params=[])
    morph1 = ephys.morphologies.NrnFileMorphology(simple_morphology_path)
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
