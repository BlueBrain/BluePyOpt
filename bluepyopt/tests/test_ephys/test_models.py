import os
import tempfile

from os.path import join as joinp

from nose.tools import eq_, ok_
from mock import Mock

from contextlib import contextmanager

from bluepyopt.ephys import models

import neuron

@contextmanager
def yeild_blank_hoc(template_name):
    hoc_template = models.create_empty_template(template_name)
    temp_file = tempfile.NamedTemporaryFile(suffix='test_models')
    with temp_file as fd:
        fd.write(hoc_template)
        fd.flush()
        yield temp_file.name


def test_create_empty_template():
    template_name = 'FakeTemplate'
    hoc_template = models.create_empty_template(template_name)
    neuron.h(hoc_template)
    ok_(hasattr(neuron.h, template_name))


def test_model():
    model = models.Model('test_model')
    model.instantiate(sim=None)
    model.destroy(sim=None)

    ok_(isinstance(model, models.Model))


def test_load_hoc_template():
    sim = Mock()
    sim.neuron = neuron

    template_name = 'test_load_hoc'
    with yeild_blank_hoc(template_name) as hoc_path:
        models.load_hoc_template(sim, hoc_path)
    ok_(hasattr(neuron.h, template_name))


def test_HocCellModel():
    sim = Mock()
    sim.neuron = neuron

    testdata_dir = joinp(os.path.dirname(os.path.abspath(__file__)), 'testdata')
    morphology_path = joinp(testdata_dir, 'simple.swc')
    template_name = 'test_HocCellModel'
    with yeild_blank_hoc(template_name) as hoc_path:
        hoc_cell = models.HocCellModel('test_hoc_model', morphology_path, hoc_path)
        hoc_cell.instantiate(sim)
        ok_(hoc_cell.icell is not None)
        ok_(hoc_cell.cell is not None)

        ok_('simple.swc' in str(hoc_cell))

        #these should be callable, but don't do anything
        hoc_cell.freeze(None)
        hoc_cell.unfreeze(None)
        hoc_cell.check_nonfrozen_params(None)
        hoc_cell.params_by_names(None)

        hoc_cell.destroy()


def test_CellModel_create_empty_cell():
    sim = Mock()
    sim.neuron = neuron
    template_name = 'EmptyModel'
    cell = models.CellModel.create_empty_cell(template_name, sim)
    ok_(callable(cell))
    ok_(hasattr(neuron.h, template_name))
