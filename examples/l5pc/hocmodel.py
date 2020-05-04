
#from bluepyopt.ephys.models import CellModel
import bglibpy
from bglibpy.importer import neuron

import collections
import logging

logger = logging.getLogger(__name__)


class HocModel(object):

    """Neurodamus model class"""

    def __init__(
            self,
            morphname=None,
            template=None):
        """Constructor"""

        self.name = None

        # morphology
        self.morphology = morphname
        self.template = template

        self.mechanisms = None
        self.params = None

        # Cell instantiation in simulator
        self.icell = None
        self.param_values = None


    def instantiate(self):
        """Instantiate model in simulator"""

        self.cell = bglibpy.Cell(self.template, self.morphology)
        self.name = self.cell.cellname

        #self.sim = bglibpy.Simulation()
        #self.sim.add_cell(cell)

        self.icell = self.cell.cell.getCell()


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


    def run_protocols(self, protocols, param_values=None):
        """Run stimulus protocols"""

        # TODO Put all of this in a decorator ?
        import traceback
        import sys
        try:

            responses = {}
            for protocol in protocols.itervalues():
                protocol_responses = self.run_protocol(protocol)
                for response_name, response in protocol_responses.items():
                    if response_name in responses:
                        raise Exception(
                            'CellModel: response name used twice: %s' %
                            response.name)
                    responses[response_name] = response

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
        content += '    %s\n' % self.morphology

        content += '  template:\n'
        content += '    %s\n' % self.template

        return content
