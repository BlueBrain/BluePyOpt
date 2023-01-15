"""Functions to create neuroml biophysiology"""

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

import os
import shutil
from pathlib import Path

import neuroml

from bluepyopt import ephys

ignore_params = ["cm", "Ra", "ena", "ek"]

# Due to the use of 1e-4 in BREAKPOINT in StochKv.mod:
# ik = 1e-4 * gk * (v - ek)
density_scales = {"StochKv": 1e-4}

channel_substitutes = {"StochKv": "StochKv_deterministic"}

channel_ions = {
    "Ih": "hcn",
    "NaTa_t": "na",
    "NaTs2_t": "na",
    "Nap_Et2": "na",
    "K_Tst": "k",
    "K_Pst": "k",
    "SKv3_1": "k",
    "SK_E2": "k",
    "StochKv": "k",
    "KdShu2007": "k",
    "Im": "k",
    "Ca": "ca",
    "Ca_HVA": "ca",
    "Ca_LVAst": "ca",
    "pas": "pas",
    "CaDynamics_E2": "ca",
}

ion_erevs = {
    "na": "50.0 mV",
    "k": "-85.0 mV",
    "hcn": "-45.0 mV",
    "ca": "nernst",
    "pas": "pas",
}

default_capacitances = {
    "axonal": "1.0 uF_per_cm2",
    "somatic": "1.0 uF_per_cm2",
    "basal": "1.0 uF_per_cm2",
    "apical": "1.0 uF_per_cm2",
}


def get_nml_mech_dir():
    """Returns path to repo containing neuroml mechanisms."""
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "NeuroML2_mechanisms")
    )


def adapt_CaDynamics_nml(
    new_concentrations,
    channel_dir="channels",
):
    """Write concentration model if not present in CaDynamics nml file.

    We have to use this non-neuroml2 approved trick until
    https://github.com/NeuroML/NeuroML2/issues/153 is solved.

    Arguments:
        new_concentrations (dict): dict of the form
            "model_name": {"gamma": value "decay": value}
            describing the concentrations to append to
            ./{channel_dir}/CaDynamics_E2_NML2.nml
        channel_dir (str): repo in which to copy the channel files
    """
    place_after = (
        '    <concentrationModel id="CaDynamics_E2_NML2" '
        'type="concentrationModelHayEtAl" '
        'minCai="1e-4 mM" decay="80 ms" depth="0.1 um" '
        'gamma="0.05" ion="ca"/>\n'
    )
    cadyn_filename = "baseCaDynamics_E2_NML2.nml"
    new_cadyn_filename = "CaDynamics_E2_NML2.nml"
    nml_mech_dir = get_nml_mech_dir()

    with open(Path(nml_mech_dir) / cadyn_filename, "r") as f:
        lines = f.readlines()

    for model, value_dict in new_concentrations.items():
        new_concentration = (
            f'    <concentrationModel id="{model}" ion="ca" '
            'type="concentrationModelHayEtAl" minCai="1e-4 mM" '
            f'gamma="{value_dict["gamma"]}" '
            f'decay="{value_dict["decay"]} ms" depth="0.1 um"/>\n'
        )
        if new_concentration not in lines:
            idx = lines.index(place_after) + 2  # 2 to account for blank line
            lines.insert(idx, f"{new_concentration}\n")

    Path(channel_dir).mkdir(exist_ok=True)
    with open(Path(channel_dir) / new_cadyn_filename, "w") as f:
        contents = "".join(lines)
        f.write(contents)


def get_channel_from_param_name(param_name):
    """Return channel name, given parameter name.

    Arguments:
        param_name (str): parameter name used within NEURON
    """
    split_name = param_name.split("_")
    if len(split_name) == 4:
        channel = "_".join(split_name[2:4])
    elif len(split_name) == 3:
        channel = "_".join(split_name[1:3])
    elif len(split_name) == 2:
        channel = split_name[1]
    else:
        raise Exception(
            f"Could not extract channel from parameter name {param_name}"
        )

    return channel


def format_dist_fun(raw_expr, value, dist_param_names):
    """Format and return the distribution expression.

    Arguments:
        raw_expr (str): the function expression to be formatted
        value (float): the value to be put in the expression
        dist_param_names (list): list of names of parameters that parametrise
            the distribution
    """
    if dist_param_names is not None:
        raise NotImplementedError(
            "Functions that depend on other parameters, "
            "like decay function, are not implemented yet."
        )
    new_expr = raw_expr.format(distance="p", value=value)
    if "math" in new_expr:
        new_expr = new_expr.replace("math.", "")
    if "(p)" in new_expr:
        new_expr = new_expr.replace("(p)", "p")

    return new_expr


