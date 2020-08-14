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


# pylint: disable=R0914, W0633

import os
import pickle
import numpy as np
import bluepyopt.ephys as ephys

# Parameters in release circuit model
release_params = {
    'gNaTs2_tbar_NaTs2_t.apical': 0.026145,
    'gSKv3_1bar_SKv3_1.apical': 0.004226,
    'gImbar_Im.apical': 0.000143,
    'gNaTa_tbar_NaTa_t.axonal': 3.137968,
    'gK_Tstbar_K_Tst.axonal': 0.089259,
    'gamma_CaDynamics_E2.axonal': 0.002910,
    'gNap_Et2bar_Nap_Et2.axonal': 0.006827,
    'gSK_E2bar_SK_E2.axonal': 0.007104,
    'gCa_HVAbar_Ca_HVA.axonal': 0.000990,
    'gK_Pstbar_K_Pst.axonal': 0.973538,
    'gSKv3_1bar_SKv3_1.axonal': 1.021945,
    'decay_CaDynamics_E2.axonal': 287.198731,
    'gCa_LVAstbar_Ca_LVAst.axonal': 0.008752,
    'gamma_CaDynamics_E2.somatic': 0.000609,
    'gSKv3_1bar_SKv3_1.somatic': 0.303472,
    'gSK_E2bar_SK_E2.somatic': 0.008407,
    'gCa_HVAbar_Ca_HVA.somatic': 0.000994,
    'gNaTs2_tbar_NaTs2_t.somatic': 0.983955,
    'decay_CaDynamics_E2.somatic': 210.485284,
    'gCa_LVAstbar_Ca_LVAst.somatic': 0.000333
}


def set_rcoptions(func):
    '''decorator to apply custom matplotlib rc params to function,undo after'''
    import matplotlib

    def wrap(*args, **kwargs):
        """Wrap"""
        options = {'axes.linewidth': 2, }
        with matplotlib.rc_context(rc=options):
            func(*args, **kwargs)
    return wrap


def get_responses(cell_evaluator, individuals, filename):

    responses = []
    if filename and os.path.exists(filename):
        with open(filename) as fd:
            return pickle.load(fd)

    for individual in individuals:
        individual_dict = cell_evaluator.param_dict(individual)
        responses.append(
            cell_evaluator.run_protocols(
                cell_evaluator.fitness_protocols.values(),
                param_values=individual_dict))

    if filename:
        with open(filename, 'w') as fd:
            pickle.dump(responses, fd)

    return responses


@set_rcoptions
def analyse_cp(opt, cp_filename, responses_filename, figs):
    """Analyse optimisation results"""
    (model_fig, model_box), (objectives_fig, objectives_box), (
        evol_fig, evol_box) = figs

    cp = pickle.load(open(cp_filename, "r"))
    hof = cp['halloffame']

    responses = get_responses(opt.evaluator, hof, responses_filename)
    plot_multiple_responses(responses, fig=model_fig)

    # objectives
    parameter_values = opt.evaluator.param_dict(hof[0])
    fitness_protocols = opt.evaluator.fitness_protocols
    responses = {}

    nrn = ephys.simulators.NrnSimulator()

    for protocol in fitness_protocols.values():
        response = protocol.run(
            cell_model=opt.evaluator.cell_model,
            param_values=parameter_values,
            sim=nrn)
        responses.update(response)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(responses)
    plot_objectives(objectives, fig=objectives_fig, box=objectives_box)
    # objectives

    plot_log(cp['logbook'], fig=evol_fig, box=evol_box)


def plot_log(log, fig=None, box=None):
    """Plot logbook"""

    gen_numbers = log.select('gen')
    mean = np.array(log.select('avg'))
    std = np.array(log.select('std'))
    minimum = np.array(log.select('min'))

    left_margin = box['width'] * 0.1
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    stdminus = mean - std
    stdplus = mean + std
    axes.plot(
        gen_numbers,
        mean,
        color='black',
        linewidth=2,
        label='population average')

    axes.fill_between(
        gen_numbers,
        stdminus,
        stdplus,
        color='lightgray',
        linewidth=2,
        label=r'population standard deviation')

    axes.plot(
        gen_numbers,
        minimum,
        color='red',
        linewidth=2,
        label='population minimum')

    axes.set_xlim(min(gen_numbers) - 1, max(gen_numbers) + 1)
    axes.set_xlabel('Generation #')
    axes.set_ylabel('Sum of objectives')
    axes.set_ylim([0, max(stdplus)])
    axes.legend()


