"""Simulator classes"""

# pylint: disable=W0511

import os
import logging
import imp
import ctypes
import platform

logger = logging.getLogger(__name__)


class NrnSimulator(object):

    """Neuron simulator"""

    def __init__(self, dt=None, cvode_active=True, cvode_minstep=None):
        """Constructor"""

        self.neuron.h.load_file('stdrun.hoc')

        self.dt = dt if dt is not None else self.neuron.h.dt

        self.neuron.h.cvode_active(1 if cvode_active else 0)
        if cvode_minstep is not None:
            self.cvode_minstep = cvode_minstep

        self.cvode_active = cvode_active

    @property
    def cvode(self):
        """Return cvode instance"""

        return self.neuron.h.CVode()

    @property
    def cvode_minstep(self):
        """Return cvode minstep value"""

        return self.cvode.minstep()

    @cvode_minstep.setter
    def cvode_minstep(self, value):
        """Set cvode minstep value"""

        self.cvode.minstep(value)

    # pylint: disable=R0201
    # TODO function below should probably a class property or something in that
    # sense
    @property
    def neuron(self):
        """Return neuron module"""

        if platform.system() != 'Windows':
            # hoc.so does not exist on NEURON Windows
            # although \\hoc.pyd can work here, it gives an error for
            # nrn_nobanner_ line
            hoc_so = os.path.join(imp.find_module('neuron')[1] + '/hoc.so')
            nrndll = ctypes.cdll[hoc_so]
            ctypes.c_int.in_dll(nrndll, 'nrn_nobanner_').value = 1

        import neuron  # NOQA

        return neuron

    def run(self, tstop=None, dt=None, cvode_active=None):
        """Run protocol"""

        self.neuron.h.tstop = tstop

        if cvode_active and dt is not None:
            raise ValueError(
                'NrnSimulator: Impossible to combine the dt argument when '
                'cvode_active is True in the NrnSimulator run method')

        if cvode_active is None:
            cvode_active = self.cvode_active

        self.neuron.h.cvode_active(1 if cvode_active else 0)

        if not cvode_active and dt is None:  # use dt of simulator
            if self.neuron.h.dt != self.dt:
                raise Exception(
                    'NrnSimulator: Some process has changed the '
                    'time step dt of Neuron since the creation of this '
                    'NrnSimulator object. Not sure this is intended:\n'
                    'current dt: %.6g\n'
                    'init dt: %.6g' % (self.neuron.h.dt, self.dt))
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
