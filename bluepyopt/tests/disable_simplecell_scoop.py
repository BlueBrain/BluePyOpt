'''
Note: this is a bizarre test due to the fact that scoop can't be started from
within python:
https://github.com/soravux/scoop/issues/29

Therefore, the way this works is for the test_ that's detected by nt then
creates a subprocess that runs scoop using the normal command line arguments

It then captures the output, and looks for the BEST: magic string which
should match the precomputed output
'''

import os
import nose.tools as nt
import subprocess

import bluepyopt as nrp
import bluepyopt.ephys as nrpel

SIMPLE_SWC = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          '../../examples/simplecell/simple.swc')


# Disabled this test. Doesn't work on a mac for some reason
# Error message: can't import scoop
# TODO Renable once this is fixed
def disabled_scoop():
    """Simplecell: test scoop"""
    cmd = ['python', '-m', 'scoop', '-n', '2', __file__]
    output = subprocess.check_output(cmd)
    for line in output.split('\n'):
        if line.startswith('BEST'):
            break
    nt.eq_(line, 'BEST: [0.11268238279399023, 0.038129859413828474]')


# The rest defines the optimization we run with scoop

morph = nrpel.morphologies.NrnFileMorphology(SIMPLE_SWC)
somatic_loc = nrpel.locations.NrnSeclistLocation('somatic',
                                                 seclist_name='somatic')

hh_mech = nrpel.mechanisms.NrnMODMechanism(name='hh',
                                           suffix='hh',
                                           locations=[somatic_loc])

cm_param = nrpel.parameters.NrnSectionParameter(name='cm',
                                                param_name='cm',
                                                value=1.0,
                                                locations=[somatic_loc],
                                                frozen=True)


gnabar_param = nrpel.parameters.NrnSectionParameter(name='gnabar_hh',
                                                    param_name='gnabar_hh',
                                                    locations=[somatic_loc],
                                                    bounds=[0.05, 0.125],
                                                    frozen=False)

gkbar_param = nrpel.parameters.NrnSectionParameter(name='gkbar_hh',
                                                   param_name='gkbar_hh',
                                                   bounds=[0.01, 0.075],
                                                   locations=[somatic_loc],
                                                   frozen=False)

simple_cell = nrpel.celltemplate.CellTemplate(name='simple_cell',
                                              morph=morph,
                                              mechs=[hh_mech],
                                              params=[cm_param,
                                                      gnabar_param,
                                                      gkbar_param])

soma_loc = nrpel.locations.NrnSeclistCompLocation(name='soma',
                                                  seclist_name='somatic',
                                                  sec_index=0,
                                                  comp_x=0.5)

protocols = {}
for protocol_name, amplitude in [('step1', 0.01), ('step2', 0.05)]:
    stim = nrpel.stimuli.NrnSquarePulse(step_amplitude=amplitude,
                                        step_delay=100,
                                        step_duration=50,
                                        location=soma_loc,
                                        total_duration=200)
    rec = nrpel.recordings.CompRecording(name='%s.soma.v' % protocol_name,
                                         location=soma_loc,
                                         variable='v')
    protocol = nrpel.protocols.Protocol(protocol_name, [stim], [rec])
    protocols[protocol.name] = protocol


default_params = {'gnabar_hh': 0.1, 'gkbar_hh': 0.03}
responses = simple_cell.run_protocols(protocols,
                                      param_values=default_params)

efel_feature_means = {'step1': {'Spikecount': 1}, 'step2': {'Spikecount': 5}}

objectives = []

for protocol_name, protocol in protocols.items():
    stim_start = protocol.stimuli[0].step_delay
    stim_end = stim_start + protocol.stimuli[0].step_duration
    for efel_feature_name, mean in \
            efel_feature_means[protocol_name].items():
        feature_name = '%s.%s' % (protocol_name, efel_feature_name)
        feature = nrpel.efeatures.eFELFeature(
            feature_name,
            efel_feature_name=efel_feature_name,
            recording_names={'': '%s.soma.v' % protocol_name},
            stim_start=stim_start,
            stim_end=stim_end,
            exp_mean=mean,
            exp_std=0.05 * mean)
        objective = objective = nrpel.objectives.SingletonObjective(
            feature_name,
            feature)
        objectives.append(objective)


score_calc = nrpel.scorecalculators.ObjectivesScoreCalculator(objectives)
cell_evaluator = nrpel.cellevaluator.CellEvaluator(
    cell_template=simple_cell,
    param_names=[
        'gnabar_hh',
        'gkbar_hh'],
    fitness_protocols=protocols,
    fitness_calculator=score_calc)

optimisation = nrp.Optimisation(
    evaluator=cell_evaluator,
    eval_function=cell_evaluator.evaluate_with_lists,
    offspring_size=10,
    use_scoop=True)

if __name__ == '__main__':
    final_pop, hall_of_fame, logs, hist = optimisation.run(max_ngen=2)
    print('BEST:', hall_of_fame[0])
