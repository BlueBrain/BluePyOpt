"""Morphology classes"""

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


import os
import logging
logger = logging.getLogger(__name__)

# TODO define an addressing scheme


class Morphology(object):

    """Morphology class"""

    def __init__(self):
        """Constructor"""

        pass


class NrnFileMorphology(Morphology):

    """Morphology loaded from a file"""

    def __init__(
            self,
            morphology_path,
            do_replace_axon=False,
            do_set_nseg=True):
        """Constructor

        Args:
            morphology_path (str): location of the file describing the
                morphology
            do_replace_axon(bool): Does the axon need to be replaced by an AIS
                stub ?
        """

        super(NrnFileMorphology, self).__init__()
        # TODO speed up loading of morphologies from files
        # Path to morphology
        self.morphology_path = morphology_path
        self.do_replace_axon = do_replace_axon
        self.do_set_nseg = do_set_nseg

    def __str__(self):
        """Return string representation"""

        return self.morphology_path

    def instantiate(self, sim=None, icell=None):
        """Load morphology"""

        logger.debug('Loading morphology %s', self.morphology_path)

        if not os.path.exists(self.morphology_path):
            raise IOError(
                'Morphology not found at \'%s\'' %
                self.morphology_path)

        sim.neuron.h.load_file('stdrun.hoc')
        sim.neuron.h.load_file('import3d.hoc')

        extension = self.morphology_path.split('.')[-1]

        if extension.lower() == 'swc':
            imorphology = sim.neuron.h.Import3d_SWC_read()
        elif extension.lower() == 'asc':
            imorphology = sim.neuron.h.Import3d_Neurolucida3()
        else:
            raise ValueError("Unknown filetype: %s" % extension)

        # TODO this is to get rid of stdout print of neuron
        # probably should be more intelligent here, and filter out the
        # lines we don't want
        sim.neuron.h.hoc_stdout('/dev/null')
        imorphology.input(str(self.morphology_path))
        sim.neuron.h.hoc_stdout()

        morphology_importer = sim.neuron.h.Import3d_GUI(imorphology, 0)

        morphology_importer.instantiate(icell)

        # TODO Set nseg should be called after all the parameters have been
        # set
        # (in case e.g. Ra was changed)
        if self.do_set_nseg:
            NrnFileMorphology.set_nseg(icell)

        # TODO replace these two functions with general function users can
        # specify
        if self.do_replace_axon:
            NrnFileMorphology.replace_axon(sim=sim, icell=icell)

    def destroy(self):
        """Destroy morphology instantiation"""
        pass

    @staticmethod
    def set_nseg(icell):
        """Set the nseg of every section"""

        for section in icell.all:
            section.nseg = 1 + 2 * int(section.L / 40)

    @staticmethod
    def replace_axon(sim=None, icell=None):
        """Replace axon"""

        ais_diams = [icell.axon[0].diam, icell.axon[0].diam]

        # Define origin of distance function
        sim.neuron.h.distance(sec=icell.soma[0])
        for section in icell.axonal:
            # If distance to soma is larger than 60, store diameter
            if sim.neuron.h.distance(0.5, sec=section) > 60:
                ais_diams[1] = section.diam
                break

        for section in icell.axonal:
            sim.neuron.h.delete_section(sec=section)

        # Create new axon array
        sim.neuron.h.execute('create axon[2]', icell)

        for index, section in enumerate(icell.axon):
            section.nseg = 1
            section.L = 30
            section.diam = ais_diams[index]
            icell.axonal.append(sec=section)
            icell.all.append(sec=section)

        icell.axon[0].connect(icell.soma[0], 1.0, 0.0)
        icell.axon[1].connect(icell.axon[0], 1.0, 0.0)

        logger.debug('Replace axon with AIS')
