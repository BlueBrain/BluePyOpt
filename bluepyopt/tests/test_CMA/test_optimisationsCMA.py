"""bluepyopt.optimisationsCMA tests"""

import nose.tools as nt

import bluepyopt
import bluepyopt.ephys.examples as examples

from nose.plugins.attrib import attr


@attr('unit')
def test_optimisationsCMA_normspace():
    "deapext.optimisationsCMA: Testing optimisationsCMA normspace"

    evaluator = examples.simplecell.cell_evaluator
    optimisation = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA(
        evaluator=evaluator)

    x = [n*0.1 for n in range(len(evaluator.params))]
    y = [f2(f1(_)) for _,f1,f2 in zip(x, optimisation.to_norm,
                                      optimisation.to_space)]
    for a, b in zip(x, y):
        nt.assert_almost_equal(a, b)

@attr('unit')
def test_optimisationsCMA_run():
    "deapext.optimisationsCMA: Testing optimisationsCMA run from centroid"

    evaluator = examples.simplecell.cell_evaluator
    x = [n * 0.1 for n in range(len(evaluator.params))]

    try:
        optimisation = bluepyopt.deapext.optimisationsCMA.DEAPOptimisationCMA(
                                                            evaluator=evaluator,
                                                            centroids=[x])
        pop, hof, log, hist = optimisation.run(max_ngen=2)
        raised = False
    except:
        raised = True

    nt.assert_equal(raised, False)
