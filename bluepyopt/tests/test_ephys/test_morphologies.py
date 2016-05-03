"""ephys/morphologies.py unit tests"""

import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys


@attr('unit')
def test_morphology_init():
    """ephys.morphologies: testing Morphology constructor"""

    morph = ephys.morphologies.Morphology()
    nt.assert_is_instance(morph, ephys.morphologies.Morphology)
