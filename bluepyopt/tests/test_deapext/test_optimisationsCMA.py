"""bluepyopt.optimisationsCMA tests"""

import pytest
import bluepyopt
import bluepyopt.ephys.examples.simplecell


@pytest.mark.unit
def test_optimisationsCMA_normspace():
    """deapext.optimisationsCMA: Testing optimisationsCMA normspace"""

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator
    optimisation = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA(
        evaluator=evaluator)

    x = [n * 0.1 for n in range(len(evaluator.params))]
    y = [f2(f1(p)) for p, f1, f2 in zip(x, optimisation.to_norm,
                                        optimisation.to_space)]

    for a, b in zip(x, y):
        assert abs(a - b) < 1e-5


@pytest.mark.unit
def test_optimisationsCMA_SO_run():
    """deapext.optimisationsCMA: Testing optimisationsCMA run from centroid"""

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator
    x = [n * 0.1 for n in range(len(evaluator.params))]

    optimiser = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA
    optimisation = optimiser(evaluator=evaluator, centroids=[x])
    pop, hof, log, hist = optimisation.run(max_ngen=2)

    assert abs(log.select("avg")[-1] - 53.3333) < 1e-4
    assert abs(log.select("std")[-1] - 83.7987) < 1e-4
    assert pop[0] == [0.10525059698894745, 0.01000000003249999]


@pytest.mark.unit
def test_optimisationsCMA_MO_run():
    """deapext.optimisationsCMA: Testing optimisationsCMA run from centroid"""

    simplecell = bluepyopt.ephys.examples.simplecell.SimpleCell()
    evaluator = simplecell.cell_evaluator

    optimiser = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA
    optimisation = optimiser(
        selector_name="multi_objective",
        offspring_size=3,
        evaluator=evaluator,
        seed=42
    )
    pop, hof, log, hist = optimisation.run(max_ngen=2)

    assert abs(log.select("avg")[-1] - 40.) < 1e-4
    assert abs(log.select("std")[-1] - 16.32993) < 1e-4
    assert pop[0] == [0.09601241274168831, 0.024646650865379722]
