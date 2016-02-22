"""Main Graupner STDP example script"""

import bluepyopt as bpop
import graupnerevaluator


def main():
    """Main"""

    evaluator = graupnerevaluator.GraupnerEvaluator()

    opt = bpop.optimisations.DEAPOptimisation(evaluator)
    opt.run(max_ngen=10000)


if __name__ == '__main__':
    main()
