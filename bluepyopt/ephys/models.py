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
import logging

from .importer import neuron

logger = logging.getLogger(__name__)


class CellModel(object):

    """Cell model class"""

    def __init__(
            self,
            name,
            morph=None,
            mechs=None,
            params=None):
        """Constructor"""

        self.name = name

        # morphology
        self.morphology = morph
        # mechanisms
        self.mechanisms = mechs
        # Model params
        self.params = collections.OrderedDict()
        for param in params:
            self.params[param.name] = param

        # Cell instantiation in simulator
        self.icell = None

        self.param_values = None

    def freeze(self, param_values):
        """Set params"""

        for param_name, param_value in param_values.items():
            param = self.params[param_name]
            param.freeze(param_value)

    def unfreeze(self, param_names):
        """Unset params"""

        for param_name in param_names:
            self.params[param_name].unfreeze()

    @staticmethod
    def create_empty_cell(name):
        """Create an empty cell in Neuron"""

        # TODO minize hardcoded definition
        # E.g. sectionlist can be procedurally generated
        template_content = 'begintemplate %s\n' \
            'objref all, apical, basal, somatic, axonal\n' \
            'proc init() {\n' \
            'all 	= new SectionList()\n' \
            'somatic = new SectionList()\n' \
            'basal 	= new SectionList()\n' \
            'apical 	= new SectionList()\n' \
            'axonal 	= new SectionList()\n' \
            'forall delete_section()\n' \
            '}\n' \
            'create soma[1], dend[1], apic[1], axon[1]\n' \
            'endtemplate %s\n' % (name, name)

        neuron.h(template_content)

        template_function = getattr(neuron.h, name)

        return template_function()

    def instantiate(self):
        """Instantiate model in simulator"""

        neuron.h.load_file('stdrun.hoc')

        # TODO replace this with the real template name
        if not hasattr(neuron.h, 'Cell'):
            self.icell = self.create_empty_cell('Cell')
        else:
            self.icell = neuron.h.Cell()

        self.morphology.instantiate(self)

        for mechanism in self.mechanisms:
            mechanism.instantiate(self)
        for param in self.params.values():
            param.instantiate(self)

    # TODO This should also get param_values as argument, and original
    # function renamed
    def run_protocol(self, protocol):
        """Run protocol"""

        self.instantiate()
        protocol.instantiate(self)

        neuron.h.tstop = protocol.total_duration
        neuron.h.cvode_active(1)
        logger.debug(
            'Running protocol %s for %.6g ms',
            protocol.name,
            protocol.total_duration)
        neuron.h.run()
        responses = protocol.responses

        protocol.destroy()
        self.destroy()

        logger.debug('Protocol finished, returning responses')
        return responses

    def destroy(self):
        """Destroy instantiated model in simulator"""

        self.icell = None
        self.morphology.destroy()
        for mechanism in self.mechanisms:
            mechanism.destroy()
        for param in self.params.values():
            param.destroy()

    def check_nonfrozen_params(self, param_names):
        """Check if all nonfrozen params are set"""

        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    'CellModel: Nonfrozen param %s needs to be '
                    'set before simulation' %
                    param_name)

    def run_protocols(self, protocols, param_values=None):
        """Run stimulus protocols"""

        # TODO Put all of this in a decorator ?
        import traceback
        import sys
        try:
            self.freeze(param_values)

            self.check_nonfrozen_params(param_values.keys())

            responses = {}
            for protocol in protocols.itervalues():
                protocol_responses = self.run_protocol(protocol)
                for response_name, response in protocol_responses.iteritems():
                    if response_name in responses:
                        raise Exception(
                            'CellModel: response name used twice: %s' %
                            response.name)
                    responses[response_name] = response

            self.unfreeze(param_values.keys())
        except:
            raise Exception(
                "".join(
                    traceback.format_exception(
                        *
                        sys.exc_info())))

        return responses

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
