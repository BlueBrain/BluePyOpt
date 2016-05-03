"""ephys/morphologies.py unit tests"""

import nose.tools as nt

import bluepyopt.ephys as ephys


def test_morphology_init():
    """ephys.morphologies: testing Morphology constructor"""

    morph = ephys.morphologies.Morphology()
    nt.assert_is_instance(morph, ephys.morphology.Morphology)
