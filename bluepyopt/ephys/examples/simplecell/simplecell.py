"""Simple cell test model"""

import os

import bluepyopt.ephys as ephys

nrn_sim = ephys.simulators.NrnSimulator()

morph = ephys.morphologies.NrnFileMorphology(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'simple.swc'))
somatic_loc = ephys.locations.NrnSeclistLocation(
    'somatic',
    seclist_name='somatic')
somacenter_loc = ephys.locations.NrnSeclistCompLocation(
    name='somacenter',
    seclist_name='somatic',
    sec_index=0,
    comp_x=0.5)
hh_mech = ephys.mechanisms.NrnMODMechanism(
    name='hh',
    suffix='hh',
    locations=[somatic_loc])


cm_param = ephys.parameters.NrnSectionParameter(
    name='cm',
    param_name='cm',
    value=1.0,
    locations=[somatic_loc],
    frozen=True)


gnabar_param = ephys.parameters.NrnSectionParameter(
    name='gnabar_hh',
    param_name='gnabar_hh',
    locations=[somatic_loc],
    bounds=[0.05, 0.125],
    frozen=False)
gkbar_param = ephys.parameters.NrnSectionParameter(
    name='gkbar_hh',
    param_name='gkbar_hh',
    bounds=[0.01, 0.075],
    locations=[somatic_loc],
    frozen=False)

cell_model = ephys.models.CellModel(
    name='simple_cell',
    morph=morph,
    mechs=[hh_mech],
    params=[cm_param, gnabar_param, gkbar_param])

default_param_values = {'gnabar_hh': 0.1, 'gkbar_hh': 0.03}

efel_feature_means = {'step1': {'Spikecount': 1}, 'step2': {'Spikecount': 5}}

objectives = []

soma_loc = ephys.locations.NrnSeclistCompLocation(
    name='soma',
    seclist_name='somatic',
    sec_index=0,
    comp_x=0.5)

stim = ephys.stimuli.NrnSquarePulse(
    step_amplitude=0.01,
    step_delay=100,
    step_duration=50,
    location=soma_loc,
    total_duration=200)
rec = ephys.recordings.CompRecording(
    name='Step1.soma.v',
    location=soma_loc,
    variable='v')
protocol = ephys.protocols.SweepProtocol('Step1', [stim], [rec])

stim_start = 100
stim_end = 150

feature_name = 'Step1.Spikecount'
feature = ephys.efeatures.eFELFeature(
    feature_name,
    efel_feature_name='Spikecount',
    recording_names={'': '%s.soma.v' % protocol.name},
    stim_start=stim_start,
    stim_end=stim_end,
    exp_mean=1.0,
    exp_std=0.05)
objective = ephys.objectives.SingletonObjective(
    feature_name,
    feature)

score_calc = ephys.objectivescalculators.ObjectivesCalculator([objective])

nrn = ephys.simulators.NrnSimulator()

cell_evaluator = ephys.evaluators.CellEvaluator(
    cell_model=cell_model,
    param_names=['gnabar_hh', 'gkbar_hh'],
    fitness_protocols={'Step1': protocol},
    fitness_calculator=score_calc,
    sim=nrn)
