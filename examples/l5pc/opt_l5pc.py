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


# pylint: disable=R0914

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

    import argparse
    parser = argparse.ArgumentParser(description='L5PC example')
    parser.add_argument('--start', action="store_true")
    parser.add_argument('--continue_cp', action="store_true")
    parser.add_argument('--analyse', action="store_true")

    # TODO read checkpoint filename from arguments
    cp_filename = 'checkpoints/checkpoint.pkl'

    args = parser.parse_args()

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

        bpop_model_fig = plt.figure(figsize=(10, 10), facecolor='white')
        bpop_evol_fig = plt.figure(figsize=(10, 10), facecolor='white')

        l5pc_analysis.analyse_cp(
            opt=opt,
            cp_filename=cp_filename,
            figs=[bpop_model_fig, bpop_evol_fig],
            boxes=[box, box])

        bpop_model_fig.savefig('figures/bpop_l5pc_model.eps')
        bpop_evol_fig.savefig('figures/bpop_l5pc_evolution.eps')

        plt.show()

if __name__ == '__main__':
    main()