def add_nml_channel_to_nml_cell_file(
    cell_doc,
    included_channels,
    channel_name=None,
    channel_nml2_file=None,
    channel_dir="channels",
    skip_channels_copy=False,
):
    """Add NeuroML channel file to NeuroML cell file.

    And copy channel in the current directory.

    Arguments:
        cell_doc (NeuroMLDocument): nml document of the cell model
        included_channels (list): list of already included channels
        channel_name (str): name of the channel
        channel_nml2_file (str): name of the neuroml channel file
        channel_dir (str): repo in which to copy the channel files
        skip_channels_copy (bool): True to skip the copy pasting
            of the neuroml channel files
    """
    if channel_nml2_file is None:
        if channel_name is None:
            raise ValueError(
                "Plaise provide either a channel name or a channel nml2 file."
            )
        channel_nml2_file = f"{channel_name}.channel.nml"

    if channel_nml2_file not in included_channels:
        channel_new_path = Path(channel_dir) / channel_nml2_file
        cell_doc.includes.append(neuroml.IncludeType(href=channel_new_path))

        # for some reason, pynml cannot accept absolute paths in IncludeType,
        # so copy paste files in current directory for the simulation to work
        if not skip_channels_copy:
            Path(channel_dir).mkdir(exist_ok=True)
            nml_mech_dir = Path(get_nml_mech_dir())
            channel_path = nml_mech_dir / channel_nml2_file
            if channel_path.is_file():
                shutil.copy(channel_path, channel_new_path)

        included_channels.append(channel_nml2_file)


def get_channel_ion(channel, custom_channel_ion=None):
    """Get ion name given channel name.

    Arguments:
        channel (str): ion channel (e.g. StochKv)
        custom_channel_ion (dict): dict mapping channel to ion
    """
    ion = channel_ions.get(channel, None)
    if ion is None and custom_channel_ion is not None:
        ion = custom_channel_ion.get(channel, None)
    if ion is None:
        raise KeyError(
            f"Ion not found for channel {channel}."
            " Please set channel-ion mapping using custom_channel_ion."
        )
    return ion


def get_erev(ion, custom_ion_erevs=None):
    """Get reversal potential as str given ion name.

    Arguments:
        ion (str): ion name (e.g. na)
        custom_ion_erevs (dict): dict mapping ion to erev (reversal potential)
    """
    erev = ion_erevs.get(ion, None)
    if erev is None and custom_ion_erevs is not None:
        erev = custom_ion_erevs.get(ion, None)
    if erev is None:
        raise KeyError(
            f"Reversal potential not found for ion {ion}."
            " Please set ion-erev mapping using custom_ion_erevs."
        )
    return erev


def get_arguments(
    params,
    parameter_name,
    section_list,
    channel,
    channel_name,
    variable_parameters,
    cond_density,
    release_params,
    custom_channel_ion=None,
    custom_ion_erevs=None,
):
    """Get arguments for channel density function.

    Arguments:
        params (dict): contains the cell's parameters
        parameter_name (str): name of the parameter (e.g. e_pas)
        section_list (str): name of the location of the parameter (e.g. axonal)
        channel (str): ion channel (e.g. StochKv)
        channel_name (str): ion channel name used in the neuroML channel file
            (e.g. StochKv_deterministic)
        variable_parameters (list of neuroml.VariableParameter):
            parameters for non-uniform distributions
        cond_density (str): conductance density
        release_params (dict): optimized parameters
        custom_channel_ion (dict): dict mapping channel to ion
        custom_ion_erevs (dict): dict mapping ion to erev (reversal potential)
    """
    arguments = {}

    arguments["ion"] = get_channel_ion(channel, custom_channel_ion)
    erev = get_erev(arguments["ion"], custom_ion_erevs)

    channel_class = "ChannelDensity"

    if erev == "nernst":
        erev = None
        channel_class = "ChannelDensityNernst"
    elif erev == "pas":
        erev = params[f"e_pas.{section_list}"].value
        if erev is None:
            # non frozen parameter
            erev = release_params[f"e_pas.{section_list}"]
        erev = f"{erev} mV"
        arguments["ion"] = "non_specific"

    if variable_parameters is not None:
        channel_class += "NonUniform"
    else:
        arguments["segment_groups"] = section_list

    if erev is not None:
        arguments["erev"] = erev
    arguments["id"] = f"{section_list}_{parameter_name}"
    if cond_density is not None:
        arguments["cond_density"] = cond_density
    arguments["ion_channel"] = channel_name
    if variable_parameters is not None:
        arguments["variable_parameters"] = variable_parameters

    return arguments, channel_class


