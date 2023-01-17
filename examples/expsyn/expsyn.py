"""Expsyn synapse parameter fitting"""

# pylint: disable=R0914


import os
import argparse

import bluepyopt as bpopt
import bluepyopt.ephys as ephys


def create_model(sim, do_replace_axon, return_locations=False):
    """Create model and optionally return locations dict"""
    if sim not in ['nrn', 'arb']:
        raise ValueError("Invalid simulator %s." % sim)

    locations = dict()

    morph = ephys.morphologies.NrnFileMorphology(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'simple.swc'),
        do_replace_axon=do_replace_axon)
    somatic_loc = ephys.locations.NrnSeclistLocation(
        'somatic',
        seclist_name='somatic')
    locations['somatic_loc'] = somatic_loc

    if sim == 'nrn':
        somacenter_loc = ephys.locations.NrnSeclistCompLocation(
            name='somacenter',
            seclist_name='somatic',
            sec_index=0,
            comp_x=0.5)
    else:
        somacenter_loc = ephys.locations.ArbLocsetLocation(
            name='somacenter',
            locset='(location 0 0.5)')
    locations['somacenter_loc'] = somacenter_loc

    pas_mech = ephys.mechanisms.NrnMODMechanism(
        name='pas',
        suffix='pas',
        locations=[somatic_loc])

    expsyn_mech = ephys.mechanisms.NrnMODPointProcessMechanism(
        name='expsyn',
        suffix='ExpSyn',
        locations=[somacenter_loc])

    expsyn_loc = ephys.locations.NrnPointProcessLocation(
        'expsyn_loc',
        pprocess_mech=expsyn_mech)
    locations['expsyn_loc'] = expsyn_loc

    expsyn_tau_param = ephys.parameters.NrnPointProcessParameter(
        name='expsyn_tau',
        param_name='tau',
        value=2,
        bounds=[0, 50],
        locations=[expsyn_loc])

    cm_param = ephys.parameters.NrnSectionParameter(
        name='cm',
        param_name='cm',
        value=1.0,
        locations=[somatic_loc],
        frozen=True)

    cell = ephys.models.CellModel(
        name='simple_cell',
        morph=morph,
        mechs=[pas_mech, expsyn_mech],
        params=[cm_param, expsyn_tau_param])

    if return_locations is True:
        return cell, locations
    else:
        return cell


def main(args):
    """Main"""
    if args.sim == 'nrn':
        sim = ephys.simulators.NrnSimulator()
    else:
        sim = ephys.simulators.ArbSimulator()

    cell, locations = create_model(sim=args.sim,
                                   do_replace_axon=False,
                                   return_locations=True)

    stim_start = 20
    number = 5
    interval = 5

    netstim = ephys.stimuli.NrnNetStimStimulus(
        total_duration=200,
        number=5,
        interval=5,
        start=stim_start,
        weight=5e-4,
        locations=[locations['expsyn_loc']])

    stim_end = stim_start + interval * number

    rec = ephys.recordings.CompRecording(
        name='soma.v',
        location=locations['somacenter_loc'],
        variable='v')

    if args.sim == 'nrn':
        protocol = ephys.protocols.SweepProtocol(
            'netstim_protocol',
            [netstim],
            [rec])
    else:
        protocol = ephys.protocols.ArbSweepProtocol(
            'netstim_protocol',
            [netstim],
            [rec])

    max_volt_feature = ephys.efeatures.eFELFeature(
        'maximum_voltage',
        efel_feature_name='maximum_voltage',
        recording_names={'': 'soma.v'},
        stim_start=stim_start,
        stim_end=stim_end,
        exp_mean=-50,
        exp_std=.1)
    max_volt_objective = ephys.objectives.SingletonObjective(
        max_volt_feature.name,
        max_volt_feature)

    score_calc = ephys.objectivescalculators.ObjectivesCalculator(
        [max_volt_objective])

    cell_evaluator = ephys.evaluators.CellEvaluator(
        cell_model=cell,
        param_names=['expsyn_tau'],
        fitness_protocols={protocol.name: protocol},
        fitness_calculator=score_calc,
        sim=sim)

    default_param_values = {'expsyn_tau': 10.0}

    print(cell_evaluator.evaluate_with_dicts(default_param_values))

    optimisation = bpopt.optimisations.DEAPOptimisation(
        evaluator=cell_evaluator,
        offspring_size=10)

    _, hall_of_fame, _, _ = optimisation.run(max_ngen=5)

    best_ind = hall_of_fame[0]

    print('Best individual: ', best_ind)
    print('Fitness values: ', best_ind.fitness.values)

    best_ind_dict = cell_evaluator.param_dict(best_ind)
    responses = protocol.run(
        cell_model=cell,
        param_values=best_ind_dict,
        sim=sim)

    time = responses['soma.v']['time']
    voltage = responses['soma.v']['voltage']

    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    plt.plot(time, voltage)
    plt.xlabel('Time (ms)')
    plt.ylabel('Voltage (ms)')

    if args.output is not None:
        if not os.path.exists(args.output):
            output_dir = os.path.dirname(args.output)
            if len(output_dir) > 0:
                os.makedirs(output_dir, exist_ok=True)
            plt.savefig(args.output)

    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='expsyn')
    parser.add_argument('--sim', default='nrn', choices=['nrn', 'arb'],
                        help='Simulator (choose either nrn or arb)')
    parser.add_argument('-o', '--output',
                        help='Path to store voltage trace plot to')
    args = parser.parse_args()

    if args.sim not in ['nrn', 'arb']:
        raise argparse.ArgumentError('Simulator must be either nrn or arb')

    main(args)
