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
# TODO rename this to 'CellModel' ?

import collections
import textwrap
import logging

import bluepyopt as bpopt

logger = logging.getLogger(__name__)


class CellTemplate(object):

    """Simple cell class"""

    def __init__(
            self,
            name,
            morph=None,
            mechs=None,
            params=None):
        """Constructor"""

        self.name = name

        self.morphology = morph
        self.mechanisms = mechs

        # Model params
        self.params = collections.OrderedDict()
        self.params = dict((param.name, param) for param in params)

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
        template_content = textwrap.dedent('''\
            begintemplate %s
                objref all, apical, basal, somatic, axonal
                proc init() {
                    all = new SectionList()
                    somatic = new SectionList()
                    basal = new SectionList()
                    apical = new SectionList()
                    axonal = new SectionList()
                    forall delete_section()
                }
                create soma[1], dend[1], apic[1], axon[1]
            endtemplate %s''') % (name=name)

        bpopt.neuron.h(template_content)

        template_function = getattr(bpopt.neuron.h, name)

        return template_function()

    def instantiate(self):
        """Instantiate model in simulator"""

        bpopt.neuron.h.load_file('stdrun.hoc')

        # TODO replace this with the real template name
        if not hasattr(bpopt.neuron.h, 'Cell'):
            self.icell = self.create_empty_cell('Cell')
        else:
            self.icell = bpopt.neuron.h.Cell()

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

        bpopt.neuron.h.tstop = protocol.total_duration
        bpopt.neuron.h.cvode_active(1)
        logger.debug('Running protocol %s for %.6g ms', protocol.name, protocol.total_duration)
        bpopt.neuron.h.run()
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

        #TODO: list all non-frozen parameters
        for param_name, param in self.params.items():
            if not param.frozen:
                raise Exception(
                    'CellTemplate: Nonfrozen param %s needs to be '
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
                            'CellTemplate: response name used twice: %s' %
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
        INDENT = ' ' * 2
        lines = []

        def out(indent_count, string):
            '''add output to lines'''
            lines.append(INDENT * indent_count + string)

        add(0, self.name + ':')
        add(1, 'morphology:')
        add(2, str(self.morphology))

        add(1, 'mechanisms:')
        for mechanism in self.mechanisms:
            add(2, str(mechanism))

        add(1, 'params:')
        for param in self.params.values():
            add(2, str(param))

        return '\n'.join(lines)
