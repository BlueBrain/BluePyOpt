"""StochKv cell example"""

# pylint: disable=R0914

import os

import bluepyopt.ephys as ephys

script_dir = os.path.dirname(__file__)
morph_dir = os.path.join(script_dir, 'morphology')


def stochkv_hoc_filename(deterministic=False):
    """Return stochkv hoc model filename"""
    return os.path.join(
        script_dir,
        'stochkvcell%s.hoc' %
        ('_det' if deterministic else ''))


def run_stochkv_model(deterministic=False):
    """Run stochkv model"""

    morph = ephys.morphologies.NrnFileMorphology(
        os.path.join(
            morph_dir,
            'simple.swc'))

    somatic_loc = ephys.locations.NrnSeclistLocation(
        'somatic',
        seclist_name='somatic')
    stochkv_mech = ephys.mechanisms.NrnMODMechanism(
        name='StochKv',
        suffix='StochKv',
        locations=[somatic_loc],
        deterministic=deterministic)
    pas_mech = ephys.mechanisms.NrnMODMechanism(
        name='pas',
        suffix='pas',
        locations=[somatic_loc])
    gkbar_param = ephys.parameters.NrnSectionParameter(
        name='gkbar_StochKv',
        param_name='gkbar_StochKv',
        locations=[somatic_loc],
        bounds=[0.0, 10.0],
        frozen=False)
    epas_param = ephys.parameters.NrnSectionParameter(
        name='e_pas',
        param_name='e_pas',
        locations=[somatic_loc],
        value=-90,
        frozen=True)
    celsius_param = ephys.parameters.NrnGlobalParameter(
        name='celsius',
        param_name='celsius',
        value=34.0,
        frozen=True)
    params = [epas_param, celsius_param, gkbar_param]
    stochkv_cell = ephys.models.CellModel(
        name='stochkv_cell',
        morph=morph,
        mechs=[pas_mech, stochkv_mech],
        params=params)

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)

    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.1,
        step_delay=50,
        step_duration=50,
        location=soma_loc,
        total_duration=150)
    hold_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=-0.025,
        step_delay=0,
        step_duration=10000,
        location=soma_loc,
        total_duration=150)
    rec = ephys.recordings.CompRecording(
        name='Step.soma.v',
        location=soma_loc,
        variable='v')

    protocol = ephys.protocols.SweepProtocol('Step', [stim, hold_stim], [rec])

    nrn = ephys.simulators.NrnSimulator(cvode_active=False)

    evaluator = ephys.evaluators.CellEvaluator(
        cell_model=stochkv_cell,
        param_names=[param.name for param in params],
        fitness_calculator=ephys.objectivescalculators.ObjectivesCalculator(),
        sim=nrn)

    best_param_values = {'gkbar_StochKv': 0.5}
    responses = evaluator.run_protocol(
        protocol,
        cell_model=stochkv_cell,
        param_values=best_param_values,
        sim=nrn)

    hoc_string = stochkv_cell.create_hoc(
        param_values=best_param_values,
        disable_banner=True)

    stochkv_hoc_cell = ephys.models.HocCellModel(
        'stochkv_hoc_cell',
        morphology_path=morph_dir,
        hoc_string=hoc_string)

    nrn.neuron.h.celsius = 34

    hoc_responses = protocol.run(stochkv_hoc_cell, best_param_values, sim=nrn)

    evaluator.use_params_for_seed = True
    different_seed_responses = evaluator.run_protocol(
        protocol,
        cell_model=stochkv_cell,
        param_values=best_param_values,
        sim=nrn)

    return responses, hoc_responses, different_seed_responses, hoc_string


def main():
    """Main"""
    import matplotlib.pyplot as plt

    for deterministic in [True, False]:
        stochkv_responses, stochkv_hoc_responses, different_seed_responses, \
            stochkv_hoc_string = \
            run_stochkv_model(deterministic=deterministic)

        with open(stochkv_hoc_filename(deterministic=deterministic), 'w') as \
                stochkv_hoc_file:
            stochkv_hoc_file.write(stochkv_hoc_string)

        time = stochkv_responses['Step.soma.v']['time']
        py_voltage = stochkv_responses['Step.soma.v']['voltage']
        hoc_voltage = stochkv_hoc_responses['Step.soma.v']['voltage']
        different_seed_voltage = \
            different_seed_responses['Step.soma.v']['voltage']

        plt.figure()
        plt.plot(time, py_voltage - hoc_voltage, label='py - hoc diff')
        plt.xlabel('time (ms)')
        plt.ylabel('voltage diff(mV)')
        plt.title('Deterministic' if deterministic else 'Stochastic')
        plt.legend()

        plt.figure()
        plt.plot(time, py_voltage, label='py')
        plt.plot(time, hoc_voltage, label='hoc')
        plt.xlabel('time (ms)')
        plt.ylabel('voltage (mV)')
        plt.title('Deterministic' if deterministic else 'Stochastic')
        plt.legend()

        plt.figure()
        plt.plot(time, py_voltage, label='py')
        plt.plot(time, different_seed_voltage, label='different seed')
        plt.xlabel('time (ms)')
        plt.ylabel('voltage (mV)')
        plt.title('Deterministic' if deterministic else 'Stochastic')
        plt.legend()

    plt.show()

if __name__ == '__main__':
    main()
