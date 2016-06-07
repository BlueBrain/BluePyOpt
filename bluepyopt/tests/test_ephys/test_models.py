"""Test ephys model objects"""

import os
import tempfile

from os.path import join as joinp

import nose.tools as nt
from nose.plugins.attrib import attr

import mock

from contextlib import contextmanager

import bluepyopt.ephys as ephys

import neuron


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
    neuron.h(hoc_template)
    nt.ok_(hasattr(neuron.h, template_name))


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
    sim = mock.Mock()
    sim.neuron = neuron

    template_name = 'test_load_hoc'
    with yield_blank_hoc(template_name) as hoc_path:
        ephys.models.load_hoc_template(sim, hoc_path)
    nt.ok_(hasattr(neuron.h, template_name))


@attr('unit')
def test_HocCellModel():
    """Test HOCCellModel class"""
    sim = mock.Mock()
    sim.neuron = neuron

    testdata_dir = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
    morphology_path = joinp(testdata_dir, 'simple.swc')
    template_name = 'test_HocCellModel'
    with yield_blank_hoc(template_name) as hoc_path:
        hoc_cell = ephys.models.HocCellModel(
            'test_hoc_model',
            morphology_path,
            hoc_path)
        hoc_cell.instantiate(sim)
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
    sim = mock.Mock()
    sim.neuron = neuron
    template_name = 'EmptyModel'
    cell = ephys.models.CellModel.create_empty_cell(template_name, sim)
    nt.ok_(callable(cell))
    nt.ok_(hasattr(neuron.h, template_name))
