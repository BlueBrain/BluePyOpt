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
import pathlib
import bisect
import numpy
from bluepyopt.ephys.base import BaseEPhys
from bluepyopt.ephys.serializer import DictMixin
from bluepyopt.ephys.acc import arbor, ArbLabel

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
            morphology_path (str or Path): location of the file describing the
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
        if isinstance(morphology_path, pathlib.Path):
            morphology_path = str(morphology_path)
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

    # Correspondence of BluePyOpt seclists to Arbor region labels
    # (renaming locations according to SWC convention: using
    # 'dend' for basal dendrite, 'apic' for apical dendrite)
    region_labels = dict(
        all=ArbLabel(
            type='region', name='all', s_expr='(all)'),
        somatic=ArbLabel(
            type='region', name='soma', s_expr='(tag %i)' % tags['soma']),
        axonal=ArbLabel(
            type='region', name='axon', s_expr='(tag %i)' % tags['axon']),
        basal=ArbLabel(
            type='region', name='dend', s_expr='(tag %i)' % tags['dend']),
        apical=ArbLabel(
            type='region', name='apic', s_expr='(tag %i)' % tags['apic']),
        myelinated=ArbLabel(
            type='region', name='myelin', s_expr='(tag %i)' % tags['myelin']),
    )

    @staticmethod
    def load(morpho_filename, replace_axon):
        '''Load morphology and optionally perform axon replacement

        Args:
            morpho_filename (str): Path to file with original morphology.
            replace_axon (): Path to/ACC string for morphology to replace
            axon with (if not None).
        '''

        morpho_suffix = pathlib.Path(morpho_filename).suffix

        if morpho_suffix == '.acc':
            morpho = arbor.load_component(morpho_filename).component
        elif morpho_suffix == '.swc':
            morpho = arbor.load_swc_arbor(morpho_filename)
        elif morpho_suffix == '.asc':
            morpho = arbor.load_asc(morpho_filename).morphology
        else:
            raise RuntimeError(
                'Unsupported morphology %s' % morpho_filename +
                ' (only .swc and .asc supported)')

        if replace_axon is not None:
            replacement = arbor.load_component(replace_axon).component
            morpho = ArbFileMorphology.replace_axon(morpho, replacement)

        return morpho

    @staticmethod
    def extract_nrn_seclists(icell, seclists):
        '''Extract section lists from an instantiated cell (axon replacement)

        Args:
            icell (): Instantiated cell model in the NEURON simulator.
            seclists (): List of section lists to extract
            (typically ['axon'] or ['axon', 'myelin']).
        '''
        replace_axon = arbor.segment_tree()
        nrn_seg_to_dist = dict()
        nrn_seg_to_arb_seg = dict()
        for sec in seclists:
            for section in getattr(icell, sec):

                if replace_axon.size == 0:  # root
                    arb_parent_seg = arbor.mnpos
                else:
                    parent_seg = section.parentseg()
                    parent_sec = parent_seg.sec.name()
                    parent_x = parent_seg.x
                    parent_seg_id = bisect.bisect_left(
                        nrn_seg_to_dist[parent_sec],
                        parent_x)
                    arb_parent_seg = \
                        nrn_seg_to_arb_seg[parent_sec][parent_seg_id]

                pts3d = section.psection()['morphology']['pts3d']
                if len(pts3d) == 0:
                    # stylized geometry, must use sim.neuron.h.define_shape()
                    raise ValueError('Before exporting to ACC, embed'
                                     ' stylized geometry in 3d'
                                     ' by instantiating morphology with'
                                     ' cell_model.instantiate_morphology_3d.')

                pts3d = numpy.array(pts3d)
                dist_x = numpy.cumsum(
                    numpy.linalg.norm(
                        pts3d[1:, :3] - pts3d[:-1, :3], axis=1)) /\
                    section.psection()['morphology']['L']
                relative_length_err = abs(1. - dist_x[-1])
                if relative_length_err > 1e-4:
                    logger.warn('pts3d length does not add up to'
                                ' section length, relative error = %s' %
                                relative_length_err)
                    if relative_length_err > 1e-2:
                        raise ValueError('pts3d length inconsistent'
                                         ' with section length, relative'
                                         ' error = %s' %
                                         relative_length_err)

                dist_x[-1] = 1.
                nrn_seg_to_dist[section.name()] = dist_x

                arb_seg_ids = []
                for i in range(1, len(pts3d)):
                    prox = pts3d[i - 1]
                    dist = pts3d[i]
                    arb_parent_seg = replace_axon.append(
                        arb_parent_seg,
                        arbor.mpoint(*prox[:3], 0.5 * prox[3]),
                        arbor.mpoint(*dist[:3], 0.5 * dist[3]),
                        ArbFileMorphology.tags[sec])
                    arb_seg_ids.append(arb_parent_seg)
                # dist, arb_seg_id pairs
                nrn_seg_to_arb_seg[section.name()] = arb_seg_ids

        replace_axon = arbor.morphology(replace_axon)

        return replace_axon

    @staticmethod
    def replace_axon(morphology, replacement=None):
        '''return a morphology with the axon replaced by another morphology

        Args:
            morphology (arbor.morphology): The original Arbor morphology
            replacement (): An Arbor morphology to replace the axon with
        '''

        # Check if tag_roots is available
        if not hasattr(arbor.segment_tree, 'tag_roots'):
            raise NotImplementedError(
                "Need a newer version of Arbor for axon replacement.")

        # Arbor tags
        axon_tag = ArbFileMorphology.tags['axon']

        # prune morphology at axon root
        st = morphology.to_segment_tree()
        axon_roots = st.tag_roots(axon_tag)
        if len(axon_roots) > 1:
            raise ValueError("Axon replacement is only supported for "
                             "morphologies with a single axon root.")
        elif len(axon_roots) == 1:
            axon_root = axon_roots[0]
            logger.debug('Axon replacement: splitting segment tree'
                         ' at segment %d.', axon_root)
            pruned_st, axon_st = st.split_at(axon_root)
            axon_parent = st.parents[axon_root]
        else:
            pruned_st = st
            axon_parent = arbor.mnpos

        # join pruned segment tree and replacement at axon parent
        axon_replacement_st = replacement.to_segment_tree()

        logger.debug('Axon replacement: joining replacement onto'
                     'pruned tree at parent segment %d.', axon_parent)
        joined_st = pruned_st.join_at(
            axon_parent, axon_replacement_st)

        return arbor.morphology(joined_st)
