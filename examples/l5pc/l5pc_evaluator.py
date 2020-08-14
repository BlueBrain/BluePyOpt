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

import os
import json

import l5pc_model  # NOQA

import bluepyopt.ephys as ephys

script_dir = os.path.dirname(__file__)
config_dir = os.path.join(script_dir, 'config')

# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format


def define_protocols():
    """Define protocols"""

    protocol_definitions = json.load(
        open(
            os.path.join(
                config_dir,
                'protocols.json')))

    protocols = {}

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)

    for protocol_name, protocol_definition in protocol_definitions.items():
        # By default include somatic recording
        somav_recording = ephys.recordings.CompRecording(
            name='%s.soma.v' %
            protocol_name,
            location=soma_loc,
            variable='v')

        recordings = [somav_recording]

        if 'extra_recordings' in protocol_definition:
            for recording_definition in protocol_definition['extra_recordings']:
                if recording_definition['type'] == 'somadistance':
                    location = ephys.locations.NrnSomaDistanceCompLocation(
                        name=recording_definition['name'],
                        soma_distance=recording_definition['somadistance'],
                        seclist_name=recording_definition['seclist_name'])
                    var = recording_definition['var']
                    recording = ephys.recordings.CompRecording(
                        name='%s.%s.%s' % (protocol_name, location.name, var),
                        location=location,
                        variable=recording_definition['var'])

                    recordings.append(recording)
                else:
                    raise Exception(
                        'Recording type %s not supported' %
                        recording_definition['type'])

        stimuli = []
        for stimulus_definition in protocol_definition['stimuli']:
            stimuli.append(ephys.stimuli.NrnSquarePulse(
                step_amplitude=stimulus_definition['amp'],
                step_delay=stimulus_definition['delay'],
                step_duration=stimulus_definition['duration'],
                location=soma_loc,
                total_duration=stimulus_definition['totduration']))

        protocols[protocol_name] = ephys.protocols.SweepProtocol(
            protocol_name,
            stimuli,
            recordings)

    return protocols


def define_fitness_calculator(protocols):
    """Define fitness calculator"""

    feature_definitions = json.load(
        open(
            os.path.join(
                config_dir,
                'features.json')))

    # TODO: add bAP stimulus
    objectives = []

    for protocol_name, locations in feature_definitions.items():
        for location, features in locations.items():
            for efel_feature_name, meanstd in features.items():
                feature_name = '%s.%s.%s' % (
                    protocol_name, location, efel_feature_name)
                recording_names = {'': '%s.%s.v' % (protocol_name, location)}
                stimulus = protocols[protocol_name].stimuli[0]

                stim_start = stimulus.step_delay

                if location == 'soma':
                    threshold = -20
                elif 'dend' in location:
                    threshold = -55

                if protocol_name == 'bAP':
                    stim_end = stimulus.total_duration
                else:
                    stim_end = stimulus.step_delay + stimulus.step_duration

                feature = ephys.efeatures.eFELFeature(
                    feature_name,
                    efel_feature_name=efel_feature_name,
                    recording_names=recording_names,
                    stim_start=stim_start,
                    stim_end=stim_end,
                    exp_mean=meanstd[0],
                    exp_std=meanstd[1],
                    threshold=threshold)
                objective = ephys.objectives.SingletonObjective(
                    feature_name,
                    feature)
                objectives.append(objective)

    fitcalc = ephys.objectivescalculators.ObjectivesCalculator(objectives)

    return fitcalc


def create():
    """Setup"""

    l5pc_cell = l5pc_model.create()

    fitness_protocols = define_protocols()
    fitness_calculator = define_fitness_calculator(fitness_protocols)

    param_names = [param.name
                   for param in l5pc_cell.params.values()
                   if not param.frozen]

    sim = ephys.simulators.NrnSimulator()

    return ephys.evaluators.CellEvaluator(
        cell_model=l5pc_cell,
        param_names=param_names,
        fitness_protocols=fitness_protocols,
        fitness_calculator=fitness_calculator,
        sim=sim)