def plot_history(history):
    """Plot the history of the individuals"""

    import networkx

    import matplotlib.pyplot as plt
    plt.figure()

    graph = networkx.DiGraph(history.genealogy_tree)
    graph = graph.reverse()     # Make the grah top-down
    # colors = [\
    #        toolbox.evaluate(history.genealogy_history[i])[0] for i in graph]
    positions = networkx.graphviz_layout(graph, prog="dot")
    networkx.draw(graph, positions)


def plot_objectives(objectives, fig=None, box=None):
    """Plot objectives of the cell model"""

    import collections
    objectives = collections.OrderedDict(sorted(objectives.items()))
    left_margin = box['width'] * 0.4
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    ytick_pos = [x + 0.5 for x in range(len(objectives.keys()))]

    axes.barh(ytick_pos,
              objectives.values(),
              height=0.5,
              align='center',
              color='#779ECB')
    axes.set_yticks(ytick_pos)
    axes.set_yticklabels(objectives.keys(), size='x-small')
    axes.set_ylim(-0.5, len(objectives.values()) + 0.5)
    axes.set_xlabel('Objective value (# std)')
    axes.set_ylabel('Objectives')


def plot_responses(responses, fig=None, box=None):
    """Plot responses of the cell model"""
    rec_rect = {}
    rec_rect['left'] = box['left']
    rec_rect['width'] = box['width']
    rec_rect['height'] = float(box['height']) / len(responses)
    rec_rect['bottom'] = box['bottom'] + \
        box['height'] - rec_rect['height']
    last = len(responses) - 1
    for i, (_, recording) in enumerate(sorted(responses.items())):
        plot_recording(recording, fig=fig, box=rec_rect, xlabel=(last == i))
        rec_rect['bottom'] -= rec_rect['height']


def get_slice(start, end, data):
    return slice(np.searchsorted(data, start),
                 np.searchsorted(data, end))


def plot_multiple_responses(responses, fig):
    '''creates 6 subplots for step{1,2,3} / dAP traces, plots the responses'''
    traces = ('Step1.soma.v', 'Step2.soma.v', 'Step3.soma.v',
              'bAP.dend1.v', 'bAP.dend2.v', 'bAP.soma.v', )
    plot_count = len(traces)
    ax = [fig.add_subplot(plot_count, 1, i + 1) for i in range(plot_count)]

    overlay_count = len(responses)
    for i, response in enumerate(reversed(responses[:overlay_count])):
        color = 'lightblue'
        if i == overlay_count - 1:
            color = 'blue'

        for i, name in enumerate(traces):
            sl = get_slice(0, 3000, response[name]['time'])
            ax[i].plot(
                response[name]['time'][sl],
                response[name]['voltage'][sl],
                color=color,
                linewidth=1)
            ax[i].set_ylabel(name + '\nVoltage (mV)')
            ax[i].set_autoscaley_on(True)
            ax[i].set_autoscalex_on(True)
            ax[i].set_ylim((-85, 50))

        ax[-1].set_xlabel('Time (ms)')


def plot_recording(recording, fig=None, box=None, xlabel=False):
    """Plot responses of the cell model"""

    import matplotlib.pyplot as plt

    left_margin = box['width'] * 0.25
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.1
    bottom_margin = box['height'] * 0.25

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    recording.plot(axes)
    axes.set_ylim(-100, 40)
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.tick_params(
        axis='both',
        bottom='on',
        top='off',
        left='on',
        right='off')

    name = recording.name
    if name.endswith('.v'):
        name = name[:-2]

    axes.set_ylabel(name + '\n(mV)', labelpad=25)
    yloc = plt.MaxNLocator(2)
    axes.yaxis.set_major_locator(yloc)

    if xlabel:
        axes.set_xlabel('Time (ms)')


