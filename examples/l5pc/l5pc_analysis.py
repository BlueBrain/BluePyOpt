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


# pylint: disable=R0914, W0633

import pickle


def analyse_cp(opt=None, cp_filename=None, figs=None, boxes=None):
    """Analyse optimisation results"""

    bpop_model_fig, bpop_evol_fig = figs
    bpop_model_box, bpop_evol_box = boxes

    cp = pickle.load(open(cp_filename, "r"))
    results = (
        cp['population'],
        cp['halloffame'],
        cp['history'],
        cp['logbook'])

    _, hof, _, log = results

    print '\nHall of fame'
    print '################'
    for ind_number, individual in enumerate(hof[:1], 1):
        objectives = opt.evaluator.objective_dict(
            individual.fitness.values)
        parameter_values = opt.evaluator.param_dict(individual)

        print '\nIndividual %d' % ind_number
        print '#############'
        print 'Parameters: %s' % parameter_values
        print '\nObjective values: %s' % objectives

        fitness_protocols = opt.evaluator.fitness_protocols
        responses = opt.evaluator.\
            cell_model.run_protocols(fitness_protocols,
                                     param_values=parameter_values)

        box = bpop_model_box
        plot_responses(
            responses,
            fig=bpop_model_fig,
            box={
                'left': box['left'],
                'bottom': box['bottom'] + float(box['height']) / 2.0,
                'width': box['width'],
                'height': float(box['height']) / 2.0})
        plot_objectives(
            objectives,
            fig=bpop_model_fig,
            box={
                'left': box['left'],
                'bottom': box['bottom'],
                'width': box['width'],
                'height': float(box['height']) / 2.0})

    plot_log(log, fig=bpop_evol_fig,
             box=bpop_evol_box)


def plot_log(log, fig=None, box=None):
    """Plot logbook"""

    gen_numbers = log.select('gen')
    mean = log.select('avg')
    std = log.select('std')
    minimum = log.select('min')
    maximum = log.select('max')

    left_margin = box['width'] * 0.2
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    axes.errorbar(
        gen_numbers,
        mean,
        std,
        color='black',
        linewidth=2,
        label='mean/std')
    axes.plot(
        gen_numbers,
        minimum,
        color='blue',
        linewidth=1,
        label='min')
    axes.plot(
        gen_numbers,
        maximum,
        color='red',
        linewidth=1,
        label='max')
    axes.set_xlim(min(gen_numbers) - 1, max(gen_numbers) + 1)
    axes.set_xlabel('Gen #')
    axes.set_ylabel('Fitness')
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
    objectives = collections.OrderedDict(sorted(objectives.iteritems()))
    left_margin = box['width'] * 0.5
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    axes.barh(range(len(objectives.values())), objectives.values(), color='b')
    axes.set_yticks(
        [x + 0.5 for x in range(len(objectives.keys()))])
    axes.set_yticklabels(objectives.keys(), size='x-small')
    axes.set_ylim(0, len(objectives.values()))
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

    for _, recording in sorted(responses.items()):
        plot_recording(recording, fig=fig, box=rec_rect)
        rec_rect['bottom'] -= rec_rect['height']


def plot_recording(recording, fig=None, box=None):
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

    axes.set_ylabel(recording.name, rotation=0, labelpad=25)
    yloc = plt.MaxNLocator(2)
    axes.yaxis.set_major_locator(yloc)


def analyse_releasecircuit_model(opt, fig=None, box=None):
    """Analyse L5PC model from release circuit"""

    # Parameters in release circuit model
    parameters = {
        'gIhbar_Ih.basal': 0.000080,
        'gNaTs2_tbar_NaTs2_t.apical': 0.026145,
        'gSKv3_1bar_SKv3_1.apical': 0.004226,
        'gIhbar_Ih.apical': 0.000080,
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
        'gIhbar_Ih.somatic': 0.000080,
        'decay_CaDynamics_E2.somatic': 210.485284,
        'gCa_LVAstbar_Ca_LVAst.somatic': 0.000333
    }
    fitness_protocols = opt.evaluator.fitness_protocols

    responses = opt.evaluator.cell_model.run_protocols(
        fitness_protocols,
        param_values=parameters)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(
        responses)

    #opt.evaluator.cell_model.freeze(param_values=parameters)
    #opt.evaluator.cell_model.instantiate()
    #for section in opt.evaluator.cell_model.icell.axonal:
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


def analyse_releasecircuit_hocmodel(opt, fig=None, box=None):
    """Analyse L5PC model from release circuit from .hoc template"""

    fitness_protocols = opt.evaluator.fitness_protocols

    from hocmodel import HocModel

    template_model = HocModel(morphname="./morphology/C060114A7.asc",
                                    template="./cADpyr_76.hoc")

    responses = template_model.run_protocols(
        fitness_protocols)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(
        responses)

    #template_model.instantiate()
    #for section in template_model.icell.axonal:
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
