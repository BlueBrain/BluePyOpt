"""Main Graupner-Brunel STDP example script"""

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


def analyse():
    """Generate plot"""

    cp = pickle.load(open(cp_filename, "r"))
    results = (
        cp['population'],
        cp['halloffame'],
        cp['history'],
        cp['logbook'])

    _, hof, _, log = results

    best_ind = hof[0]
    best_ind_dict = evaluator.get_param_dict(best_ind)

    print('Best Individual')
    for attribute, value in best_ind_dict.iteritems():
        print('\t{} : {}'.format(attribute, value))

    model_sg = evaluator.compute_synaptic_gain_with_lists(best_ind)

    # Load data
    protocols, sg, _, stderr = stdputil.load_neviansakmann()
    dt = np.array([float(p.prot_id[:3]) for p in protocols])

    # Plot result summary
    fig1, ax1 = plt.subplots()

    ax1.errorbar(dt, model_sg, marker='o', label='Model')
    ax1.errorbar(dt, sg, yerr=stderr, marker='o', label='In vitro')

    ax1.axhline(y=1, color='k', linestyle='--')
    ax1.axvline(color='k', linestyle='--')

    ax1.set_xlabel('$\Delta t$(ms)')
    ax1.set_ylabel('change in EPSP amplitude')
    ax1.legend()

    fig1.savefig('figures/gb_fit.eps')
    
    # Plot calcium transients for each protocol
    fig2, axarr2 = plt.subplots(len(protocols), 1, sharex=True)
    for i, protocol in enumerate(protocols):
        calcium = stdputil.CalciumTrace(protocol, best_ind_dict)
        time, ca = calcium.materializetrace()
        
        axarr2[i].plot(time, ca)
        axarr2[i].axhline(y=best_ind_dict['theta_d'], color='g', linestyle='--')
        axarr2[i].annotate(r'$\theta_d$', xy=(0.3, best_ind_dict['theta_d']-0.15))
        axarr2[i].axhline(y=best_ind_dict['theta_p'], color='r', linestyle='--')
        axarr2[i].annotate(r'$\theta_p$', xy=(0.3, best_ind_dict['theta_p']+0.05))
        axarr2[i].set_title(protocol.prot_id)
        axarr2[i].set_xlim(-0.1, 0.4)
        axarr2[i].set_ylabel('calcium')
    axarr2[i].set_xlabel('time (sec)')
    
    fig2.savefig('figures/calcium_traces.eps')
    
    # Plot dt scan
    dt_vec = np.linspace(-90e-3, 50e-3, 100)
    sg_vec = []
    for model_dt in dt_vec:
        protocol = stdputil.Protocol(['pre', 'post', 'post', 'post'], [model_dt, 20e-3, 20e-3], 0.1, 60.0, prot_id='%.2fms'%model_dt)
        model_sg = stdputil.protocol_outcome(protocol, best_ind_dict)
        sg_vec.append(model_sg)

    fig3, ax3 = plt.subplots()

    ax3.plot(dt_vec*1000.0, sg_vec, marker='o', label='Model')
    ax3.errorbar(dt, sg, yerr=stderr, marker='o', label='In vitro')

    ax3.axhline(y=1, color='k', linestyle='--')
    ax3.axvline(color='k', linestyle='--')

    ax3.set_xlabel('$\Delta t$(ms)')
    ax3.set_ylabel('change in EPSP amplitude')
    ax3.legend()

    fig3.savefig('figures/dt_scan.eps')
        
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
