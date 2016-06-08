"""Cell template class"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


# pylint: disable=W0511

# TODO take into account that one might want to run protocols on different
# machines
# TODO rename this to 'CellModel' -> definitely

import collections
import os

from bluepyopt.ephys import morphologies

import logging
logger = logging.getLogger(__name__)


class Model(object):

    """Model"""

    def __init__(self, name):
        """Constructor
        Args:
            name (str): name of the model
        """
        self.name = name

    def instantiate(self, sim=None):
        """Instantiate model in simulator"""
        pass

    def destroy(self, sim=None):
        """Destroy instantiated model in simulator"""
        pass


class CellModel(Model):

    """Cell model class"""

    def __init__(
            self,
            name,
            morph=None,
            mechs=None,
            params=None):
        """Constructor

        Args:
            name (str): name of this object
            morph (Morphology):
                underlying Morphology of the cell
            mechs (list of Mechanisms):
                Mechanisms associated with the cell
            params (list of Parameters):
                Parameters of the cell model
        """
        super(CellModel, self).__init__(name)
        self.morphology = morph
        self.mechanisms = mechs
        self.params = collections.OrderedDict()
        for param in params:
            self.params[param.name] = param

        # Cell instantiation in simulator
        self.icell = None

        self.param_values = None

    def params_by_names(self, param_names):
        """Get parameter objects by name"""

        return [self.params[param_name] for param_name in param_names]

    def freeze(self, param_dict):
        """Set params"""

        for param_name, param_value in param_dict.items():
            self.params[param_name].freeze(param_value)

    def unfreeze(self, param_names):
        """Unset params"""

        for param_name in param_names:
            self.params[param_name].unfreeze()

    @staticmethod
    def create_empty_template(template_name):
        '''create an hoc template named template_name for an empty cell'''
        return '''\
        begintemplate %(template_name)s
          objref all, apical, basal, somatic, axonal, this, CellRef
          proc init() {
            all = new SectionList()
            somatic = new SectionList()
            basal = new SectionList()
            apical = new SectionList()
            axonal = new SectionList()
            forall delete_section()
            CellRef = this
          }
          create soma[1], dend[1], apic[1], axon[1]
        endtemplate %(template_name)s
               ''' % dict(template_name=template_name)

    @staticmethod
    def create_empty_cell(name, sim):
        """Create an empty cell in Neuron"""

        # TODO minize hardcoded definition
        # E.g. sectionlist can be procedurally generated
        hoc_template = CellModel.create_empty_template(name)
        sim.neuron.h(hoc_template)

        template_function = getattr(sim.neuron.h, name)

        return template_function()

    def instantiate(self, sim=None):
        """Instantiate model in simulator"""

        # TODO replace this with the real template name
        if not hasattr(sim.neuron.h, 'Cell'):
            self.icell = self.create_empty_cell('Cell', sim=sim)
        else:
            self.icell = sim.neuron.h.Cell()

        self.morphology.instantiate(sim=sim, icell=self.icell)

        for mechanism in self.mechanisms:
            mechanism.instantiate(sim=sim, icell=self.icell)
        for param in self.params.values():
            param.instantiate(sim=sim, icell=self.icell)

    def destroy(self, sim=None):  # pylint: disable=W0613
        """Destroy instantiated model in simulator"""

        self.icell = None
        self.morphology.destroy()
        for mechanism in self.mechanisms:
            mechanism.destroy()
        for param in self.params.values():
            param.destroy()

    def check_nonfrozen_params(self, param_names):  # pylint: disable=W0613
        """Check if all nonfrozen params are set"""

        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    'CellModel: Nonfrozen param %s needs to be '
                    'set before simulation' %
                    param_name)

    def __str__(self):
        """Return string representation"""

        content = '%s:\n' % self.name

        content += '  morphology:\n'
        content += '    %s\n' % str(self.morphology)

        content += '  mechanisms:\n'
        for mechanism in self.mechanisms:
            content += '    %s\n' % mechanism
        content += '  params:\n'
        for param in self.params.values():
            content += '    %s\n' % param

        return content


def load_hoc_template(sim, hoc_path):
    '''have neuron load a hoc file, and detect what the name template name is

    Note: this may fail if there is a begintemplate in a /* */ style comment

    The template must have an init that takes two parameters, the second of
    which is the path to a morphology.

    It must also have a CellRef member that is the result of
        `Import3d_GUI(...).instantiate()`
    '''
    with open(hoc_path) as fd:
        for i, line in enumerate(fd):
            if 'begintemplate' in line:
                line = line.strip().split()
                assert line[0] == 'begintemplate', \
                    'begintemplate must come first, line %d' % i
                template_name = line[1]
                logger.info('Found template %s on line %d', template_name, i)
                break
        else:
            raise Exception('Could not find begintemplate in hoc file')

    if not hasattr(sim.neuron.h, template_name):
        sim.neuron.h.load_file(hoc_path)
        assert hasattr(sim.neuron.h, template_name), \
            'NEURON does not have template: ' + template_name

    return template_name


class HocCellModel(CellModel):

    '''Wrapper class for a hoc template so it can be used by BluePyOpt'''
    class Morphology(morphologies.Morphology):

        '''wrapper for Morphology so that it has a morphology_path'''

        # TODO refactor this
        # we shouldn't have nested classes, problematic for pickling

        def __init__(self, morphology_path):
            super(HocCellModel.Morphology, self).__init__()
            if not os.path.exists(morphology_path):
                raise Exception('HocCellModel: Morphology not found at: %s'
                                % morphology_path)
            self.morphology_path = morphology_path

    def __init__(self, name, morphology_path, hoc_path):
        """Constructor

        Args:
            name(str): name of this object
            sim(NrnSimulator): simulator in which to instatiate hoc_path
            morphology_path(str path): path to morphology that can be loaded by
                                       Neuron
            hoc_path(str path): path to .hoc file that will be used
        """
        super(HocCellModel, self).__init__(name,
                                           morph=None,
                                           mechs=[],
                                           params=[])
        self.hoc_path = hoc_path
        self.morphology = HocCellModel.Morphology(morphology_path)
        self.cell = None
        self.icell = None

    def params_by_names(self, param_names):
        pass

    def freeze(self, param_dict):
        pass

    def unfreeze(self, param_names):
        pass

    def instantiate(self, sim=None):
        template_name = load_hoc_template(sim, self.hoc_path)
        morph_path = self.morphology.morphology_path
        self.cell = getattr(sim.neuron.h, template_name)(0, morph_path)
        self.icell = self.cell.CellRef

    def destroy(self, sim=None):
        self.cell = None
        self.icell = None

    def check_nonfrozen_params(self, param_names):
        pass

    def __str__(self):
        """Return string representation"""
        return ('%s: %s of %s(%s)' %
                (self.__class__, self.name, self.hoc_path,
                 self.morphology.morphology_path, ))
