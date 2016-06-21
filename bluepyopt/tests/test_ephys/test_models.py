"""Test ephys model objects"""

import os
import tempfile

from os.path import join as joinp

import nose.tools as nt
from nose.plugins.attrib import attr

from contextlib import contextmanager

import bluepyopt.ephys as ephys

SIM = ephys.simulators.NrnSimulator()
TESTDATA_DIR = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
MORPHOLOGY_PATH = joinp(TESTDATA_DIR, 'simple.swc')


@contextmanager
def yield_blank_hoc(template_name):
    """Create blank hoc template"""
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    temp_file = tempfile.NamedTemporaryFile(suffix='test_models')
    with temp_file as fd:
        fd.write(hoc_template)
        fd.flush()
        yield temp_file.name


@attr('unit')
def test_create_empty_template():
    """Test creation of empty template"""
    template_name = 'FakeTemplate'
    hoc_template = ephys.models.CellModel.create_empty_template(template_name)
    SIM.neuron.h(hoc_template)
    nt.ok_(hasattr(SIM.neuron.h, template_name))


@attr('unit')
def test_model():
    """Test Model class"""
    model = ephys.models.Model('test_model')
    model.instantiate(sim=None)
    model.destroy(sim=None)
    nt.ok_(isinstance(model, ephys.models.Model))


@attr('unit')
def test_load_hoc_template():
    """Test loading of hoc template"""

    template_name = 'test_load_hoc'
    with yield_blank_hoc(template_name) as hoc_path:
        ephys.models.load_hoc_template(SIM, hoc_path)
    nt.ok_(hasattr(SIM.neuron.h, template_name))


@attr('unit')
def test_HocCellModel():
    """Test HOCCellModel class"""
    template_name = 'test_HocCellModel'
    with yield_blank_hoc(template_name) as hoc_path:
        hoc_cell = ephys.models.HocCellModel(
            'test_hoc_model',
            MORPHOLOGY_PATH,
            hoc_path)
        hoc_cell.instantiate(SIM)
        nt.ok_(hoc_cell.icell is not None)
        nt.ok_(hoc_cell.cell is not None)

        nt.ok_('simple.swc' in str(hoc_cell))

        # these should be callable, but don't do anything
        hoc_cell.freeze(None)
        hoc_cell.unfreeze(None)
        hoc_cell.check_nonfrozen_params(None)
        hoc_cell.params_by_names(None)

        hoc_cell.destroy()


@attr('unit')
def test_CellModel_create_empty_cell():
    """Test create_empty_cell"""
    template_name = 'create_empty_cell'
    cell = ephys.models.CellModel.create_empty_cell(template_name, SIM)
    nt.ok_(callable(cell))
    nt.ok_(hasattr(SIM.neuron.h, template_name))


@attr('unit')
def test_CellModel_destroy():
    """Test CellModel destroy"""
    morph0 = ephys.morphologies.NrnFileMorphology(MORPHOLOGY_PATH)
    cell_model0 = ephys.models.CellModel('CellModel_destroy0',
                                         morph=morph0,
                                         mechs=[],
                                         params=[])
    morph1 = ephys.morphologies.NrnFileMorphology(MORPHOLOGY_PATH)
    cell_model1 = ephys.models.CellModel('CellModel_destroy1',
                                         morph=morph1,
                                         mechs=[],
                                         params=[])

    nt.ok_(not hasattr(SIM.neuron.h, 'Cell'))

    cell_model0.instantiate(sim=SIM)
    nt.ok_(hasattr(SIM.neuron.h, 'Cell'))
    nt.eq_(1, len(SIM.neuron.h.Cell))

    cell_model1.instantiate(sim=SIM)
    nt.eq_(2, len(SIM.neuron.h.Cell))

    #make sure cleanup works
    cell_model0.destroy()

    sf = SIM.neuron.h.StringFunctions()
    sf.references(SIM.neuron.h.Cell)
    nt.eq_(1, len(SIM.neuron.h.Cell))

    cell_model1.destroy()
    sf.references(SIM.neuron.h.Cell)
    nt.eq_(0, len(SIM.neuron.h.Cell))
