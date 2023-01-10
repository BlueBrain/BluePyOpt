"""Functions to create neuroml morphology"""

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
import os
from pathlib import Path

import neuroml
from pyneuroml.neuron import export_to_neuroml2

logger = logging.getLogger(__name__)


def create_loadcell_hoc(
    loadcell_hoc_filename, hoc_filename, morphology_path, v_init, cell_name
):
    """Create a hoc file able to load the cell.

    Arguments:
        loadcell_hoc_filename (str): path to the loadcell hoc file to output
        hoc_filename (str): file name of the cell hoc file
        morphology_path (str): path to the morphology file
        v_init (float): inital voltage in mV
        cell_name (str): cell name
    """
    morph_path = Path(morphology_path)
    morph_dir = morph_path.parent
    morph_file = morph_path.name
    cell_cmd = '"cell = new %s(\\"%s\\", \\"%s\\")"'
    cell = f'{cell_cmd}, "{cell_name}", "{morph_dir}", "{morph_file}"'
    loadcell_hoc = f"""
        load_file("nrngui.hoc")
        load_file("import3d.hoc")
        load_file("{hoc_filename}")

        // ================== constants ==================
        v_init={v_init}
        // ================== creating cell object ==================
        objref cell

        proc create_cell() {{ localobj cellstring
            cellstring = new String()
            sprint(cellstring.s, {cell})
            execute(cellstring.s)
        }}
        create_cell(0)
    """
    with open(loadcell_hoc_filename, "w", encoding="utf-8") as hoc_file:
        hoc_file.write(loadcell_hoc)


def create_morph_nml(bpo_cell, network_filename, release_params):
    """Create cell hoc file, then cell nml file.

    Arguments:
        bpo_cell (ephys.CellModel): bluepyopt cell
        network_filename (str): name of the neuroml network file
        release_params (dict): name and values of optimised parameters
    """
    import pebble

    hoc_filename = f"{bpo_cell.name}.hoc"
    loadcell_hoc_filename = "loadcell.hoc"

    # write the cell in a hoc file
    cell_hoc = bpo_cell.create_hoc(release_params)
    with open(hoc_filename, "w", encoding="utf-8") as hoc_file:
        hoc_file.write(cell_hoc)

    # write a hoc file able to load the cell
    create_loadcell_hoc(
        loadcell_hoc_filename,
        hoc_filename,
        bpo_cell.morphology.morphology_path,
        bpo_cell.params["v_init"].value,
        bpo_cell.name,
    )

    if not os.path.isdir("x86_64"):
        logger.warning(
            "It seems you have not compiled the mechanisms. "
            "This program will likely fail."
        )

    # isolate the export_to_neuroml to a subprocess
    # so that the cell remain non-instantiated in the main process
    # that way, using this function will not prevent us to run the cell
    # with bluepyopt
    with pebble.ProcessPool(max_workers=1, max_tasks=1) as pool:
        tasks = pool.schedule(
            export_to_neuroml2,
            kwargs={
                "hoc_or_python_file": loadcell_hoc_filename,
                "nml2_file_name": network_filename,
                "separateCellFiles": True,
                "includeBiophysicalProperties": False,
            },
        )
        tasks.result()


def add_segment_groups(cell):
    """Add the segment groups to be consistent with naming in biophys.

    Arguments:
        cell (neuroml.Cell): neuroml cell
    """
    groups = {"somatic": [], "axonal": [], "basal": [], "apical": []}
    for seg in cell.morphology.segment_groups:
        if "soma" in seg.id:
            groups["somatic"].append(seg)
        elif "axon" in seg.id:
            groups["axonal"].append(seg)
        elif "dend" in seg.id:
            groups["basal"].append(seg)
        elif "apic" in seg.id:
            groups["apical"].append(seg)

    for g, segments in groups.items():
        new_seg_group = neuroml.SegmentGroup(id=g)
        cell.morphology.segment_groups.append(new_seg_group)
        for sg in segments:
            new_seg_group.includes.append(neuroml.Include(sg.id))
        if g in ["basal", "apical"]:
            new_seg_group.inhomogeneous_parameters.append(
                neuroml.InhomogeneousParameter(
                    id=f"PathLengthOver_{g}",
                    variable="p",
                    metric="Path Length from root",
                    proximal=neuroml.ProximalDetails(translation_start="0"),
                )
            )

    cell.morphology.segment_groups.append(
        neuroml.SegmentGroup(
            id="soma_group", includes=[neuroml.Include("somatic")]
        )
    )
    cell.morphology.segment_groups.append(
        neuroml.SegmentGroup(
            id="axon_group", includes=[neuroml.Include("axonal")]
        )
    )
    cell.morphology.segment_groups.append(
        neuroml.SegmentGroup(
            id="dendrite_group",
            includes=[neuroml.Include("basal"), neuroml.Include("apical")],
        )
    )
