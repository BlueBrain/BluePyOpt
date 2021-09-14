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

import os
import collections

try:
    import simplejson as json
except ImportError:
    import json

import bluepyopt.ephys as ephys


import logging
logger = logging.getLogger(__name__)



import random

def multi_locations(sectionlist):
    """Define mechanisms"""

    if sectionlist == "alldend":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal")
        ]
    elif sectionlist == "somadend":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation(
                "basal", seclist_name="basal"),
            ephys.locations.NrnSeclistLocation(
                "somatic", seclist_name="somatic")
        ]
    elif sectionlist == "somaxon":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation(
                "axonal", seclist_name="axonal"),
            ephys.locations.NrnSeclistLocation(
                "somatic", seclist_name="somatic")
        ]
    elif sectionlist == "allact":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation(
                "basal", seclist_name="basal"),
            ephys.locations.NrnSeclistLocation(
                "somatic", seclist_name="somatic"),
            ephys.locations.NrnSeclistLocation(
                "axonal", seclist_name="axonal")
        ]
    else:
        seclist_locs = [ephys.locations.NrnSeclistLocation(
            sectionlist,
            seclist_name=sectionlist)]

    return seclist_locs


def define_mechanisms(params_filename):
    """Define mechanisms"""

    with open(os.path.join(os.path.dirname(__file__), '..', params_filename)) as params_file:
        mech_definitions = json.load(
            params_file,
            object_pairs_hook=collections.OrderedDict)["mechanisms"]

    mechanisms_list = []
    for sectionlist, channels in mech_definitions.items():

        seclist_locs = multi_locations(sectionlist)

        for channel in channels["mech"]:
            mechanisms_list.append(ephys.mechanisms.NrnMODMechanism(
                name='%s.%s' % (channel, sectionlist),
                mod_path=None,
                prefix=channel,
                locations=seclist_locs,
                preloaded=True))

    return mechanisms_list


def define_parameters(params_filename):
    """Define parameters"""

    parameters = []

    with open(os.path.join(os.path.dirname(__file__), '..', params_filename)) as params_file:
        definitions = json.load(
            params_file,
            object_pairs_hook=collections.OrderedDict)

    # set distributions
    distributions = collections.OrderedDict()
    distributions["uniform"] = ephys.parameterscalers.NrnSegmentLinearScaler()

    distributions_definitions = definitions["distributions"]
    for distribution, definition in distributions_definitions.items():
        distributions[distribution] = \
            ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
                distribution=definition["fun"])

    params_definitions = definitions["parameters"]

    if "__comment" in params_definitions:
        del params_definitions["__comment"]

    for sectionlist, params in params_definitions.items():
        if sectionlist == 'global':
            seclist_locs = None
            is_global = True
        else:
            seclist_locs = multi_locations(sectionlist)
            is_global = False

        bounds = None
        value = None
        for param_config in params:
            param_name = param_config["name"]

            if isinstance(param_config["val"], (list, tuple)):
                is_frozen = False
                bounds = param_config["val"]
                value = None
            else:
                is_frozen = True
                value = param_config["val"]
                bounds = None

            if is_global:
                parameters.append(
                    ephys.parameters.NrnGlobalParameter(
                        name=param_name,
                        param_name=param_name,
                        frozen=is_frozen,
                        bounds=bounds,
                        value=value))
            else:
                if "dist" in param_config:
                    dist = distributions[param_config["dist"]]
                    use_range = True
                else:
                    dist = distributions["uniform"]
                    use_range = False

                if use_range:
                    parameters.append(ephys.parameters.NrnRangeParameter(
                        name='%s.%s' % (param_name, sectionlist),
                        param_name=param_name,
                        value_scaler=dist,
                        value=value,
                        bounds=bounds,
                        frozen=is_frozen,
                        locations=seclist_locs))
                else:
                    parameters.append(ephys.parameters.NrnSectionParameter(
                        name='%s.%s' % (param_name, sectionlist),
                        param_name=param_name,
                        value_scaler=dist,
                        value=value,
                        bounds=bounds,
                        frozen=is_frozen,
                        locations=seclist_locs))

    return parameters


from bluepyopt.ephys.morphologies import NrnFileMorphology

def define_morphology(morphology_filename, do_set_nseg=1e9):
    """Define morphology"""

    # Use default moprhology class from BluePyOpt
    return ephys.morphologies.NrnFileMorphology(
        os.path.join(morphology_filename),
        do_replace_axon=True,
        do_set_nseg=do_set_nseg)


def create(recipe, etype, altmorph=None):
    """Create cell template"""

    if altmorph is None:
        morph_path = os.path.join(os.path.join(recipe[etype]['morph_path'], recipe[etype]['morphology']))
    else:
        morph_path = altmorph

    cell = ephys.models.CellModel(
        etype,
        morph=define_morphology(morph_path, do_set_nseg=40.),
        mechs=define_mechanisms(recipe[etype]['params']),
        params=define_parameters(recipe[etype]['params']))

    return cell
