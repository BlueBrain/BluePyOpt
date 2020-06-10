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
import numpy as np
from pathlib import Path

import l5pc_model  # NOQA
import bluepyopt as bpopt

import bluepyopt.ephys as ephys

import LFPy
import numpy as np

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


def compute_feature_values(params, cell_model, protocols, sim, feature_set='bap', std=0.2,
                           feature_folder='config/features', probe=None, channels=None):
    """Compute feature values based on params"""

    assert feature_set in ['bap', 'soma', 'extra']

    feature_list = json.load(
        open(os.path.join(config_dir, 'features_list.json')))[feature_set]

    if feature_set == 'extra':
        assert probe is not None, "Provide a MEAutility probe to use the 'extra' set"
        if channels is None:
            channels = np.arange(probe.number_electrodes)

    features = {}

    for protocol_name, locations in feature_list.items():
        features[protocol_name] = []
        for location, feats in locations.items():
            for efel_feature_name in feats:
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
                    kwargs['ms_cut'] = [3, 10]
                    kwargs['upsample'] = 10
                    kwargs['somatic_recording_name'] = f'{protocol_name}.soma.v'
                    kwargs['channel_locations'] = probe.positions
                    kwargs['extrafel_feature_name'] = efel_feature_name
                    if efel_feature_name != 'velocity':
                        for ch in channels:
                            kwargs['channel_id'] = int(ch)
                            feature = feature_class(
                                feature_name,
                                exp_mean=0,
                                exp_std=0,
                                **kwargs)
                            features[protocol_name].append(feature)
                    else:
                        feature = feature_class(
                            feature_name,
                            exp_mean=0,
                            exp_std=0,
                            **kwargs)
                        features[protocol_name].append(feature)
                else:
                    feature_class = ephys.efeatures.eFELFeature
                    kwargs['efel_feature_name'] = efel_feature_name
                    kwargs['recording_names'] = {'': '%s.%s.v' % (protocol_name, location)}

                    feature = feature_class(
                        feature_name,
                        exp_mean=0,
                        exp_std=0,
                        **kwargs)
                    features[protocol_name].append(feature)
    responses = {}

    for protocol_name, protocol in protocols.items():
        print('Running', protocol_name)
        responses.update(protocol.run(cell_model=cell_model, param_values=params, sim=sim))

    feature_meanstd = {}
    std = 0.2
    for protocol_name, featlist in features.items():
        print(protocol_name, 'Num features:', len(featlist))

        mean_std = {}
        for feat in featlist:
            prot, location, name = feat.name.split('.')
            val = feat.calculate_feature(responses)
            if val is not None:
                if isinstance(feat, ephys.efeatures.eFELFeature):
                    feat_name = name
                else:
                    feat_name = f'{name}_{str(feat.channel_id)}'
                if location not in mean_std.keys():
                    mean_std[location] = {}
                mean_std[location][feat_name] = [val, np.abs(std * val)]
        feature_meanstd[protocol_name] = mean_std

    feature_folder = Path(feature_folder)
    if not feature_folder.is_dir():
        os.makedirs(feature_folder)

    feature_file = feature_folder / f'{feature_set}.json'

    with feature_file.open('w') as f:
        json.dump(feature_meanstd, f, indent=4)

    return str(feature_file)


def define_fitness_calculator(protocols, feature_file=None, feature_set=None, probe=None):
    """Define fitness calculator"""

    assert feature_file is not None or feature_set is not None
    if feature_set is not None:
        assert feature_set in ['bap', 'soma', 'extra']

        feature_definitions = json.load(
            open(
                os.path.join(
                    config_dir,
                    'features.json')))[feature_set]
    else:
        feature_definitions = json.load(open(feature_file))

    if feature_set == 'extra' or 'extra' in feature_file:
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
                    kwargs['ms_cut'] = [3, 10]
                    kwargs['upsample'] = 10
                    kwargs['somatic_recording_name'] = f'{protocol_name}.soma.v'
                    if efel_feature_name != 'velocity':
                        kwargs['channel_id'] = int(efel_feature_name.split('_')[-1])
                        kwargs['extrafel_feature_name'] = '_'.join(efel_feature_name.split('_')[:-1])
                    else:
                        kwargs['extrafel_feature_name'] = efel_feature_name
                    kwargs['channel_locations'] = probe.positions
                else:
                    feature_class = ephys.efeatures.eFELFeature
                    kwargs['efel_feature_name'] = efel_feature_name
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

    mea_positions = np.zeros((5, 3))
    mea_positions[:, 2] = 20
    mea_positions[:, 1] = np.linspace(0, 900, 5)
    probe = mu.return_mea(info={'pos': mea_positions, 'center': False, 'plane': 'xy'})
    electrode = LFPy.RecExtElectrode(probe=probe, method='linesource')
    
    return electrode, probe


def create(feature_set):
    """Setup"""
    
    electrode, probe = define_electrode()

    feature_set = "extra" # 'soma'/'bap'

    morphology = ephys.morphologies.NrnFileMorphology('morphology/C060114A7.asc', do_replace_axon=True)
    param_configs = json.load(open('config/parameters.json'))
    parameters = l5pc_model.define_parameters()
    mechanisms = l5pc_model.define_mechanisms()

    l5pc_cell = ephys.models.LFPyCellModel('l5pc', 
                                           v_init=-65., 
                                           morph=morphology, 
                                           mechs=mechanisms, 
                                           params=parameters)

    param_names = [param.name for param in l5pc_cell.params.values() if not param.frozen]      

    if feature_set == "extra":
        fitness_protocols = define_protocols(electrode) 
    else:
        fitness_protocols = define_protocols() 

    fitness_calculator = define_fitness_calculator(fitness_protocols, 
                                                   feature_set=feature_set, 
                                                   probe=probe)

    if feature_set == "extra":
        sim = ephys.simulators.LFPySimulator(LFPyCellModel=l5pc_cell, cvode_active=True, electrode=electrode)
    else:
        sim = ephys.simulators.LFPySimulator(LFPyCellModel=l5pc_cell, cvode_active=True)

    evaluator = ephys.evaluators.CellEvaluator(                                          
                    cell_model=l5pc_cell,                                                       
                    param_names=param_names,                                                    
                    fitness_protocols=fitness_protocols,                                        
                    fitness_calculator=fitness_calculator,                                      
                    sim=sim)  
    
    return evaluator

