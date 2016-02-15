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

import pickle


def analyse_cp(opt=None, cp_filename=None):
    """Analyse optimisation results"""

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
            cell_template.run_protocols(fitness_protocols,
                                        parameter_values=parameter_values)

        plot_responses(responses)
        plot_objectives(objectives)

    plot_log(log)

    # plot_history(history)


def plot_log(log):
    """Plot logbook"""

    import matplotlib.pyplot as plt
    import numpy

    gen_numbers = log.select('gen')
    mean = log.select('avg')
    std = log.select('std')
    minimum = log.select('min')
    maximum = log.select('max')

    _, ax = plt.subplots(facecolor='white')

    ax.errorbar(
        gen_numbers,
        numpy.negative(mean),
        std,
        color='black',
        linewidth=2,
        label='mean/std')
    ax.plot(
        gen_numbers,
        numpy.negative(minimum),
        color='blue',
        linewidth=1,
        label='max')
    ax.plot(
        gen_numbers,
        numpy.negative(maximum),
        color='red',
        linewidth=1,
        label='min')
    ax.set_xlim(min(gen_numbers) - 1, max(gen_numbers) + 1)
    ax.set_xlabel('Gen #')
    ax.set_ylabel('Fitness')
    ax.legend()


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


def plot_objectives(objectives):
    """Plot responses of the cell template"""

    import matplotlib.pyplot as plt

    _, ax = plt.subplots(facecolor='white')

    ax.barh(range(len(objectives.values())), objectives.values(), color='b')
    ax.set_yticks(
        [x + 0.5 for x in range(len(objectives.keys()))])
    ax.set_yticklabels(objectives.keys(), size='small')
    ax.set_ylim(0, len(objectives.values()))
    ax.set_xlabel('Objective value (# std)')
    ax.set_ylabel('Objectives')

    plt.tight_layout()
    plt.subplots_adjust(top=0.95)


def plot_responses(responses):
    """Plot responses of the cell template"""

    import matplotlib.pyplot as plt
    import numpy

    n_of_cols = 1
    n_of_rows = len(responses)
    _, axes_obj = plt.subplots(n_of_rows, n_of_cols, facecolor='white')
    axes = numpy.ravel(axes_obj)

    for rec_number, (_, recording) in \
            enumerate(responses.items()):
        # axes[rec_number].set_title(recording_name)
        recording.plot(axes[rec_number])
        axes[rec_number].legend()

        axes[rec_number].set_xlabel('Time (ms)')
        axes[rec_number].set_ylabel('Vm (mV)')

    plt.tight_layout()
    plt.subplots_adjust(top=0.95)


def analyse_releasecircuit_model(opt):
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

    responses = opt.evaluator.cell_template.run_protocols(
        fitness_protocols,
        parameter_values=parameters)

    objectives = opt.evaluator.objective_dict(
        opt.
        evaluator.
        fitness_calculator.calculate_scores(
            responses))

    plot_responses(responses)
    plot_objectives(objectives)