def extract_parameter_value(
    parameter, section_list, channel, skip_non_uniform, release_params
):
    """Returns conductance density and variable parameters.

    Arguments:
        parameter (ephys.parameters)
        section_list (str): location
        channel (str): ion channel
        skip_non_uniform (bool): True to skip non uniform distributions
        release_params (dict): optimized parameters
    """
    cond_density = None
    variable_parameters = None

    # uniform
    if isinstance(
        parameter.value_scaler, ephys.parameterscalers.NrnSegmentLinearScaler
    ):
        value = parameter.value
        if value is None:
            # non frozen parameter
            value = release_params[parameter.name]
        if channel in density_scales:
            value = value * density_scales[channel]
        cond_density = f"{value} S_per_cm2"
    # non uniform
    elif not skip_non_uniform:
        value = parameter.value
        if value is None:
            # non frozen parameter
            value = release_params[parameter.name]
        # did not mulyiply by 1e4. Is that ok?
        new_expr = format_dist_fun(
            raw_expr=parameter.value_scaler.distribution,
            value=value,
            dist_param_names=parameter.value_scaler.dist_param_names,
        )

        iv = neuroml.InhomogeneousValue(
            inhomogeneous_parameters=f"PathLengthOver_{section_list}",
            value=new_expr,
        )
        variable_parameters = [
            neuroml.VariableParameter(
                segment_groups=section_list,
                parameter="condDensity",
                inhomogeneous_value=iv,
            )
        ]
    else:
        return None, None

    return cond_density, variable_parameters


def get_density(
    cell_doc,
    cell,
    parameter,
    section_list,
    included_channels,
    skip_non_uniform,
    release_params,
    skip_channels_copy,
    custom_channel_ion=None,
    custom_ion_erevs=None,
):
    """Return density.

    Arguments:
        cell_doc (NeuroMLDocument): nml document of the cell model
        cell (ephys.CellModel): bluepyopt cell
        parameter (ephys.parameters)
        section_list (str): location
        included_channels (list): list of channels already included
            in the nml file
        skip_non_uniform (bool): True to skip non uniform distributions
        release_params (dict): optimized parameters
        skip_channels_copy (bool): True to skip the copy pasting
            of the neuroml channel files
        custom_channel_ion (dict): dict mapping channel to ion
        custom_ion_erevs (dict): dict mapping ion to erev (reversal potential)
    """
    channel = get_channel_from_param_name(parameter.param_name)

    cond_density, variable_parameters = extract_parameter_value(
        parameter, section_list, channel, skip_non_uniform, release_params
    )
    if cond_density is None and variable_parameters is None:
        return None, None

    channel_name = channel
    if channel in channel_substitutes:
        channel_name = channel_substitutes[channel]

    # add nml channel to nml cell file
    add_nml_channel_to_nml_cell_file(
        cell_doc,
        included_channels,
        channel_name=channel_name,
        skip_channels_copy=skip_channels_copy,
    )

    arguments, channel_class = get_arguments(
        params=cell.params,
        parameter_name=parameter.param_name,
        section_list=section_list,
        channel=channel,
        channel_name=channel_name,
        variable_parameters=variable_parameters,
        cond_density=cond_density,
        release_params=release_params,
        custom_channel_ion=custom_channel_ion,
        custom_ion_erevs=custom_ion_erevs,
    )

    density = getattr(neuroml, channel_class)(**arguments)

    return density, channel_class


def get_specific_capacitance(capacitance_overwrites):
    """Returns the specific capacitance.

    Arguments:
        capacitance_overwrites (dict): capacitance values from parameters
            to overwrites default ones.
    """
    specific_capacitances = []
    for section_list in default_capacitances:
        if section_list in capacitance_overwrites:
            capacitance = capacitance_overwrites[section_list]
        elif "all" in capacitance_overwrites:
            capacitance = capacitance_overwrites["all"]
        else:
            capacitance = default_capacitances[section_list]

        specific_capacitances.append(
            neuroml.SpecificCapacitance(
                value=capacitance, segment_groups=section_list
            )
        )

    return specific_capacitances


