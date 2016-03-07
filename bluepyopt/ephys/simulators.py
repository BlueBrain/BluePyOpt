"""Simulator classes"""

import os
import imp
import ctypes

import logging
logger = logging.getLogger(__name__)


class NrnSimulator(object):

    """Neuron simulator"""

    def __init__(self):
        """Constructor"""

        hoc_so = os.path.join(imp.find_module('neuron')[1] + '/hoc.so')

        nrndll = ctypes.cdll[hoc_so]
        ctypes.c_int.in_dll(nrndll, 'nrn_nobanner_').value = 1

        import neuron  # NOQA

    @property
    def neuron(self):
        """Return neuron module"""
        import neuron
        return neuron

    def run(self, tstop=None, cvode_active=True):
        """Run protocol"""

        self.neuron.h.tstop = tstop
        self.neuron.h.cvode_active(1 if cvode_active else 0)
        logger.debug('Running Neuron simulator %.6g ms', tstop)
        self.neuron.h.run()
        logger.debug('Neuron simulation finished')
