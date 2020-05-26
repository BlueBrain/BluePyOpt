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
import json

import l5pc_model  # NOQA

import bluepyopt.ephys as ephys

import LFPy

script_dir = os.path.dirname(__file__)
config_dir = os.path.join(script_dir, 'config')

# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format


def define_protocols(electrode=None):
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
        
        # Add LFP recording
        if electrode is not None:
            recordings.append(
                ephys.recordings.LFPRecording('%s.MEA.LFP' % protocol_name)
            )

        stimuli = []
        for stimulus_definition in protocol_definition['stimuli']:
            stimuli.append(ephys.stimuli.LFPySquarePulse(
                step_amplitude=stimulus_definition['amp'],
                step_delay=stimulus_definition['delay'],
                step_duration=stimulus_definition['duration'],
                location=soma_loc,
                total_duration=stimulus_definition['totduration']))

        protocols[protocol_name] = ephys.protocols.SweepProtocol(
            protocol_name,
            stimuli,
            recordings,
            cvode_active=True)

    return protocols


def define_fitness_calculator(protocols, feature_set='bap', probe=None):
    """Define fitness calculator"""

    assert feature_set in ['bap', 'soma', 'extra']

    feature_definitions = json.load(
        open(
            os.path.join(
                config_dir,
                'features.json')))[feature_set]

    if feature_set == 'extra':
        assert probe is not None, "Provide a MEAutility probe to use the 'extra' set"

    objectives = []

    for protocol_name, locations in feature_definitions.items():
        for location, features in locations.items():
            for efel_feature_name, meanstd in features.items():
                feature_name = '%s.%s.%s' % (
                    protocol_name, location, efel_feature_name)
                kwargs = {}

                stimulus = protocols[protocol_name].stimuli[0]
                kwargs['stim_start'] = stimulus.step_delay

                if location == 'soma':
                    kwargs['threshold'] = -20
                elif 'dend' in location:
                    kwargs['threshold'] = -55
                else:
                    kwargs['threshold'] = -20

                if protocol_name == 'bAP':
                    kwargs['stim_end'] = stimulus.total_duration
                else:
                    kwargs['stim_end'] = stimulus.step_delay + stimulus.step_duration

                if location == 'MEA':
                    feature_class = ephys.efeatures.extraFELFeature
                    kwargs['recording_names'] = {'': '%s.%s.LFP' % (protocol_name, location)}
                    kwargs['fs'] = 20
                    kwargs['fcut'] = 1
                    kwargs['somatic_recording_name'] = f'{protocol_name}.soma.v'
                    if efel_feature_name != 'velocity':
                        kwargs['channel_id'] = int(efel_feature_name.split('_')[-1])
                    kwargs['channel_locations'] = probe.positions
                    kwargs['fs'] = 20
                    kwargs['extrafel_feature_name'] = ['_'.join(efel_feature_name.split('_')[:-1])]
                else:
                    feature_class = ephys.efeatures.eFELFeature
                    kwargs['efel_feature_name'] = [efel_feature_name]
                    kwargs['recording_names'] = {'': '%s.%s.v' % (protocol_name, location)}

                feature = feature_class(
                    feature_name,
                    exp_mean=meanstd[0],
                    exp_std=meanstd[1],
                    **kwargs)
                objective = ephys.objectives.SingletonObjective(
                    feature_name,
                    feature)
                objectives.append(objective)

    fitcalc = ephys.objectivescalculators.ObjectivesCalculator(objectives)

    return fitcalc


def define_electrode():
    """Define electrode"""
    import MEAutility as mu

    sq_mea = mu.return_mea('SqMEA-10-15')
    sq_mea.rotate([0, 1, 0], 90)
    sq_mea.move([0, 0, -50])

    electrode = LFPy.RecExtElectrode(probe=sq_mea)

    return electrode


def create():
    """Setup"""

    l5pc_cell = l5pc_model.create()

    electrode = define_electrode()
    sim = ephys.simulators.LFPySimulator(LFPyCellModel=l5pc_cell,
                                         electrode=electrode)
    
    fitness_protocols = define_protocols(electrode=electrode)
    fitness_calculator = define_fitness_calculator(fitness_protocols)
    
    param_names = [param.name
                   for param in l5pc_cell.params.values()
                   if not param.frozen]
    
    return ephys.evaluators.CellEvaluator(
        cell_model=l5pc_cell,
        param_names=param_names,
        fitness_protocols=fitness_protocols,
        fitness_calculator=fitness_calculator,
        sim=sim)
