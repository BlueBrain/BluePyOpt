"""Test bluepyopt.tools"""

from nose.plugins.attrib import attr
import nose.tools as nt


@attr('unit')
def test_load():
    """bluepyopt.tools: test import"""

    import bluepyopt.tools  # NOQA


@attr('unit')
def test_uint32_seed():
    """bluepyopt.tools: test uint32_seed"""

    import bluepyopt.tools as bpoptools

    nt.assert_equal(bpoptools.uint32_seed("test"), 640136438)

    import random
    random.seed(1)

    hashes = []
    strings = []
    for _ in range(1000):
        string = ''.join(
            (chr(random.randint(0, 127)) for x in
             range(random.randint(10, 255))))
        strings.append(string)
        hashes.append(bpoptools.uint32_seed(string))

    nt.assert_equal(len(strings), len(set(strings)))
    nt.assert_equal(len(hashes), len(set(hashes)))

    import numpy
    for hash_value in hashes:
        nt.assert_equal(hash_value, numpy.uint32(hash_value))
