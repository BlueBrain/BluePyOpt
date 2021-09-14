"""Simple cell test model"""

import os

import bluepyopt.ephys as ephys


class SimpleCell:
    def __init__(self):
        self.nrn_sim = ephys.simulators.NrnSimulator()

        self.morph = ephys.morphologies.NrnFileMorphology(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'simple.swc'))
        self.somatic_loc = ephys.locations.NrnSeclistLocation(
            'somatic',
            seclist_name='somatic')
        self.somacenter_loc = ephys.locations.NrnSeclistCompLocation(
            name='somacenter',
            seclist_name='somatic',
            sec_index=0,
            comp_x=0.5)
        self.hh_mech = ephys.mechanisms.NrnMODMechanism(
            name='hh',
            suffix='hh',
            locations=[self.somatic_loc])

        self.cm_param = ephys.parameters.NrnSectionParameter(
            name='cm',
            param_name='cm',
            value=1.0,
            locations=[self.somatic_loc],
            frozen=True)

        self.gnabar_param = ephys.parameters.NrnSectionParameter(
            name='gnabar_hh',
            param_name='gnabar_hh',
            locations=[self.somatic_loc],
            bounds=[0.05, 0.125],
            frozen=False)
        self.gkbar_param = ephys.parameters.NrnSectionParameter(
            name='gkbar_hh',
            param_name='gkbar_hh',
            bounds=[0.01, 0.075],
            locations=[self.somatic_loc],
            frozen=False)

        self.cell_model = ephys.models.CellModel(
            name='simple_cell',
            morph=self.morph,
            mechs=[self.hh_mech],
            params=[self.cm_param, self.gnabar_param, self.gkbar_param])

        self.default_param_values = {'gnabar_hh': 0.1, 'gkbar_hh': 0.03}

        self.efel_feature_means = {
            'step1': {
                'Spikecount': 1}, 'step2': {
                'Spikecount': 5}}

        self.objectives = []

        self.soma_loc = ephys.locations.NrnSeclistCompLocation(
            name='soma',
            seclist_name='somatic',
            sec_index=0,
            comp_x=0.5)

        self.stim = ephys.stimuli.NrnSquarePulse(
            step_amplitude=0.01,
            step_delay=100,
            step_duration=50,
            location=self.soma_loc,
            total_duration=200)
        self.rec = ephys.recordings.CompRecording(
            name='Step1.soma.v',
            location=self.soma_loc,
            variable='v')
        self.protocol = ephys.protocols.SweepProtocol(
            'Step1', [self.stim], [self.rec])

        self.stim_start = 100
        self.stim_end = 150

        self.feature_name = 'Step1.Spikecount'
        self.feature = ephys.efeatures.eFELFeature(
            self.feature_name,
            efel_feature_name='Spikecount',
            recording_names={'': '%s.soma.v' % self.protocol.name},
            stim_start=self.stim_start,
            stim_end=self.stim_end,
            exp_mean=1.0,
            exp_std=0.05)
        self.objective = ephys.objectives.SingletonObjective(
            self.feature_name,
            self.feature)

        self.score_calc = \
            ephys.objectivescalculators.ObjectivesCalculator([self.objective])

        self.nrn = ephys.simulators.NrnSimulator()

        self.cell_evaluator = ephys.evaluators.CellEvaluator(
            cell_model=self.cell_model,
            param_names=['gnabar_hh', 'gkbar_hh'],
            fitness_protocols={'Step1': self.protocol},
            fitness_calculator=self.score_calc,
            sim=self.nrn)
