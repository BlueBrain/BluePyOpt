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

"""
This optimisation is based on L5PC optimisations developed by Etay Hay in the
context of the BlueBrain project
"""

# pylint: disable=R0914, W0403
import os

import argparse
# pylint: disable=R0914
import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

import bluepyopt

# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format


import l5pc_evaluator
evaluator = l5pc_evaluator.create()


def evaluate(parameter_array):
    """Global evaluate function"""

    return evaluator.evaluate(parameter_array)

opt = bluepyopt.optimisations.DEAPOptimisation(
    evaluator=evaluator,
    offspring_size=2,
    use_scoop=True)


def main():
    """Main"""

    parser = argparse.ArgumentParser(description='L5PC example')
    parser.add_argument('--start', action="store_true")
    parser.add_argument('--continue_cp', action="store_true")
    parser.add_argument('--analyse', action="store_true")
    parser.add_argument('--compile', action="store_true")
    parser.add_argument('--hocanalyse', action="store_true")

    args = parser.parse_args()

    if args.compile:
        import commands
        commands.getstatusoutput('cd mechanisms/; nrnivmodl; cd ..')

    # TODO store definition dicts in json
    # TODO rename 'score' into 'objective'
    # TODO add functionality to read settings of every object from config format

    if args.hocanalyse:
        try:
            import bglibpy  # NOQA
        except ImportError:
            raise ImportError(
                'bglibpy not installed, '
                '--hocanalyse for internal testing only!')
    else:
        mechfile = "./mechanisms/x86_64/.libs/libnrnmech.so"
        if os.path.isfile(mechfile):
            from bluepyopt.ephys import neuron
            neuron.h.nrn_load_dll(mechfile)

        else:
            raise ImportError('nrnmech not compiled, run --compile first!')

    # TODO read checkpoint filename from arguments
    cp_filename = 'checkpoints/checkpoint.pkl'

    if args.start or args.continue_cp:
        opt.run(
            max_ngen=200,
            continue_cp=args.continue_cp,
            cp_filename=cp_filename)

    if args.analyse:
        import l5pc_analysis

        # _, axes_obj = plt.subplots(n_of_rows, n_of_cols, facecolor='white')
        # axes = numpy.ravel(axes_obj)
        import matplotlib.pyplot as plt
        fig_release = plt.figure(figsize=(10, 10), facecolor='white')

        box = {
            'left': 0.0,
            'bottom': 0.0,
            'width': 1.0,
            'height': 1.0}

        l5pc_analysis.analyse_releasecircuit_model(
            opt=opt,
            fig=fig_release,
            box=box)

        fig_release.savefig('figures/release_l5pc.eps')

        if os.path.isfile(cp_filename):

            bpop_model_fig = plt.figure(figsize=(10, 10), facecolor='white')
            bpop_evol_fig = plt.figure(figsize=(10, 10), facecolor='white')

            l5pc_analysis.analyse_cp(
                opt=opt,
                cp_filename=cp_filename,
                figs=[bpop_model_fig, bpop_evol_fig],
                boxes=[box, box])

            bpop_model_fig.savefig('figures/bpop_l5pc_model.eps')
            bpop_evol_fig.savefig('figures/bpop_l5pc_evolution.eps')

        else:
            print('No checkpoint file available run optimization '
                  'first with --start')

        plt.show()

    elif args.hocanalyse:

        import l5pc_analysis

        # _, axes_obj = plt.subplots(n_of_rows, n_of_cols, facecolor='white')
        # axes = numpy.ravel(axes_obj)
        import matplotlib.pyplot as plt
        fig_release = plt.figure(figsize=(10, 10), facecolor='white')

        box = {
            'left': 0.0,
            'bottom': 0.0,
            'width': 1.0,
            'height': 1.0}

        l5pc_analysis.analyse_releasecircuit_hocmodel(
            opt=opt,
            fig=fig_release,
            box=box)

        fig_release.savefig('figures/release_l5pc_hoc.eps')

        plt.show()

if __name__ == '__main__':
    main()
