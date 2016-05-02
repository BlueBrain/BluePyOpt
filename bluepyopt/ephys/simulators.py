"""Simulator classes"""

import os
import logging
logger = logging.getLogger(__name__)


class NrnSimulator(object):

    """Neuron simulator"""

    def __init__(self, dt=0.025, cvode_active=True):
        """Constructor"""

        import imp
        import ctypes

        hoc_so = os.path.join(imp.find_module('neuron')[1] + '/hoc.so')

        nrndll = ctypes.cdll[hoc_so]
        ctypes.c_int.in_dll(nrndll, 'nrn_nobanner_').value = 1

        self.dt = dt
        self.cvode_active = cvode_active

    @property
    def neuron(self):
        """Return neuron module"""

        import neuron  # NOQA

        return neuron

    def run(self, tstop=None, cvode_active=None, dt=None):
        """Run protocol"""

        self.neuron.h.tstop = tstop

        if cvode_active is None:  # use cvode_active of simulator
            cvode_active = self.cvode_active

        self.neuron.h.cvode_active(1 if cvode_active else 0)

        if dt is None:  # use dt of simulator
            dt = self.dt

        if cvode_active:
            logger.debug('Running Neuron simulator %.6g ms, with cvode', tstop)
        else:
            self.neuron.h.dt = dt
            self.neuron.h.steps_per_ms = 1.0 / dt
            logger.debug(
                'Running Neuron simulator %.6g ms, with dt=%r',
                tstop,
                dt)

        self.neuron.h.run()
        logger.debug('Neuron simulation finished')
