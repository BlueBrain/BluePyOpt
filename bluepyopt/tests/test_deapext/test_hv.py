"""bluepyopt.deapext.hype tests"""

import numpy

import nose.tools as nt
from nose.plugins.attrib import attr

from bluepyopt.deapext.hype import hypeIndicatorSampled, hypeIndicatorExact


@attr("unit")
def test_hypeIndicator():
    "bluepyopt.deapext.hype"

    points = numpy.asarray([[1.0, 1.0], [2.0, 2.0], [1.7, 1.0], [1.0, 1.5]])
    bounds = numpy.max(points, axis=0)

    hv_sampled = hypeIndicatorSampled(
        points=points, bounds=bounds, k=5, nrOfSamples=200000
    )

    hv_exact = hypeIndicatorExact(points=points, bounds=bounds, k=5)

    idx_sampled = sorted(range(len(hv_sampled)), key=lambda k: hv_sampled[k])
    idx_exact = sorted(range(len(hv_exact)), key=lambda k: hv_exact[k])
    for samp, ex in zip(idx_sampled, idx_exact):
        nt.assert_equal(samp, ex)