def plot_validation(opt, parameters):
    """Plot validation"""

    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name='soma',
        seclist_name='somatic',
        sec_index=0,
        comp_x=0.5)

    validation_recording = ephys.recordings.CompRecording(
        name='validation.soma.v',
        location=soma_loc,
        variable='v')

    validation_i_data = np.loadtxt('exp_data/noise_i.txt')
    # validation_v_data = np.loadtxt('exp_data/noise_v.txt')
    validation_time = validation_i_data[:, 0] + 200.0
    validation_current = validation_i_data[:, 1]
    # validation_voltage = validation_v_data[:, 1]
    validation_stimulus = ephys.stimuli.NrnCurrentPlayStimulus(
        current_points=validation_current,
        time_points=validation_time,
        location=soma_loc)
    hypamp_stimulus = ephys.stimuli.NrnSquarePulse(
        step_amplitude=-0.126,
        step_delay=0,
        step_duration=max(validation_time),
        location=soma_loc,
        total_duration=max(validation_time))

    validation_protocol = ephys.protocols.SweepProtocol(
        'validation',
        [validation_stimulus, hypamp_stimulus],
        [validation_recording])

    validation_responses = {}
    write_pickle = False

    paramsets = {}
    paramsets['release'] = release_params
    for index, param_values in enumerate(parameters):
        paramsets['model%d' % index] = param_values

    if write_pickle:
        for paramset_name, paramset in paramsets.items():
            validation_responses[paramset_name] = opt.evaluator.run_protocols(
                [validation_protocol],
                param_values=paramset)

        pickle.dump(validation_responses, open('validation_response.pkl', 'w'))
    else:
        validation_responses = pickle.load(open('validation_response.pkl'))
    # print validation_responses['validation.soma.v']['time']

    peaktimes = {}
    import efel
    for index, model_name in enumerate(validation_responses.keys()):
        trace = {}
        trace['T'] = validation_responses[
            model_name]['validation.soma.v']['time']
        trace['V'] = validation_responses[model_name][
            'validation.soma.v']['voltage']
        trace['stim_start'] = [500]
        trace['stim_end'] = [max(validation_time)]
        peaktimes[model_name] = efel.getFeatureValues(
            [trace],
            ['peak_time'])[0]['peak_time']

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, figsize=(10, 7), facecolor='white', sharex=True)

    ax[0].plot(validation_time, validation_current, 'k')
    ax[0].spines['top'].set_visible(False)
    ax[0].spines['right'].set_visible(False)
    ax[0].spines['bottom'].set_visible(False)
    ax[0].tick_params(
        axis='both',
        bottom='off',
        top='off',
        left='on',
        right='off')
    ax[0].set_ylabel('Current\n (nA)', rotation=0, labelpad=25)

    for index, (model_name, peak_time) in enumerate(sorted(peaktimes.items())):
        print(model_name)
        if model_name == 'release':
            color = 'red'
            print(color, peak_time)
        elif model_name == 'model0':
            color = 'darkblue'
        else:
            color = 'lightblue'
        ax[1].scatter(
            peak_time,
            np.array(
                [100] *
                len(peak_time)) +
            10 *
            index,
            color=color,
            s=10)
    ax[1].spines['top'].set_visible(False)
    ax[1].spines['right'].set_visible(False)
    ax[1].spines['bottom'].set_visible(False)
    ax[1].spines['left'].set_visible(False)
    ax[1].tick_params(
        bottom='off',
        top='off',
        left='off',
        right='off')
    ax[1].set_yticks([])

    ax[2].plot(
        validation_responses['release']['validation.soma.v']['time'],
        validation_responses['release']['validation.soma.v']['voltage'], 'r',
        linewidth=1)

    ax[2].plot(
        validation_responses[
            'model0']['validation.soma.v']['time'],
        validation_responses[
            'model0']['validation.soma.v']['voltage'],
        color='darkblue',
        linewidth=1)

    ax[2].spines['top'].set_visible(False)
    ax[2].spines['right'].set_visible(False)
    ax[2].tick_params(
        axis='both',
        bottom='on',
        top='off',
        left='on',
        right='off')

    ax[2].set_yticks([-100, 0.0])
    ax[2].set_ylabel('Voltage\n (mV)', rotation=0, labelpad=25)
    ax[2].set_xlabel('Time (ms)')
    ax[2].set_xlim(min(validation_time), max(validation_time))

    fig.tight_layout()

    fig.savefig('figures/l5pc_valid.eps')


