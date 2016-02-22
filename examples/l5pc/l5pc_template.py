"""Run simple cell optimisation"""

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
# pylint: disable=R0914

import os
import collections

import bluepyopt.ephys as ephys
import bluepyopt.ephys.celltemplate as ct

script_dir = os.path.dirname(__file__)

# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format


def define_mechanisms():
    """Define mechanisms"""

    import json
    with open(os.path.join(script_dir, 'mechanisms.json')) as mech_file:
        mech_definitions = json.load(mech_file)

    mechanisms = []
    for sectionlist, channels in mech_definitions.iteritems():
        seclist_loc = ephys.locations.NrnSeclistLocation(
            sectionlist,
            seclist_name=sectionlist)
        for channel in channels:
            mechanisms.append(ephys.mechanisms.NrnMODMechanism(
                name='%s.%s' % (channel, sectionlist),
                mod_path=None,
                prefix=channel,
                locations=[seclist_loc],
                preloaded=True))

    return mechanisms


def define_parameters():
    """Define parameters"""

    import json
    parameters = []

    # TODO put exp equation in file

    uniform_scaler = ephys.parameterscalers.NrnSegmentLinearScaler()
    exponential_scaler = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
        distribution='(-0.8696 + 2.087*math.exp(({distance})*0.0031))*{value}')

    # Fixed section parameters
    # TODO check the order of executions of all parameters

    with open(os.path.join(script_dir, 'fixed_params.json'), 'r') as \
            fixed_params_file:
        fixed_params_definitions = json.load(
            fixed_params_file,
            object_pairs_hook=collections.OrderedDict)

    for sectionlist, params in fixed_params_definitions.iteritems():
        if sectionlist == 'global':
            for param_name, value in params:
                parameters.append(
                    ephys.parameters.NrnGlobalParameter(
                        name=param_name,
                        param_name=param_name,
                        frozen=True,
                        value=value))
        else:
            seclist_loc = ephys.locations.NrnSeclistLocation(
                sectionlist,
                seclist_name=sectionlist)

            for param_name, value, dist in params:
                parameters.append(ephys.parameters.NrnSectionParameter(
                    name='%s.%s' % (param_name, sectionlist),
                    param_name=param_name,
                    value_scaler=uniform_scaler,
                    value=value,
                    frozen=True,
                    locations=[seclist_loc]))

    # Compact parameter description
    # Format ->
    # - Root dictionary: keys = section list name,
    #                    values = parameter description array
    # - Parameter description array: prefix, parameter name, minbound, maxbound

    with open(os.path.join(script_dir, 'params.json'), 'r') as parameter_file:
        parameter_definitions = json.load(
            parameter_file,
            object_pairs_hook=collections.OrderedDict)

    for sectionlist, params in parameter_definitions.iteritems():
        seclist_loc = ephys.locations.NrnSeclistLocation(
            sectionlist,
            seclist_name=sectionlist)

        for prefix, param_name, min_bound, max_bound, dist in params:
            if dist == 'uniform':
                scaler = uniform_scaler
            elif dist == 'exp':
                scaler = exponential_scaler
            parameters.append(ephys.parameters.NrnRangeParameter(
                name='%s_%s.%s' % (param_name, prefix, sectionlist),
                param_name='%s_%s' % (param_name, prefix),
                value_scaler=scaler,
                bounds=[min_bound, max_bound],
                locations=[seclist_loc]))

    return parameters


def define_morphology():
    """Define morphology"""

    return ephys.morphologies.NrnFileMorphology(
        os.path.join(
            script_dir,
            'morphology/C060114A7.asc'),
        do_replace_axon=True)


def create():
    """Create cell template"""

    cell = ct.CellTemplate(
        'l5pc',
        morph=define_morphology(),
        mechs=define_mechanisms(),
        params=define_parameters())

    return cell
