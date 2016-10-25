"""Main Graupner-Brunel STDP example script"""

# pylint: disable=R0914

from __future__ import print_function

import pickle
import bluepyopt as bpop
import matplotlib.pyplot as plt
import numpy as np
import gbevaluator
import stdputil

cp_filename = 'checkpoints/checkpoint.pkl'

evaluator = gbevaluator.GraupnerBrunelEvaluator()

opt = bpop.optimisations.DEAPOptimisation(evaluator, offspring_size=100,
                                          eta=20, mutpb=0.3, cxpb=0.7)


def run_model():
    """Run model"""

    _, _, _, _ = opt.run(
        max_ngen=200, cp_filename=cp_filename, cp_frequency=100)


def plot_log(log):
    """Plot logbook"""

    fig, axes = plt.subplots(figsize=(10, 10), facecolor='white')

    gen_numbers = log.select('gen')
    mean = np.array(log.select('avg'))
    std = np.array(log.select('std'))
    minimum = log.select('min')
    # maximum = log.select('max')

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

    fig.tight_layout()
    fig.savefig('figures/graupner_evolution.eps')


def plot_epspamp_discrete(dt, model_sg, sg, stderr):
    """Plot EPSP amplitude change for discrete points"""
    # Plot result summary
    fig1, ax1 = plt.subplots(figsize=(10, 10), facecolor='white')

    ax1.errorbar(dt, model_sg, marker='o', label='Model')
    ax1.errorbar(dt, sg, yerr=stderr, marker='o', label='In vitro')

    ax1.axhline(y=1, color='k', linestyle='--')
    ax1.axvline(color='k', linestyle='--')

    ax1.set_xlabel(r'$\Delta t$ (ms)')
    ax1.set_ylabel('change in EPSP amplitude')
    ax1.legend()

    fig1.savefig('figures/graupner_fit.eps')


def plot_calcium_transients(protocols, best_ind_dict):
    """Plot calcium transients"""

    # Plot calcium transients for each protocol
    fig2, axarr2 = plt.subplots(
        len(protocols), 1, sharex=True, figsize=(
            10, 10), facecolor='white')
    for i, protocol in enumerate(protocols):
        calcium = stdputil.CalciumTrace(protocol, best_ind_dict)
        time, ca = calcium.materializetrace()

        axarr2[i].plot(time, ca)
        axarr2[i].axhline(y=best_ind_dict['theta_d'], color='g', linestyle='--')
        axarr2[i].annotate(
            r'$\theta_d$', xy=(
                0.3, best_ind_dict['theta_d'] - 0.15))
        axarr2[i].axhline(y=best_ind_dict['theta_p'], color='r', linestyle='--')
        axarr2[i].annotate(
            r'$\theta_p$', xy=(
                0.3, best_ind_dict['theta_p'] + 0.05))
        axarr2[i].set_title(protocol.prot_id)
        axarr2[i].set_xlim(-0.012, 0.6)
        axarr2[i].set_ylim(-0.1, 2.2)
        axarr2[i].set_ylabel('calcium')

        yloc = plt.MaxNLocator(3)
        axarr2[i].yaxis.set_major_locator(yloc)

    axarr2[i].set_xlabel('Time (s)')

    fig2.tight_layout()

    fig2.savefig('figures/graupner_ca_traces.eps')


def plot_dt_scan(best_ind_dict, good_solutions, dt, sg, stderr):
    """Plot dt scan"""
    dt_vec = np.linspace(-90e-3, 50e-3, 100)
    sg_vec = []
    for model_dt in dt_vec:
        protocol = stdputil.Protocol(
            ['pre', 'post', 'post', 'post'], [model_dt, 20e-3, 20e-3], 0.1,
            60.0, prot_id='%.2fms' % model_dt)
        model_sg = stdputil.protocol_outcome(protocol, best_ind_dict)
        sg_vec.append(model_sg)

    try:
        sg_good_sol_vec = pickle.load(open("sg_good_sol_vec.pkl", "rb"))
    except IOError:
        sg_good_sol_vec = []
        for _, good_sol in enumerate(good_solutions):
            sg_ind = []
            for model_dt in dt_vec:
                protocol = stdputil.Protocol(
                    ['pre', 'post', 'post', 'post'], [model_dt, 20e-3, 20e-3],
                    0.1, 60.0, prot_id='%.2fms' % model_dt)
                model_sg = stdputil.protocol_outcome(protocol, good_sol)
                sg_ind.append(model_sg)
            sg_good_sol_vec.append(sg_ind)
        pickle.dump(sg_good_sol_vec, open("sg_good_sol_vec.pkl", "wb"))

    fig3, ax3 = plt.subplots(figsize=(10, 10), facecolor='white')
    ax3.set_rasterization_zorder(1)

    for sg_ind in sg_good_sol_vec:
        ax3.plot(dt_vec * 1000.0, sg_ind, lw=1, color='lightblue', zorder=0)
    ax3.plot(dt_vec * 1000.0, sg_vec, marker='o', lw=1, color='darkblue',
             label='Best model')
    ax3.errorbar(dt, sg, yerr=stderr, fmt='o', color='red', ms=10,
                 ecolor='red', elinewidth=3, capsize=5, capthick=3,
                 zorder=10000, label='In vitro')

    ax3.axhline(y=1, color='k', linestyle='--')
    ax3.axvline(color='k', linestyle='--')

    ax3.set_xlabel(r'$\Delta t$ (ms)')
    ax3.set_ylabel('EPSP amplitude change')
    ax3.legend()

    fig3.tight_layout()

    fig3.savefig('figures/graupner_dtscan.eps', rasterized=True, dpi=72)


def analyse():
    """Generate plot"""

    cp = pickle.load(open(cp_filename, "r"))
    results = (
        cp['population'],
        cp['halloffame'],
        cp['history'],
        cp['logbook'])

    _, hof, hst, log = results

    best_ind = hof[0]
    best_ind_dict = evaluator.get_param_dict(best_ind)

    print('Best Individual')
    for attribute, value in best_ind_dict.iteritems():
        print('\t{} : {}'.format(attribute, value))

    good_solutions = [
        evaluator.get_param_dict
        (ind)
        for ind in hst.genealogy_history.itervalues
        () if np.all(np.array(ind.fitness.values) < 1)]

    # model_sg = evaluator.compute_synaptic_gain_with_lists(best_ind)

    # Load data
    protocols, sg, _, stderr = stdputil.load_neviansakmann()
    dt = np.array([float(p.prot_id[:3]) for p in protocols])

    plt.rcParams['lines.linewidth'] = 2
    # plot_epspamp_discrete(dt, model_sg, sg, stderr)
    plot_dt_scan(best_ind_dict, good_solutions, dt, sg, stderr)
    plot_calcium_transients(protocols, best_ind_dict)

    plot_log(log)

    plt.show()


def main():
    """Main"""
    import argparse
    parser = argparse.ArgumentParser(description='Graupner-Brunel STDP')
    parser.add_argument('--start', action="store_true")
    parser.add_argument('--continue_cp', action="store_true")
    parser.add_argument('--analyse', action="store_true")

    args = parser.parse_args()
    if args.analyse:
        analyse()
    elif args.start:
        run_model()

if __name__ == '__main__':
    main()