@set_rcoptions
def analyse_releasecircuit_model(opt, figs, box=None):
    """Analyse L5PC model from release circuit"""
    (release_responses_fig, response_box), (
        release_objectives_fig, objectives_box) = figs

    fitness_protocols = opt.evaluator.fitness_protocols

    nrn = ephys.simulators.NrnSimulator()

    responses = {}
    for protocol in fitness_protocols.values():
        response = protocol.run(
            cell_model=opt.evaluator.cell_model,
            param_values=release_params,
            sim=nrn)
        responses.update(response)

    plot_multiple_responses([responses], fig=release_responses_fig)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(responses)
    plot_objectives(objectives, fig=release_objectives_fig, box=objectives_box)


def analyse_releasecircuit_hocmodel(opt, fig=None, box=None):
    """Analyse L5PC model from release circuit from .hoc template"""

    fitness_protocols = opt.evaluator.fitness_protocols

    from hocmodel import HocModel  # NOQA

    template_model = HocModel(morphname="./morphology/C060114A7.asc",
                              template="./cADpyr_76.hoc")

    responses = template_model.run_protocols(
        fitness_protocols)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(
        responses)

    # template_model.instantiate()
    # for section in template_model.icell.axonal:
    #    print section.L, section.diam, section.nseg

    plot_responses(responses, fig=fig,
                   box={
                       'left': box['left'],
                       'bottom': box['bottom'] + float(box['height']) / 2.0,
                       'width': box['width'],
                       'height': float(box['height']) / 2.0})

    plot_objectives(objectives, fig=fig,
                    box={
                        'left': box['left'],
                        'bottom': box['bottom'],
                        'width': box['width'],
                        'height': float(box['height']) / 2.0})


FITNESS_CUT_OFF = 5


def plot_individual_params(
        opt,
        ax,
        params,
        marker,
        color,
        markersize=40,
        plot_bounds=False,
        fitness_cut_off=FITNESS_CUT_OFF):
    '''plot the individual parameter values'''
    observations_count = len(params)
    param_count = len(params[0])

    results = np.zeros((observations_count, param_count))
    good_fitness = 0
    for i, param in enumerate(params):
        if fitness_cut_off < max(param.fitness.values):
            continue
        results[good_fitness] = param
        good_fitness += 1

    results = results

    for c in range(good_fitness):
        x = np.arange(param_count)
        y = results[c, :]
        ax.scatter(x=x, y=y, s=float(markersize), marker=marker, color=color)

    if plot_bounds:
        def plot_tick(column, y):
            col_width = 0.25
            x = [column - col_width,
                 column + col_width]
            y = [y, y]
            ax.plot(x, y, color='black')

        # plot min and max
        for i, parameter in enumerate(opt.evaluator.params):
            min_value = parameter.lower_bound
            max_value = parameter.upper_bound
            plot_tick(i, min_value)
            plot_tick(i, max_value)


def plot_diversity(opt, checkpoint_file, fig, param_names):
    '''plot the whole history, the hall of fame, and the best individual
    from a unpickled checkpoint
    '''
    import matplotlib.pyplot as plt
    checkpoint = pickle.load(open(checkpoint_file, "r"))

    ax = fig.add_subplot(1, 1, 1)

    import copy
    release_individual = copy.deepcopy(checkpoint['halloffame'][0])
    for index, param_name in enumerate(opt.evaluator.param_names):
        release_individual[index] = release_params[param_name]
    plot_individual_params(
        opt,
        ax,
        checkpoint['history'].genealogy_history.values(),
        marker='.',
        color='grey',
        plot_bounds=True)
    plot_individual_params(opt, ax, checkpoint['halloffame'],
                           marker='o', color='black')
    plot_individual_params(opt,
                           ax,
                           [checkpoint['halloffame'][0]],
                           markersize=150,
                           marker='x',
                           color='blue')
    plot_individual_params(opt, ax, [release_individual], markersize=150,
                           marker='x', color='red')

    labels = [name.replace('.', '\n') for name in param_names]

    param_count = len(checkpoint['halloffame'][0])
    x = range(param_count)
    for xline in x:
        ax.axvline(xline, linewidth=1, color='grey', linestyle=':')

    plt.xticks(x, labels, rotation=80, ha='center', size='small')
    ax.set_xlabel('Parameter names')
    ax.set_ylabel('Parameter values')
    ax.set_yscale('log')
    ax.set_ylim(bottom=1e-7)

    plt.tight_layout()
    plt.plot()
    ax.set_autoscalex_on(True)
