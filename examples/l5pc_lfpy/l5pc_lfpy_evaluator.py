"""Create evaluator with LFP related efeatures"""

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
import json
import pathlib

import l5pc_lfpy_model

import bluepyopt.ephys as ephys
from bluepyopt.ephys.extra_features_utils import all_1D_features

config_dir = pathlib.Path(__file__).parents[1] / "l5pc" / "config"


extra_kwargs = dict(
    fs=20,
    fcut=[300, 6000],
    filt_type="filtfilt",
    ms_cut=[3, 5],
    upsample=10
)


def define_protocols():
    """Define protocols"""
    
    protocol_name = "Step1"

    protocol_definition = json.load(open(config_dir / "protocols.json")
                                    )[protocol_name]

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    # By default include somatic recording
    somav_recording = ephys.recordings.CompRecording(
        name="%s.soma.v" % protocol_name, location=soma_loc, variable="v"
    )
    mea_recording = ephys.recordings.LFPRecording("%s.MEA.v" % protocol_name)
    
    recordings = [somav_recording, mea_recording]

    stimuli = []
    for stimulus_definition in protocol_definition["stimuli"]:
        stimuli.append(
            ephys.stimuli.LFPySquarePulse(
                step_amplitude=stimulus_definition["amp"],
                step_delay=stimulus_definition["delay"],
                step_duration=stimulus_definition["duration"],
                location=soma_loc,
                total_duration=stimulus_definition["totduration"],
            )
        )

    return {
        protocol_name: ephys.protocols.SweepProtocol(
            protocol_name, stimuli, recordings)
    }


def get_feature_name(protocol_name, location, feature):
    return "%s.%s.%s" % (protocol_name, location, feature)


def get_recording_names(protocol_name, location=None):
    return {"": "%s.%s.v" % (protocol_name, location)}


def define_fitness_calculator(protocols, feature_file):

    with open(feature_file, "r") as f:
        feature_definitions = json.load(f)

    objectives = []
    threshold = -20

    for protocol_name in protocols:
        for location, features in feature_definitions[protocol_name].items():
            recording_names = get_recording_names(protocol_name, location)
            for efel_feature_name, meanstd in features.items():
                feature_name = get_feature_name(protocol_name, location, efel_feature_name)

                stimulus = protocols[protocol_name].stimuli[0]

                args = {
                    "name": feature_name,
                    "stim_start": stimulus.step_delay, 
                    "stim_end": stimulus.step_delay + stimulus.step_duration,
                    "exp_mean": meanstd[0],
                    "exp_std": meanstd[1],
                    "recording_names": recording_names,
                    "threshold": threshold,
                }

                if "MEA" not in location:
                    feature = ephys.efeatures.eFELFeature(
                        efel_feature_name=efel_feature_name,
                        stimulus_current=stimulus.step_amplitude,
                        **args
                    )
                else:
                    somatic_recording_name = recording_names[""].replace("MEA", "soma")
                    feature = ephys.efeatures.extraFELFeature(
                        extrafel_feature_name=efel_feature_name,
                        somatic_recording_name=somatic_recording_name,
                        channel_ids=None,
                        **args,
                        **extra_kwargs
                    )

                objective = ephys.objectives.SingletonObjective(
                    feature_name, feature
                )
                objectives.append(objective)

    return ephys.objectivescalculators.ObjectivesCalculator(objectives)


def create(feature_file="extra_features.json", cvode_active=True, dt=None):
    """Setup"""

    l5pc_cell = l5pc_lfpy_model.create()

    fitness_protocols = define_protocols()
    fitness_calculator = define_fitness_calculator(fitness_protocols, feature_file)

    param_names = [
        param.name for param in l5pc_cell.params.values() if not param.frozen
    ]

    lfpy_sim = ephys.simulators.LFPySimulator(cvode_active=cvode_active, dt=dt)

    return ephys.evaluators.CellEvaluator(
        cell_model=l5pc_cell,
        param_names=param_names,
        fitness_protocols=fitness_protocols,
        fitness_calculator=fitness_calculator,
        sim=lfpy_sim,
    )
