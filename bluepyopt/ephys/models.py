"""Cell template class"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

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

import sys
import os
import collections
import string

from . import create_hoc, create_acc
from . import morphologies

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
        params=None,
        gid=0,
        seclist_names=None,
        secarray_names=None
    ):
        """Constructor

        Args:
            name (str): name of this object
                        should be alphanumeric string, underscores are allowed,
                        first char should be a letter
            morph (Morphology):
                underlying Morphology of the cell
            mechs (list of Mechanisms):
                Mechanisms associated with the cell
            params (list of Parameters):
                Parameters of the cell model
            seclist_names (list of strings):
                Names of the lists of sections
            secarray_names (list of strings):
                Names of the sections
        """

        super(CellModel, self).__init__(name)

        self.check_name()
        self.morphology = morph
        self.mechanisms = mechs
        self.params = collections.OrderedDict()
        if params is not None:
            for param in params:
                self.params[param.name] = param

        # Cell instantiation in simulator
        self.icell = None
        self.icell_existing_secs = None

        self.param_values = None
        self.gid = gid

        if seclist_names is None:
            self.seclist_names = [
                'all', 'somatic', 'basal', 'apical', 'axonal', 'myelinated'
            ]
        else:
            self.seclist_names = seclist_names

        if secarray_names is None:
            self.secarray_names = [
                'soma', 'dend', 'apic', 'axon', 'myelin'
            ]
        else:
            self.secarray_names = secarray_names

    def check_name(self):
        """Check if name complies with requirements"""

        allowed_chars = string.ascii_letters + string.digits + '_'

        if sys.version_info[0] < 3:
            translate_args = [None, allowed_chars]
        else:
            translate_args = [str.maketrans('', '', allowed_chars)]

        if self.name == '' \
                or self.name[0] not in string.ascii_letters \
                or not str(self.name).translate(*translate_args) == '':
            raise TypeError(
                'CellModel: name "%s" provided to constructor does not comply '
                'with the rules for Neuron template name: name should be '
                'alphanumeric '
                'non-empty string, underscores are allowed, '
                'first char should be letter' % self.name)

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
    def create_empty_template(
            template_name,
            seclist_names=None,
            secarray_names=None):
        '''create an hoc template named template_name for an empty cell'''

        objref_str = 'objref this, CellRef'
        newseclist_str = ''

        if seclist_names:
            for seclist_name in seclist_names:
                objref_str += ', %s' % seclist_name
                newseclist_str += \
                    '             %s = new SectionList()\n' % seclist_name

        create_str = ''
        if secarray_names:
            create_str = 'create '
            create_str += ', '.join(
                '%s[1]' % secarray_name
                for secarray_name in secarray_names)
            create_str += '\n'

        template = '''\
        begintemplate %(template_name)s
          %(objref_str)s
          proc init() {\n%(newseclist_str)s
            forall delete_section()
            CellRef = this
          }

          gid = 0

          proc destroy() {localobj nil
            CellRef = nil
          }

          %(create_str)s
        endtemplate %(template_name)s
               ''' % dict(template_name=template_name, objref_str=objref_str,
                          newseclist_str=newseclist_str,
                          create_str=create_str)
        return template

    @staticmethod
    def create_empty_cell(
            name,
            sim,
            seclist_names=None,
            secarray_names=None):
        """Create an empty cell in Neuron"""

        # TODO minize hardcoded definition
        # E.g. sectionlist can be procedurally generated
        hoc_template = CellModel.create_empty_template(
            name,
            seclist_names,
            secarray_names)
        sim.neuron.h(hoc_template)

        template_function = getattr(sim.neuron.h, name)

        return template_function()

    def instantiate_morphology(self, sim=None):
        """Instantiate morphology in simulator"""

        # TODO replace this with the real template name
        if not hasattr(sim.neuron.h, self.name):
            self.icell = self.create_empty_cell(
                self.name,
                sim=sim,
                seclist_names=self.seclist_names,
                secarray_names=self.secarray_names)
        else:
            self.icell = getattr(sim.neuron.h, self.name)()

        self.icell.gid = self.gid

        self.morphology.instantiate(sim=sim, icell=self.icell)

        self.icell_existing_secs = [
            sec for sec in self.secarray_names
            if sim.neuron.h.section_exists(sec, self.icell)]

    def instantiate_morphology_3d(self, sim=None):
        """Instantiate morphology and fill in 3d pts for stylized geometry"""

        self.instantiate_morphology(sim=sim)
        sim.neuron.h.define_shape()

    def instantiate(self, sim=None):
        """Instantiate model in simulator"""

        self.instantiate_morphology(sim)

        if self.mechanisms is not None:
            for mechanism in self.mechanisms:
                mechanism.instantiate(sim=sim, icell=self.icell)

        if self.params is not None:
            for param in self.params.values():
                param.instantiate(sim=sim, icell=self.icell,
                                  params=self.params)

    def destroy(self, sim=None):  # pylint: disable=W0613
        """Destroy instantiated model in simulator"""

        # Make sure the icell's destroy() method is called
        # without it a circular reference exists between CellRef and the object
        # this prevents the icells from being garbage collected, and
        # cell objects pile up in the simulator
        self.icell.destroy()

        # The line below is some M. Hines magic
        # DON'T remove it, because it will make sure garbage collection
        # is called on the icell object
        sim.neuron.h.Vector().size()

        self.icell = None
        self.icell_existing_secs = None

        self.morphology.destroy(sim=sim)
        for mechanism in self.mechanisms:
            mechanism.destroy(sim=sim)
        for param in self.params.values():
            param.destroy(sim=sim)

    def check_nonfrozen_params(self, param_names):  # pylint: disable=W0613
        """Check if all nonfrozen params are set"""

        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    'CellModel: Nonfrozen param %s needs to be '
                    'set before simulation' %
                    param_name)

    def _create_sim_desc(self, param_values,
                         ignored_globals=(), template=None,
                         disable_banner=False,
                         template_dir=None,
                         extra_params=None,
                         sim_desc_creator=None):
        """Create simulator description for this model"""

        to_unfreeze = []
        for param in self.params.values():
            if not param.frozen:
                param.freeze(param_values[param.name])
                to_unfreeze.append(param.name)

        template_name = self.name
        morphology = os.path.basename(self.morphology.morphology_path)

        if sim_desc_creator is create_hoc.create_hoc:
            if self.morphology.do_replace_axon:
                replace_axon = self.morphology.replace_axon_hoc
            else:
                replace_axon = None

            if (
                self.morphology.morph_modifiers is not None
                and self.morphology.morph_modifiers_hoc is None
            ):
                logger.warning('You have provided custom morphology'
                               ' modifiers, but no corresponding hoc files.')
            elif (
                self.morphology.morph_modifiers is not None
                and self.morphology.morph_modifiers_hoc is not None
            ):
                if replace_axon is None:
                    replace_axon = ''
                for morph_modifier_hoc in self.morphology.morph_modifiers_hoc:
                    replace_axon += '\n'
                    replace_axon += morph_modifier_hoc
        elif sim_desc_creator is create_acc.create_acc:
            if self.morphology.do_replace_axon:

                replace_axon = morphologies.\
                    ArbFileMorphology.extract_nrn_seclists(
                        self.icell, [sl for sl in ['axon', 'myelin']
                                     if sl in self.icell_existing_secs])

            else:
                replace_axon = None
        else:
            raise ValueError('Unsupported sim_desc_creator %s '
                             '(choose either create_hoc.create_hoc or '
                             'create_acc.create_acc)', str(sim_desc_creator))

        if extra_params is None:
            extra_params = dict()

        ret = sim_desc_creator(mechs=self.mechanisms,
                               parameters=self.params.values(),
                               morphology=morphology,
                               ignored_globals=ignored_globals,
                               replace_axon=replace_axon,
                               template_name=template_name,
                               template_filename=template,
                               template_dir=template_dir,
                               disable_banner=disable_banner,
                               **extra_params)

        self.unfreeze(to_unfreeze)

        return ret

    def create_hoc(self, param_values,
                   ignored_globals=(), template='cell_template.jinja2',
                   disable_banner=False,
                   template_dir=None):
        """Create hoc code for this model"""
        return self._create_sim_desc(param_values,
                                     ignored_globals, template,
                                     disable_banner,
                                     template_dir,
                                     sim_desc_creator=create_hoc.create_hoc)

    def create_acc(self, param_values,
                   ignored_globals=(), template='acc/*_template.jinja2',
                   disable_banner=False,
                   template_dir=None,
                   ext_catalogues=None,
                   create_mod_morph=False,
                   sim=None):
        """Create JSON/ACC-description for this model"""
        destroy_cell = False
        if self.morphology.do_replace_axon:
            if self.icell is None:
                if sim is None:
                    raise ValueError('Need an instance of NrnSimulator in sim'
                                     ' to instantiate morphology in order to'
                                     ' create JSON/ACC-description with'
                                     ' axon replacement.')
                self.instantiate_morphology_3d(sim=sim)
                destroy_cell = True

        extra_params = dict(
            morphology_dir=os.path.dirname(self.morphology.morphology_path),
            create_mod_morph=create_mod_morph,
            ext_catalogues=ext_catalogues
        )

        ret = self._create_sim_desc(param_values,
                                    ignored_globals, template,
                                    disable_banner,
                                    template_dir,
                                    extra_params=extra_params,
                                    sim_desc_creator=create_acc.create_acc)

        if destroy_cell:
            self.destroy(sim=sim)
        return ret

    def write_acc(self, output_dir, param_values,
                  template_filename='acc/*_template.jinja2',
                  ext_catalogues=None,
                  create_mod_morph=False,
                  sim=None):
        """Write JSON/ACC-description for this model to output directory"""
        create_acc.write_acc(output_dir, self, param_values,
                             template_filename=template_filename,
                             ext_catalogues=ext_catalogues,
                             create_mod_morph=create_mod_morph,
                             sim=sim)

    def __str__(self):
        """Return string representation"""

        content = '%s:\n' % self.name

        content += '  morphology:\n'

        if self.morphology is not None:
            content += '    %s\n' % str(self.morphology)

        content += '  mechanisms:\n'
        if self.mechanisms is not None:
            for mechanism in self.mechanisms:
                content += '    %s\n' % mechanism

        content += '  params:\n'
        if self.params is not None:
            for param in self.params.values():
                content += '    %s\n' % param

        return content


class HocMorphology(morphologies.Morphology):

    '''wrapper for Morphology so that it has a morphology_path'''

    def __init__(self, morphology_path):
        super(HocMorphology, self).__init__()
        if not os.path.exists(morphology_path):
            raise Exception('HocCellModel: Morphology not found at: %s'
                            % morphology_path)
        self.morphology_path = morphology_path


class HocCellModel(CellModel):

    '''Wrapper class for a hoc template so it can be used by BluePyOpt'''

    def __init__(self, name, morphology_path, hoc_path=None, hoc_string=None):
        """Constructor

        Args:
            name(str): name of this object
            sim(NrnSimulator): simulator in which to instatiate hoc_string
            hoc_path(str): Path to a hoc file
                (hoc_path and hoc_string can't be used simultaneously,
                but one of them has to specified)
            hoc_string(str): String that of hoc code that defines a template
                (hoc_path and hoc_string can't be used simultaneously,
                but one of them has to specified))
            morphology_path(str path): path to morphology that can be loaded by
                                       Neuron
        """
        super(HocCellModel, self).__init__(name,
                                           morph=None,
                                           mechs=[],
                                           params=[])

        if hoc_path is not None and hoc_string is not None:
            raise TypeError('HocCellModel: cant specify both hoc_string '
                            'and hoc_path argument')
        if hoc_path is not None:
            with open(hoc_path) as hoc_file:
                self.hoc_string = hoc_file.read()
        else:
            self.hoc_string = hoc_string

        self.morphology = HocMorphology(morphology_path)
        self.cell = None
        self.icell = None

    def params_by_names(self, param_names):
        pass

    def freeze(self, param_dict):
        pass

    def unfreeze(self, param_names):
        pass

    def instantiate(self, sim=None):
        sim.neuron.h.load_file('stdrun.hoc')
        template_name = self.load_hoc_template(sim, self.hoc_string)

        morph_path = self.morphology.morphology_path
        assert os.path.exists(morph_path), \
            'Morphology path does not exist: %s' % morph_path
        if os.path.isdir(morph_path):
            # will use the built in morphology name, if the init() only
            # gets one parameter
            self.cell = getattr(sim.neuron.h, template_name)(morph_path)
        else:
            morph_dir = os.path.dirname(morph_path)
            morph_name = os.path.basename(morph_path)
            self.cell = getattr(sim.neuron.h, template_name)(morph_dir,
                                                             morph_name)
        self.icell = self.cell.CellRef

    def destroy(self, sim=None):
        self.cell = None
        self.icell = None

    def check_nonfrozen_params(self, param_names):
        pass

    def __str__(self):
        """Return string representation"""
        return (
            '%s: %s of %s(%s)' %
            (self.__class__,
             self.name,
             self.get_template_name(self.hoc_string),
             self.morphology.morphology_path,))

    @staticmethod
    def get_template_name(hoc_string):
        """Find the template name from hoc_string

        Note: this will fail if there is a begintemplate in a `/* */` style
        comment before the real begintemplate
        """
        for i, line in enumerate(hoc_string.split('\n')):
            if 'begintemplate' in line:
                line = line.strip().split()
                assert line[0] == 'begintemplate', \
                    'begintemplate must come first, line %d' % i
                template_name = line[1]
                logger.info('Found template %s on line %d', template_name, i)
                return template_name
        else:  # pylint: disable=W0120
            raise Exception('Could not find begintemplate in hoc file')

    @staticmethod
    def load_hoc_template(sim, hoc_string):
        """Have neuron hoc template, and detect what the name template name is

        The template must have an init that takes two parameters, the second of
        which is the path to a morphology.

        It must also have a CellRef member that is the result of
            `Import3d_GUI(...).instantiate()`
        """
        template_name = HocCellModel.get_template_name(hoc_string)
        if not hasattr(sim.neuron.h, template_name):
            sim.neuron.h(hoc_string)
            assert hasattr(sim.neuron.h, template_name), \
                'NEURON does not have template: ' + template_name

        return template_name


class LFPyCellModel(Model):

    """LFPy.Cell model class"""

    def __init__(
        self,
        name,
        electrode=None,
        morph=None,
        mechs=None,
        params=None,
        dt=0.025,
        v_init=-65.0,
        gid=0,
        seclist_names=None,
        secarray_names=None,
    ):
        """Constructor

        Args:
            name (str): name of this object
                        should be alphanumeric string, underscores are allowed,
                        first char should be a letter
            morph (Morphology):
                underlying Morphology of the cell
            mechs (list of Mechanisms):
                Mechanisms associated with the cell
            params (list of Parameters):
                Parameters of the cell model
            seclist_names (list of strings):
                Names of the lists of sections
            secarray_names (list of strings):
                Names of the sections
        """
        super(LFPyCellModel, self).__init__(name)
        self.check_name()
        self.morphology = morph
        self.mechanisms = mechs
        self.params = collections.OrderedDict()
        if params is not None:
            for param in params:
                self.params[param.name] = param

        # Cell instantiation in simulator
        self.icell = None
        self.lfpy_cell = None
        self.electrode = electrode
        self.lfpy_electrode = None

        self.dt = dt
        self.v_init = v_init

        self.param_values = None
        self.gid = gid

        if seclist_names is None:
            self.seclist_names = [
                "all",
                "somatic",
                "basal",
                "apical",
                "axonal",
                "myelinated",
            ]
        else:
            self.seclist_names = seclist_names

        if secarray_names is None:
            self.secarray_names = ["soma", "dend", "apic", "axon", "myelin"]
        else:
            self.secarray_names = secarray_names

    def check_name(self):
        """Check if name complies with requirements"""

        allowed_chars = string.ascii_letters + string.digits + "_"

        if sys.version_info[0] < 3:
            translate_args = [None, allowed_chars]
        else:
            translate_args = [str.maketrans("", "", allowed_chars)]

        if (
            self.name == ""
            or self.name[0] not in string.ascii_letters
            or not str(self.name).translate(*translate_args) == ""
        ):
            raise TypeError(
                'CellModel: name "%s" provided to constructor does not comply '
                "with the rules for Neuron template name: name should be "
                "alphanumeric "
                "non-empty string, underscores are allowed, "
                "first char should be letter" % self.name
            )

    def params_by_names(self, param_names):
        """Get parameter objects by name"""

        return [self.params[param_name] for param_name in param_names]

    def freeze(self, param_dict):
        """Set params"""

        for param_name, param_value in param_dict.items():
            self.params[param_name].freeze(param_dict[param_name])

    def unfreeze(self, param_names):
        """Unset params"""

        for param_name in param_names:
            self.params[param_name].unfreeze()

    @staticmethod
    def create_empty_template(
        template_name, seclist_names=None, secarray_names=None
    ):
        """create an hoc template named template_name for an empty cell"""

        objref_str = "objref this, CellRef"
        newseclist_str = ""

        if seclist_names:
            for seclist_name in seclist_names:
                objref_str += ", %s" % seclist_name
                newseclist_str += (
                    "             %s = new SectionList()\n" % seclist_name
                )

        create_str = ""
        if secarray_names:
            create_str = "create "
            create_str += ", ".join(
                "%s[1]" % secarray_name for secarray_name in secarray_names
            )
            create_str += "\n"

        template = """\
        begintemplate %(template_name)s
          %(objref_str)s
          proc init() {\n%(newseclist_str)s
            forall delete_section()
            CellRef = this
          }

          gid = 0

          proc destroy() {localobj nil
            CellRef = nil
          }

          %(create_str)s
        endtemplate %(template_name)s
               """ % dict(
            template_name=template_name,
            objref_str=objref_str,
            newseclist_str=newseclist_str,
            create_str=create_str,
        )

        return template

    @staticmethod
    def create_empty_cell(name, sim, seclist_names=None, secarray_names=None):
        """Create an empty cell in Neuron"""

        # TODO minize hardcoded definition
        # E.g. sectionlist can be procedurally generated
        hoc_template = CellModel.create_empty_template(
            name, seclist_names, secarray_names
        )
        sim.neuron.h(hoc_template)

        template_function = getattr(sim.neuron.h, name)

        return template_function()

    def instantiate(self, sim=None):
        """Instantiate model in simulator"""
        from LFPy import Cell
        from lfpykit import RecExtElectrode

        # TODO replace this with the real template name
        if not hasattr(sim.neuron.h, self.name):
            self.icell = self.create_empty_cell(
                self.name,
                sim=sim,
                seclist_names=self.seclist_names,
                secarray_names=self.secarray_names,
            )
        else:
            self.icell = getattr(sim.neuron.h, self.name)()

        self.icell.gid = self.gid

        self.morphology.instantiate(sim=sim, icell=self.icell)

        self.lfpy_cell = Cell(
            morphology=sim.neuron.h.allsec(),
            dt=self.dt,
            v_init=self.v_init,
            pt3d=True,
            delete_sections=False,
            nsegs_method=None,
        )

        self.lfpy_electrode = RecExtElectrode(
            self.lfpy_cell, probe=self.electrode
        )

        if self.mechanisms is not None:
            for mechanism in self.mechanisms:
                mechanism.instantiate(sim=sim, icell=self.icell)

        if self.params is not None:
            for param in self.params.values():
                param.instantiate(sim=sim, icell=self.icell,
                                  params=self.params)

    def destroy(self, sim=None):  # pylint: disable=W0613
        """Destroy instantiated model in simulator"""

        # Make sure the icell's destroy() method is called
        # without it a circular reference exists between CellRef and the object
        # this prevents the icells from being garbage collected, and
        # cell objects pile up in the simulator
        self.icell.destroy()

        # The line below is some M. Hines magic
        # DON'T remove it, because it will make sure garbage collection
        # is called on the icell object
        sim.neuron.h.Vector().size()

        self.icell = None

        self.morphology.destroy(sim=sim)
        for mechanism in self.mechanisms:
            mechanism.destroy(sim=sim)
        for param in self.params.values():
            param.destroy(sim=sim)

    def check_nonfrozen_params(self, param_names):  # pylint: disable=W0613
        """Check if all nonfrozen params are set"""

        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    "CellModel: Nonfrozen param %s needs to be "
                    "set before simulation" % param_name
                )

    def create_hoc(
        self,
        param_values,
        ignored_globals=(),
        template="cell_template.jinja2",
        disable_banner=False,
        template_dir=None,
    ):
        """Create hoc code for this model"""

        to_unfreeze = []
        for param in self.params.values():
            if not param.frozen:
                param.freeze(param_values[param.name])
                to_unfreeze.append(param.name)

        template_name = self.name
        morphology = os.path.basename(self.morphology.morphology_path)
        if self.morphology.do_replace_axon:
            replace_axon = self.morphology.replace_axon_hoc
        else:
            replace_axon = None

        ret = create_hoc.create_hoc(
            mechs=self.mechanisms,
            parameters=self.params.values(),
            morphology=morphology,
            ignored_globals=ignored_globals,
            replace_axon=replace_axon,
            template_name=template_name,
            template_filename=template,
            template_dir=template_dir,
            disable_banner=disable_banner,
        )

        self.unfreeze(to_unfreeze)

        return ret

    def __str__(self):
        """Return string representation"""

        content = "%s:\n" % self.name

        content += "  morphology:\n"

        if self.morphology is not None:
            content += "    %s\n" % str(self.morphology)

        content += "  mechanisms:\n"
        if self.mechanisms is not None:
            for mechanism in self.mechanisms:
                content += "    %s\n" % mechanism

        content += "  params:\n"
        if self.params is not None:
            for param in self.params.values():
                content += "    %s\n" % param

        return content
