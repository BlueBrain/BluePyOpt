"""bluepyopt.deapext.hype tests"""

import numpy

import bluepyopt.deapext.hype

import pytest


@pytest.mark.unit
def test_hypeIndicatorExact():
    """deapext.hype: Testing hypeIndicatorExact"""

    points = numpy.asarray([[250., 250.], [0., 0.], [240., 240.]])
    bounds = numpy.asarray([250., 250.])

    hv = bluepyopt.deapext.hype.hypeIndicatorExact(points, bounds, k=5)

    assert hv[0] == 0
    assert hv[1] == 62500
    assert hv[2] == 100


@pytest.mark.unit
def test_hypeIndicatorSampled():
    """deapext.hype: Testing hypeIndicatorSampled"""

    points = numpy.asarray([[250., 250.], [0., 0.], [240., 240.]])
    bounds = numpy.asarray([250., 250.])

    numpy.random.seed(42)
    hv = bluepyopt.deapext.hype.hypeIndicatorSampled(
        points, bounds, nrOfSamples=1000000, k=5
    )

    assert hv[0] == 0
    assert hv[1] == 62500
    assert numpy.abs((hv[2] / 100) - 1) < 0.05
