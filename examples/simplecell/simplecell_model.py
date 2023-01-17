"""Run simple cell optimisation"""

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
# pylint: disable=R0914

import bluepyopt.ephys as ephys


def define_morphology(do_replace_axon):

    return ephys.morphologies.NrnFileMorphology('simple.swc',
                                                 do_replace_axon=do_replace_axon)

def define_mechanisms():
    somatic_loc = ephys.locations.NrnSeclistLocation('somatic', seclist_name='somatic')

    hh_mech = ephys.mechanisms.NrnMODMechanism(
        name='hh',
        suffix='hh',
        locations=[somatic_loc])
    return [hh_mech]


def define_parameters():
    somatic_loc = ephys.locations.NrnSeclistLocation('somatic', seclist_name='somatic')

    cm_param = ephys.parameters.NrnSectionParameter(
        name='cm',
        param_name='cm',
        value=1.0,
        locations=[somatic_loc],
        frozen=True)

    gnabar_param = ephys.parameters.NrnSectionParameter(                                    
        name='gnabar_hh',
        param_name='gnabar_hh',
        locations=[somatic_loc],
        bounds=[0.05, 0.125],
        frozen=False)
    gkbar_param = ephys.parameters.NrnSectionParameter(
        name='gkbar_hh',
        param_name='gkbar_hh',
        bounds=[0.01, 0.075],
        locations=[somatic_loc],
        frozen=False)
    return [cm_param, gnabar_param, gkbar_param]


def create(do_replace_axon):
    """Create cell model (identical to simplecell.ipynb)"""

    cell = ephys.models.CellModel(
        'simple_cell',
        morph=define_morphology(do_replace_axon),
        mechs=define_mechanisms(),
        params=define_parameters())

    return cell
