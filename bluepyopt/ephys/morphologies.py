"""Morphology classes"""

"""
Copyright (c) 2016-2020, EPFL/Blue Brain Project

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

import os
import platform
import logging
from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin

try:
    import arbor
    import numpy
except ImportError as e:
    class arbor:
        def __getattribute__(self, _):
            raise ImportError("Loading an ACC/JSON-exported cell model into an"
                              " Arbor morphology and cable cell components"
                              " requires missing dependency arbor."
                              " To install BluePyOpt with arbor,"
                              " run 'pip install bluepyopt[arbor]'.")


logger = logging.getLogger(__name__)

# TODO define an addressing scheme


class Morphology(BaseEPhys):

    """Morphology class"""
    pass


class NrnFileMorphology(Morphology, DictMixin):

    """Morphology loaded from a file"""
    SERIALIZED_FIELDS = ('morphology_path', 'do_replace_axon', 'do_set_nseg',
                         'replace_axon_hoc', )

    def __init__(
            self,
            morphology_path,
            do_replace_axon=False,
            do_set_nseg=True,
            comment='',
            replace_axon_hoc=None,
            nseg_frequency=40,
            morph_modifiers=None,
            morph_modifiers_hoc=None):
        """Constructor

        Args:
            morphology_path (str): location of the file describing the
                morphology
            do_replace_axon (bool): Does the axon need to be replaced by an AIS
                stub with default function ?
            replace_axon_hoc (str): Translation in HOC language for the
                'replace_axon' method. This code will 'only' be used when
                calling create_hoc on a cell model. While the model is run in
                python, replace_axon is used instead. Must include
                'proc replace_axon(){ ... }
                If None,the default replace_axon is used
            nseg_frequency (float): frequency of nseg
            do_set_nseg (bool): if True, it will use nseg_frequency
            morph_modifiers (list): list of functions to modify the icell
                with (sim, icell) as arguments
            morph_modifiers_hoc (list): list of hoc strings corresponding
                to morph_modifiers
        """
        name = os.path.basename(morphology_path)
        super(NrnFileMorphology, self).__init__(name=name, comment=comment)
        # TODO speed up loading of morphologies from files
        # Path to morphology
        self.morphology_path = morphology_path
        self.do_replace_axon = do_replace_axon
        self.do_set_nseg = do_set_nseg
        self.nseg_frequency = nseg_frequency
        self.morph_modifiers = morph_modifiers
        self.morph_modifiers_hoc = morph_modifiers_hoc

        if replace_axon_hoc is None:
            self.replace_axon_hoc = self.default_replace_axon_hoc
        else:
            self.replace_axon_hoc = replace_axon_hoc

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

        imorphology.quiet = 1

        if platform.system() == 'Windows':
            sim.neuron.h.hoc_stdout('NUL')
        else:
            sim.neuron.h.hoc_stdout('/dev/null')

        imorphology.input(str(self.morphology_path))
        sim.neuron.h.hoc_stdout()

        morphology_importer = sim.neuron.h.Import3d_GUI(imorphology, 0)

        morphology_importer.instantiate(icell)

        # TODO Set nseg should be called after all the parameters have been
        # set
        # (in case e.g. Ra was changed)
        if self.do_set_nseg:
            self.set_nseg(icell)

        if self.do_replace_axon:
            self.replace_axon(sim=sim, icell=icell)

        if self.morph_modifiers is not None:
            for morph_modifier in self.morph_modifiers:
                morph_modifier(sim=sim, icell=icell)

    def destroy(self, sim=None):
        """Destroy morphology instantiation"""
        pass

    def set_nseg(self, icell):
        """Set the nseg of every section"""
        for section in icell.all:
            section.nseg = 1 + 2 * int(section.L / self.nseg_frequency)

    @staticmethod
    def replace_axon(sim=None, icell=None):
        """Replace axon"""

        nsec = len([sec for sec in icell.axonal])

        if nsec == 0:
            ais_diams = [1, 1]
        elif nsec == 1:
            ais_diams = [icell.axon[0].diam, icell.axon[0].diam]
        else:
            ais_diams = [icell.axon[0].diam, icell.axon[0].diam]
            # Define origin of distance function
            sim.neuron.h.distance(0, 0.5, sec=icell.soma[0])

            for section in icell.axonal:
                # If distance to soma is larger than 60, store diameter
                if sim.neuron.h.distance(1, 0.5, sec=section) > 60:
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

    default_replace_axon_hoc = \
        '''
proc replace_axon(){ local nSec, D1, D2
  // preserve the number of original axonal sections
  nSec = sec_count(axonal)

  // Try to grab info from original axon
  if(nSec == 0) { //No axon section present
    D1 = D2 = 1
  } else if(nSec == 1) {
    axon[0] D1 = D2 = diam
  } else {
    axon[0] D1 = D2 = diam
    soma distance() //to calculate distance from soma
    forsec axonal{
      //if section is longer than 60um then store diam and exit from loop
      if(distance(0.5) > 60){
        D2 = diam
        break
      }
    }
  }

  // get rid of the old axon
  forsec axonal{
    delete_section()
  }

  create axon[2]

  axon[0] {
    L = 30
    diam = D1
    nseg = 1 + 2*int(L/40)
    all.append()
    axonal.append()
  }
  axon[1] {
    L = 30
    diam = D2
    nseg = 1 + 2*int(L/40)
    all.append()
    axonal.append()
  }
  nSecAxonal = 2
  soma[0] connect axon[0](0), 1
  axon[0] connect axon[1](0), 1
}
        '''


class ArbLabel:
    """Arbor label"""

    def __init__(self, type, name, defn):
        self._type = type
        self._name = name
        self._defn = defn

    @property
    def defn(self):
        """Label definition for label-dict"""
        return '(%s-def "%s" %s)' % (self._type, self._name, self._defn)

    @property
    def ref(self):
        """Reference to label defined in label-dict"""
        return '(%s "%s")' % (self._type, self._name)

    @property
    def name(self):
        """Name of the label"""
        return self._name

    @property
    def loc(self):
        """Expression defining the location of the label"""
        return self._defn


class ArbFileMorphology(Morphology, DictMixin):
    """Arbor morphology utilities"""

    # Arbor morphology tags
    tags = dict(
        soma=1,
        axon=2,
        dend=3,
        apic=4,
        myelin=5
    )

    # Correspondence of BluePyOpt to Arbor region labels
    # (renaming locations according to SWC convention: using
    # 'dend' for basal dendrite, 'apic' for apical dendrite)
    region_labels = dict(
        all=ArbLabel(
            type='region', name='all', defn='(all)'),
        somatic=ArbLabel(
            type='region', name='soma', defn='(tag %i)' % tags['soma']),
        axonal=ArbLabel(
            type='region', name='axon', defn='(tag %i)' % tags['axon']),
        basal=ArbLabel(
            type='region', name='dend', defn='(tag %i)' % tags['dend']),
        apical=ArbLabel(
            type='region', name='apic', defn='(tag %i)' % tags['apic']),
        myelinated=ArbLabel(
            type='region', name='myelin', defn='(tag %i)' % tags['myelin']),
    )

    @staticmethod
    def replace_axon(morphology, replacement=None):
        '''return a morphology with the axon replaced by two 30 um segments

        Args:
            morphology (arbor.morphology): An Arbor morphology
            replacement (): A list of dictionaries containing Arbor segment
            parameters including nseg, length, radius and tag of the axon
            replacement (derived from Neuron's stylized specification of
            geometry, cf. Neuron topology/geometry docs). Each of these is
            interpreted so that the axon replacement is formed from a single
            branch of stacked cylindrical segments.
        '''

        def _mpt_to_coord(mpt):
            '''Convert arbor.mpoint 3d center coordinates to numpy array'''
            return numpy.array([mpt.x, mpt.y, mpt.z])

        def _find_ais_centers(st, axon_parent=None):
            if axon_parent is None or axon_parent == arbor.mnpos:
                soma_segs = [i for i, s in enumerate(st.segments)
                             if s.tag == ArbFileMorphology.tags['soma']]
                soma_terminals = [i for i in soma_segs if st.is_terminal(i)]
                if len(soma_terminals) > 0:
                    axon_parent = soma_terminals[-1]
                elif len(soma_segs) > 0:
                    axon_parent = soma_segs[-1]
                else:
                    raise ValueError('Morphology without soma,'
                                     ' cannot replace axon.')

            ar_prox = st.segments[axon_parent].dist
            ar_prox_center = _mpt_to_coord(ar_prox)
            ar_dist = st.segments[axon_parent].prox
            ar_dist_center = 2 * ar_prox_center - _mpt_to_coord(ar_dist)

            return ar_prox_center, ar_dist_center

        # Check if tag_roots is available
        if not hasattr(arbor.segment_tree, 'tag_roots'):
            raise NotImplementedError(
                "Need a newer version of Arbor for axon replacement.")

        # Arbor tags
        axon_tag = ArbFileMorphology.tags['axon']

        # Prune morphology at axon root
        st = morphology.to_segment_tree()
        axon_roots = st.tag_roots(axon_tag)
        if len(axon_roots) > 1:
            raise ValueError("Axon replacement is only supported for "
                             "morphologies with a single axon root.")
        elif len(axon_roots) == 1:
            axon_root = axon_roots[0]
            pruned_st, axon_st = st.split_at(axon_root)
        else:
            pruned_st = st

        if replacement is not None:
            ar_radius = [r['radius'] for r in replacement]
        else:
            if len(axon_roots) > 1:
                ValueError('Please specify axon replacement explicitly '
                           'for morphology with pre-existing axon.')
            ar_radius = None

        # Create axon replacement building on the pruned root
        if len(axon_roots) == 1:
            axon_root = axon_roots[0]
            axon_parent = st.parents[axon_root]
            ar_prox = st.segments[axon_root].prox
            ar_prox_center = _mpt_to_coord(ar_prox)
            ar_dist = st.segments[axon_root].dist
            ar_dist_center = _mpt_to_coord(ar_dist)

            if all(ar_prox_center == ar_dist_center):
                ar_prox_center, ar_dist_center = \
                    _find_ais_centers(st, axon_parent)

            # Could approximate ar_radius based on original morphology
            # here if it is None (caught above)

            logger.debug('Replacing axon with root %d with AIS'
                         ' of radii %s.', axon_root, str(ar_radius))
        else:
            if ar_radius is None:
                ar_radius = [0.5, 0.5]

            ar_prox_center, ar_dist_center = _find_ais_centers(st)

            # create new branch for replaced axon not to break
            # existing location expressions
            axon_parent = arbor.mnpos
            logger.debug('Replacing non-existent axon with AIS'
                         ' of radii %s.', str(ar_radius))

        if replacement is not None:
            ar_seg_scaling = numpy.cumsum([0] +
                                          [r['length'] for r in replacement])
        else:
            ar_seg_scaling = numpy.cumsum([0, 30, 30])
        ar_seg_scaling /= numpy.linalg.norm(ar_dist_center - ar_prox_center)

        ar_centers = [ar_prox_center +
                      scale * (ar_dist_center - ar_prox_center)
                      for scale in ar_seg_scaling]

        ar_tags = [r['tag'] for r in replacement]

        for prox, dist, radius, tag in zip(ar_centers[:-1],
                                           ar_centers[1:],
                                           ar_radius,
                                           ar_tags):
            axon_parent = pruned_st.append(
                axon_parent,
                arbor.mpoint(*prox, radius),
                arbor.mpoint(*dist, radius),
                tag)

        return arbor.morphology(pruned_st)
