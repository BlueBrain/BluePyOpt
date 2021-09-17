"""Test bluepyopt.tools"""

import pytest


@pytest.mark.unit
def test_load():
    """bluepyopt.tools: test import"""

    import bluepyopt.tools  # NOQA


@pytest.mark.unit
def test_uint32_seed():
    """bluepyopt.tools: test uint32_seed"""

    import bluepyopt.tools as bpoptools

    assert bpoptools.uint32_seed("test") == 640136438

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

    assert len(strings) == len(set(strings))
    assert len(hashes) == len(set(hashes))

    import numpy
    for hash_value in hashes:
        assert hash_value == numpy.uint32(hash_value)
