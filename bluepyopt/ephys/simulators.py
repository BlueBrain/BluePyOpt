"""Simulator classes"""

import logging
logger = logging.getLogger(__name__)


class NrnSimulator(object):

    """Neuron simulator"""

    @property
    def neuron(self):
        """Return neuron module"""
        from .importer import neuron  # NOQA
        return neuron

    def run(self, tstop=None, cvode_active=True):
        """Run protocol"""

        self.neuron.h.tstop = tstop
        self.neuron.h.cvode_active(1 if cvode_active else 0)
        logger.debug('Running Neuron simulator %.6g ms', tstop)
        self.neuron.h.run()
        logger.debug('Neuron simulation finished')
