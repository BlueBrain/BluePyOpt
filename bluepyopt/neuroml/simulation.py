"""Functions to create neuroml  simulation"""

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

import neuroml
from neuroml import ExplicitInput

from pyneuroml import pynml
from pyneuroml.lems import generate_lems_file_for_neuroml

logger = logging.getLogger(__name__)


def create_neuroml_simulation(
    network_filename, protocols, dt, cell_name, lems_filename
):
    """Append simulation data to a neuroml network.

    Arguments:
        network_filename (str): name of the neuroml network file
        protocols (ephys.protocols.Protocol): protocols
        dt (float): timestep
        cell_name (str): name of the cell
        lems_filename (str): file name under which to register the lems file
    """
    # Get neuroml netowrk file
    new_net_doc = pynml.read_neuroml2_file(network_filename)
    new_net = new_net_doc.networks[0]

    pop_id = new_net.populations[0].id

    stim_sim_duration = 0

    # Create neuroml stimuli
    # Expects ephys.stimuli.NrnSquarePulse objects
    for i, stim in enumerate(protocols.stimuli):
        stim_sim_duration = stim.total_duration
        stim_ref = f"stimulus_{i}"

        # create Pulse
        new_nml_stim = neuroml.PulseGenerator(
            id=stim_ref,
            delay=f"{stim.step_delay}ms",
            duration=f"{stim.step_duration}ms",
            amplitude=f"{stim.step_amplitude}nA",
        )
        new_net_doc.pulse_generators.append(new_nml_stim)

        exp_input = ExplicitInput(target=f"{pop_id}[0]", input=stim_ref)
        new_net.explicit_inputs.append(exp_input)

    # write updated netowrk file
    pynml.write_neuroml2_file(new_net_doc, network_filename)

    local_nml2_cell_dir = "."  # target dir
    generate_lems_file_for_neuroml(
        cell_name,
        network_filename,
        "network",
        stim_sim_duration,
        dt,
        lems_filename,
        local_nml2_cell_dir,
        copy_neuroml=False,
        simulation_seed=1234,
    )
