"""Simulator classes"""

# pylint: disable=W0511

import ctypes
import importlib.util
import logging
import os
import pathlib
import platform
import warnings

from bluepyopt.ephys.acc import arbor

logger = logging.getLogger(__name__)


class NrnSimulator(object):
    """Neuron simulator"""

    def __init__(
        self,
        dt=None,
        cvode_active=True,
        cvode_minstep=None,
        random123_globalindex=None,
        mechanisms_directory=None,
    ):
        """Constructor

        Args:
            dt (float): the integration time step used by Neuron.
            cvode_active (bool): should Neuron use the variable time step
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
        self.disable_banner = platform.system() not in ["Windows", "Darwin"]
        self.banner_disabled = False
        self.mechanisms_directory = mechanisms_directory

        self.dt = dt if dt is not None else self.neuron.h.dt

        self.cvode_minstep_value = cvode_minstep

        self.cvode_active = cvode_active

        self.initialize()

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

        nrnpy_path = pathlib.Path(
            importlib.util.find_spec("neuron").origin
        ).parent

        hoc_so_list = list(nrnpy_path.glob("hoc*.so"))

        if len(hoc_so_list) != 1:
            warnings.warn(
                "Unable to find Neuron hoc shared library in %s, "
                "not disabling banner" % nrnpy_path
            )
        else:
            hoc_so = hoc_so_list[0]
            nrndll = ctypes.cdll[str(hoc_so)]
            ctypes.c_int.in_dll(nrndll, "nrn_nobanner_").value = 1

    # pylint: disable=R0201
    @property
    def neuron(self):
        """Return Neuron module"""

        if self.disable_banner and not self.banner_disabled:
            NrnSimulator._nrn_disable_banner()
            self.banner_disabled = True

        import neuron  # NOQA

        if self.mechanisms_directory is not None:
            neuron.load_mechanisms(
                self.mechanisms_directory, warn_if_already_loaded=False
            )

        return neuron

    def initialize(self):
        """Initialize simulator: Set Neuron variables"""
        self.neuron.h.load_file("stdrun.hoc")
        self.neuron.h.dt = self.dt
        self.neuron.h.cvode_active(1 if self.cvode_active else 0)

    def run(
        self,
        tstop=None,
        dt=None,
        cvode_active=None,
        random123_globalindex=None,
    ):
        """Run protocol"""

        self.neuron.h.tstop = tstop

        if cvode_active and dt is not None:
            raise ValueError(
                "NrnSimulator: Impossible to combine the dt argument when "
                "cvode_active is True in the NrnSimulator run method"
            )

        if cvode_active is None:
            cvode_active = self.cvode_active

        if not cvode_active and dt is None:  # use dt of simulator
            if self.neuron.h.dt != self.dt:
                raise Exception(
                    "NrnSimulator: Some process has changed the "
                    "time step dt of Neuron since the creation of this "
                    "NrnSimulator object. Not sure this is intended:\n"
                    "current dt: %.6g\n"
                    "init dt: %.6g" % (self.neuron.h.dt, self.dt)
                )
            dt = self.dt

        self.neuron.h.cvode_active(1 if cvode_active else 0)
        if self.cvode_minstep_value is not None:
            save_minstep = self.cvode_minstep
            self.cvode_minstep = self.cvode_minstep_value

        if cvode_active:
            logger.debug("Running Neuron simulator %.6g ms, with cvode", tstop)
        else:
            self.neuron.h.dt = dt
            self.neuron.h.steps_per_ms = 1.0 / dt
            logger.debug(
                "Running Neuron simulator %.6g ms, with dt=%r", tstop, dt
            )

        if random123_globalindex is None:
            random123_globalindex = self.random123_globalindex

        if random123_globalindex is not None:
            rng = self.neuron.h.Random()
            rng.Random123_globalindex(random123_globalindex)

        try:
            self.neuron.h.run()
        except Exception as e:
            raise NrnSimulatorException("Neuron simulator error", e)

        if self.cvode_minstep_value is not None:
            self.cvode_minstep = save_minstep

        logger.debug("Neuron simulation finished")


class NrnSimulatorException(Exception):
    """All exception generated by Neuron simulator"""

    def __init__(self, message, original):
        """Constructor"""

        super(NrnSimulatorException, self).__init__(message)
        self.original = original


class LFPySimulator(NrnSimulator):
    """LFPy simulator"""

    def __init__(
        self,
        dt=None,
        cvode_active=True,
        cvode_minstep=None,
        random123_globalindex=None,
        mechanisms_directory=None,
    ):
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

        super(LFPySimulator, self).__init__(
            dt=dt,
            cvode_active=cvode_active,
            cvode_minstep=cvode_minstep,
            random123_globalindex=random123_globalindex,
            mechanisms_directory=mechanisms_directory,
        )

    def run(
        self,
        lfpy_cell,
        lfpy_electrode,
        tstop=None,
        dt=None,
        cvode_active=None,
        random123_globalindex=None,
    ):
        """Run protocol"""
        _ = self.neuron

        lfpy_cell.tstart = 0.0
        lfpy_cell.tstop = tstop

        if dt is not None:
            lfpy_cell.dt = dt

        if cvode_active and dt is not None:
            raise ValueError(
                "NrnSimulator: Impossible to combine the dt argument when "
                "cvode_active is True in the NrnSimulator run method"
            )

        if cvode_active is None:
            cvode_active = self.cvode_active

        if cvode_active is not None:
            self.cvode_active = cvode_active

        if random123_globalindex is None:
            random123_globalindex = self.random123_globalindex

        if random123_globalindex is not None:
            rng = self.neuron.h.Random()
            rng.Random123_globalindex(random123_globalindex)

        probes = [lfpy_electrode] if lfpy_electrode is not None else None

        sim_params = {
            "probes": probes,
            "rec_vmem": False,
            "rec_imem": False,
            "rec_ipas": False,
            "rec_icap": False,
            "rec_variables": [],
            "variable_dt": self.cvode_active,
            "atol": 0.001,
            "to_memory": True,
            "to_file": False,
            "file_name": None,
        }

        try:
            lfpy_cell.simulate(**sim_params)
        except Exception as e:
            raise LFPySimulatorException("LFPy simulator error", e)

        logger.debug("LFPy simulation finished")


class LFPySimulatorException(Exception):
    """All exception generated by LFPy simulator"""

    def __init__(self, message, original):
        """Constructor"""

        super(LFPySimulatorException, self).__init__(message)
        self.original = original


class ArbSimulator(object):
    """Arbor simulator"""

    def __init__(self, dt=None, ext_catalogues=None):
        """Constructor

        Args:
            dt (float): the integration time step used by Arbor.
            ext_catalogues (): Name to path mapping of non-Arbor built-in
            NMODL mechanism catalogues compiled with modcc
        """

        self.dt = dt
        self.ext_catalogues = ext_catalogues
        if ext_catalogues is not None:
            for cat, cat_path in ext_catalogues.items():
                cat_lib = "%s-catalogue.so" % cat
                cat_path = pathlib.Path(cat_path).resolve()
                if not os.path.exists(cat_path / cat_lib):
                    raise ArbSimulatorException(
                        "Cannot find %s at %s - first build"
                        % (cat_lib, cat_path)
                        + " mechanism catalogue with modcc:"
                        + " arbor-build-catalogue %s %s" % (cat, cat_path)
                    )
        # TODO: add parameters for discretization

    def initialize(self):
        """Initialize simulator"""
        pass

    def instantiate(self, morph, decor, labels):
        cable_cell = arbor.cable_cell(
            morphology=morph, decor=decor, labels=labels
        )

        arb_cell_model = arbor.single_cell_model(cable_cell)

        # Add catalogues with explicit qualifiers
        arb_cell_model.properties.catalogue = arbor.catalogue()

        # User-supplied catalogues take precedence
        if self.ext_catalogues is not None:
            for cat, cat_path in self.ext_catalogues.items():
                cat_lib = "%s-catalogue.so" % cat
                cat_path = pathlib.Path(cat_path).resolve()
                arb_cell_model.properties.catalogue.extend(
                    arbor.load_catalogue(cat_path / cat_lib), cat + "::"
                )

        # Built-in catalogues are always added (could be made optional)
        if self.ext_catalogues is None or "default" not in self.ext_catalogues:
            arb_cell_model.properties.catalogue.extend(
                arbor.default_catalogue(), "default::"
            )

        if self.ext_catalogues is None or "BBP" not in self.ext_catalogues:
            arb_cell_model.properties.catalogue.extend(
                arbor.bbp_catalogue(), "BBP::"
            )

        if self.ext_catalogues is None or "allen" not in self.ext_catalogues:
            arb_cell_model.properties.catalogue.extend(
                arbor.allen_catalogue(), "allen::"
            )

        return arb_cell_model

    def run(self, arb_cell_model, tstop=None, dt=None):
        dt = dt if dt is not None else self.dt

        if dt is not None:
            return arb_cell_model.run(tfinal=tstop, dt=dt)
        else:
            return arb_cell_model.run(tfinal=tstop)


class ArbSimulatorException(Exception):
    """All exception generated by Arbor simulator"""

    def __init__(self, message):
        """Constructor"""

        super(ArbSimulatorException, self).__init__(message)