def get_biophys(
    cell,
    cell_doc,
    release_params,
    skip_non_uniform=False,
    skip_channels_copy=False,
    custom_channel_ion=None,
    custom_ion_erevs=None,
):
    """Get biophys in neuroml format.

    Arguments:
        cell (ephys.CellModel): bluepyopt cell
        cell_doc (NeuroMLDocument): nml document of the cell model
        release_params (dict): optimized parameters
        skip_non_uniform (bool): True to skip non uniform distributions
        skip_channels_copy (bool): True to skip the copy pasting
            of the neuroml channel files
        custom_channel_ion (dict): dict mapping channel to ion
        custom_ion_erevs (dict): dict mapping ion to erev (reversal potential)
    """
    concentrationModels = {}

    # Membrane properties
    included_channels = []
    channel_densities = []
    channel_density_nernsts = []
    channel_density_non_unif_nernsts = []
    channel_density_non_uniforms = []
    species = []

    capacitance_overwrites = {}

    for parameter in cell.params.values():
        if not (
            isinstance(parameter, ephys.parameters.NrnGlobalParameter)
            or isinstance(parameter, ephys.parameters.MetaParameter)
        ):
            for location in parameter.locations:
                section_list = location.seclist_name

                if (
                    parameter.param_name != "e_pas"
                    and "CaDynamics_E2" not in parameter.param_name
                    and parameter.param_name not in ignore_params
                ):
                    density, channel_class = get_density(
                        cell_doc,
                        cell,
                        parameter,
                        section_list,
                        included_channels,
                        skip_non_uniform,
                        release_params,
                        skip_channels_copy,
                        custom_channel_ion,
                        custom_ion_erevs,
                    )

                    if density is not None:
                        # add density to list of densities
                        if channel_class == "ChannelDensityNernst":
                            channel_density_nernsts.append(density)
                        elif (
                            channel_class == "ChannelDensityNernstNonUniform"
                        ):
                            channel_density_non_unif_nernsts.append(
                                density
                            )
                        elif channel_class == "ChannelDensityNonUniform":
                            channel_density_non_uniforms.append(density)
                        else:
                            channel_densities.append(density)

                elif "gamma_CaDynamics_E2" in parameter.param_name:
                    model = f"CaDynamics_E2_NML2__{cell.name}_{section_list}"
                    value = parameter.value
                    if value is None:
                        # non frozen parameter
                        value = release_params[parameter.name]

                    if model not in concentrationModels:
                        concentrationModels[model] = {}
                    concentrationModels[model]["gamma"] = value

                elif "decay_CaDynamics_E2" in parameter.param_name:
                    model = f"CaDynamics_E2_NML2__{cell.name}_{section_list}"
                    species.append(
                        neuroml.Species(
                            id="ca",
                            ion="ca",
                            initial_concentration="5.0E-11 mol_per_cm3",
                            initial_ext_concentration="2.0E-6 mol_per_cm3",
                            concentration_model=model,
                            segment_groups=section_list,
                        )
                    )

                    channel_nml2_file = "CaDynamics_E2_NML2.nml"
                    add_nml_channel_to_nml_cell_file(
                        cell_doc,
                        included_channels,
                        channel_nml2_file=channel_nml2_file,
                    )

                    value = parameter.value
                    if value is None:
                        # non frozen parameter
                        value = release_params[parameter.name]

                    if model not in concentrationModels:
                        concentrationModels[model] = {}
                    concentrationModels[model]["decay"] = value

                elif parameter.param_name == "cm":
                    capacitance_overwrites[
                        section_list
                    ] = f"{parameter.value} uF_per_cm2"

    # append new concentrations to the CaDynamics_E2_NML2.nml file
    if concentrationModels and not skip_channels_copy:
        adapt_CaDynamics_nml(concentrationModels)

    specific_capacitances = get_specific_capacitance(capacitance_overwrites)

    v_init = cell.params["v_init"].value
    init_memb_potentials = [
        neuroml.InitMembPotential(value=f"{v_init} mV", segment_groups="all")
    ]

    membrane_properties = neuroml.MembraneProperties(
        channel_densities=channel_densities,
        channel_density_nernsts=channel_density_nernsts,
        channel_density_non_uniform_nernsts=channel_density_non_unif_nernsts,
        channel_density_non_uniforms=channel_density_non_uniforms,
        specific_capacitances=specific_capacitances,
        init_memb_potentials=init_memb_potentials,
    )

    # Intracellular Properties
    Ra = cell.params["Ra.all"].value
    resistivities = [
        neuroml.Resistivity(value=f"{Ra} ohm_cm", segment_groups="all")
    ]

    intracellular_properties = neuroml.IntracellularProperties(
        resistivities=resistivities,
        species=species,
    )

    # Biophysical Properties
    biophysical_properties = neuroml.BiophysicalProperties(
        id="biophys",
        intracellular_properties=intracellular_properties,
        membrane_properties=membrane_properties,
    )

    return biophysical_properties
