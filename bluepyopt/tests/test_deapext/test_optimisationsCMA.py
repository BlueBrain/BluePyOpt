"""bluepyopt.optimisationsCMA tests"""

import pytest
import bluepyopt
import bluepyopt.ephys.examples.simplecell


@pytest.mark.unit
def test_optimisationsCMA_normspace():
    "deapext.optimisationsCMA: Testing optimisationsCMA normspace"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator
    optimisation = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA(
        evaluator=evaluator)

    x = [n * 0.1 for n in range(len(evaluator.params))]
    y = [f2(f1(_)) for _, f1, f2 in zip(x, optimisation.to_norm,
                                        optimisation.to_space)]

    for a, b in zip(x, y):
        assert abs(a - b) < 1e-5


@pytest.mark.unit
def test_optimisationsCMA_run():
    "deapext.optimisationsCMA: Testing optimisationsCMA run from centroid"

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator
    x = [n * 0.1 for n in range(len(evaluator.params))]

    optimiser = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA
    optimisation = optimiser(evaluator=evaluator, centroids=[x])
    pop, hof, log, hist = optimisation.run(max_ngen=2)
