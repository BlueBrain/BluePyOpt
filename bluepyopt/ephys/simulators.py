"""Simulator classes"""

# pylint: disable=W0511

import os
import logging
import imp
import ctypes
import platform
import warnings

logger = logging.getLogger(__name__)


class NrnSimulator(object):

    """Neuron simulator"""

    def __init__(self, dt=None, cvode_active=True, cvode_minstep=None,
                 random123_globalindex=None, mechanisms_directory=None):
        """Constructor

        Args:
            dt (float): the integration time step used by neuron.
            cvode_active (bool): should neuron use the variable time step
                integration method
            cvode_minstep (float): the minimum time step allowed for a cvode
                step. Default is 0.0.
            random123_globalindex (int): used to set the global index used by
                all instances of the Random123 instances of Random
            mechanisms_directory (str): path to the parent directory of the
                directory containing the mod files. If the mod files are in
                "./data/mechanisms", then mechanisms_directory should be
                "./data/".
        """

        # hoc.so does not exist on NEURON Windows or MacOS
        # although \\hoc.pyd can work here, it gives an error for
        # nrn_nobanner_ line
        self.disable_banner = platform.system() not in ['Windows', 'Darwin']
        self.banner_disabled = False
        self.mechanisms_directory = mechanisms_directory
        self.neuron.h.load_file('stdrun.hoc')

        self.dt = dt if dt is not None else self.neuron.h.dt
        self.neuron.h.dt = self.dt

        self.neuron.h.cvode_active(1 if cvode_active else 0)
        self.cvode_minstep_value = cvode_minstep

        self.cvode_active = cvode_active

        self.random123_globalindex = random123_globalindex

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

    @staticmethod
    def _nrn_disable_banner():
        """Disable Neuron banner"""

        nrnpy_path = os.path.join(imp.find_module('neuron')[1])
        import glob
        hoc_so_list = \
            glob.glob(os.path.join(nrnpy_path, 'hoc*.so'))

        if len(hoc_so_list) != 1:
            warnings.warn('Unable to find Neuron hoc shared library in %s, '
                          'not disabling banner' % nrnpy_path)
        else:
            hoc_so = hoc_so_list[0]
            nrndll = ctypes.cdll[hoc_so]
            ctypes.c_int.in_dll(nrndll, 'nrn_nobanner_').value = 1

    # pylint: disable=R0201
    @property
    def neuron(self):
        """Return neuron module"""

        if self.disable_banner and not self.banner_disabled:
            NrnSimulator._nrn_disable_banner()
            self.banner_disabled = True

        import neuron  # NOQA

        if self.mechanisms_directory is not None:
            neuron.load_mechanisms(
                self.mechanisms_directory, warn_if_already_loaded=False
            )

        return neuron

    def check_voltage_valid(self, icell, voltage_bound=200.):
        """Raises exception if voltage at soma is out of bound"""

        if icell and abs(icell.soma[0](0.5).v) > voltage_bound:
            raise NrnSimulatorException('Membrane potential is out of bound')

    def run(
            self,
            tstop=None,
            dt=None,
            cvode_active=None,
            random123_globalindex=None,
            icell=None):
        """Run protocol"""

        self.neuron.h.tstop = tstop

        if cvode_active and dt is not None:
            raise ValueError(
                'NrnSimulator: Impossible to combine the dt argument when '
                'cvode_active is True in the NrnSimulator run method')

        if cvode_active is None:
            cvode_active = self.cvode_active

        if not cvode_active and dt is None:  # use dt of simulator
            if self.neuron.h.dt != self.dt:
                raise Exception(
                    'NrnSimulator: Some process has changed the '
                    'time step dt of Neuron since the creation of this '
                    'NrnSimulator object. Not sure this is intended:\n'
                    'current dt: %.6g\n'
                    'init dt: %.6g' % (self.neuron.h.dt, self.dt))
            dt = self.dt

        self.neuron.h.cvode_active(1 if cvode_active else 0)
        if self.cvode_minstep_value is not None:
            save_minstep = self.cvode_minstep
            self.cvode_minstep = self.cvode_minstep_value

        if cvode_active:
            logger.debug('Running Neuron simulator %.6g ms, with cvode', tstop)
        else:
            self.neuron.h.dt = dt
            self.neuron.h.steps_per_ms = 1.0 / dt
            logger.debug(
                'Running Neuron simulator %.6g ms, with dt=%r',
                tstop,
                dt)

        if random123_globalindex is None:
            random123_globalindex = self.random123_globalindex

        if random123_globalindex is not None:
            rng = self.neuron.h.Random()
            rng.Random123_globalindex(random123_globalindex)

        try:
            self.neuron.h.finitialize()
            while self.neuron.h.t < self.neuron.h.tstop:
                self.neuron.h.fadvance()
                self.check_voltage_valid(icell)
        except Exception as e:
            raise NrnSimulatorException('Neuron simulator error', e)

        if self.cvode_minstep_value is not None:
            self.cvode_minstep = save_minstep

        logger.debug('Neuron simulation finished')


class NrnSimulatorException(Exception):

    """All exception generated by Neuron simulator"""

    def __init__(self, message, original):
        """Constructor"""

        super(NrnSimulatorException, self).__init__(message)
        self.original = original
