"""Create l5pc model with MEA"""

"""
Copyright (c) 2016-2022, EPFL/Blue Brain Project

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

import sys
import os
import MEAutility as mu

import bluepyopt
import bluepyopt.ephys as ephys

L5PC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../l5pc'))
sys.path.insert(0, L5PC_PATH)

import l5pc_model


def define_electrode(
    probe_center=[0, 300, 20],
    mea_dim=[10, 4],
    mea_pitch=[300, 300],
):
    """
    Defines LFPy electrode object
    Parameters
    ----------
    probe_center: 3d array
        The center of the probe
    mea_dim: 2d array
        Dimensions of planar probe (nrows, ncols)
    mea_pitch: 3d arraay
        The pitch of the planar probe (row pitch, column pitch)
    Returns
    -------
    electrode: MEAutility.MEA object
        The MEAutility electrode object
    """

    mea_info = {
        'dim': mea_dim,
        'electrode_name': 'hd-mea',
        'pitch': mea_pitch,
        'shape': 'square',
        'size': 5,
        'type': 'mea',
        'plane': 'xy'
    }
    probe = mu.return_mea(info=mea_info)

    # Move the MEA out of the neuron plane (yz)
    probe.move(probe_center)

    return probe


def create():

    l5pc_cell = ephys.models.LFPyCellModel(
        "l5pc_lfpy",
        morph=l5pc_model.define_morphology(),
        mechs=l5pc_model.define_mechanisms(),
        params=l5pc_model.define_parameters(),
        electrode=define_electrode()
    )

    return l5pc_cell
