"""Functions to create neuroml cell"""

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

import logging

from neuroml import NeuroMLDocument
from pyneuroml import pynml

from .biophys import get_biophys
from .morphology import add_segment_groups
from .morphology import create_morph_nml

logger = logging.getLogger(__name__)


def create_neuroml_cell(
    bpo_cell,
    release_params,
    skip_channels_copy=False,
    custom_channel_ion=None,
    custom_ion_erevs=None,
):
    """Create the cell.

    Arguments:
        bpo_cell (ephys.CellModel): bluepyopt cell
        release_params (dict): the optimized parameters
        skip_channels_copy (bool): True to skip the copy pasting
            of the neuroml channel files
        custom_channel_ion (dict): dict mapping channel to ion
        custom_ion_erevs (dict): dict mapping ion to erev (reversal potential)

    :returns: name of the cell nml file
    """
    # Create the nml file and add the ion channels
    cell_doc = NeuroMLDocument(id=bpo_cell.name)
    # the network name
    network_filename = f"{bpo_cell.name}.net.nml"

    # Morphology
    logger.info(
        "This will create a cell hoc file in order to create a cell nml file"
    )
    create_morph_nml(bpo_cell, network_filename, release_params)

    # change the network temperature.
    # because the pyneurom.export_to_neuroml2 sets it automatically to 6C.
    network_doc = pynml.read_neuroml2_file(network_filename)
    network = network_doc.networks[0]
    network.temperature = f"{bpo_cell.params['celsius'].value} degC"
    pynml.write_neuroml2_file(
        nml2_doc=network_doc, nml2_file_name=network_filename, validate=True
    )

    # get the cell
    nml_cell_loc = f"{bpo_cell.name}_0_0.cell.nml"
    nml_doc = pynml.read_neuroml2_file(nml_cell_loc)

    cell = nml_doc.cells[0]

    # add segment groups (cell)
    add_segment_groups(cell)

    # get biophys
    bio_prop = get_biophys(
        bpo_cell,
        cell_doc,
        release_params,
        skip_non_uniform=True,
        skip_channels_copy=skip_channels_copy,
        custom_channel_ion=custom_channel_ion,
        custom_ion_erevs=custom_ion_erevs,
    )

    # Append biophys to cell
    cell.biophysical_properties = bio_prop

    # Adding notes
    notes = "This cell was exported from BluePyOpt."
    cell.notes = notes

    # write neuroml cell doc
    cell_doc.cells.append(cell)
    pynml.write_neuroml2_file(
        nml2_doc=cell_doc, nml2_file_name=nml_cell_loc, validate=True
    )

    return nml_cell_loc
