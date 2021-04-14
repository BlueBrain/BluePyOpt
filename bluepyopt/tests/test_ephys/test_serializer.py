"""Test for ephys.serializer"""

import json

import pytest
import numpy

import bluepyopt.ephys as ephys


class ClassforTesting(ephys.serializer.DictMixin):

    """Test class for serializer"""
    SERIALIZED_FIELDS = ('string', 'boolean', 'float_', 'list_', 'dict_')

    def __init__(self, string, boolean, float_, list_, dict_):
        self.string = string
        self.boolean = boolean
        self.float_ = float_
        self.list_ = list_
        self.dict_ = dict_


class NestedClassforTesting(ephys.serializer.DictMixin):

    """Nested test class for serializer"""

    SERIALIZED_FIELDS = ('test', 'tuples', 'lists', 'dicts', )

    def __init__(self, test, tuples, lists, dicts):
        self.test = test
        self.tuples = tuples
        self.lists = lists
        self.dicts = dicts


@pytest.mark.unit
def test_serializer():
    """ephys.serializer: test serialization of test class"""
    tc = ClassforTesting('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    assert isinstance(serialized, dict)
    json.dumps(serialized)


@pytest.mark.unit
def test_roundtrip_serializer():
    """ephys.serializer: test round trip of serialization of test class"""

    tc = ClassforTesting('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    instantiated = ephys.serializer.instantiator(serialized)
    assert isinstance(instantiated, ClassforTesting)


@pytest.mark.unit
def test_nested_serializer():
    """ephys.serializer: test a nested serialization of test class"""

    tc = ClassforTesting('some string', False, 1.0, [1, 2, 3], {'0': 0})
    ntc = NestedClassforTesting(
        test=tc, tuples=(tc,),
        lists=[tc] * 3, dicts={0: tc})
    serialized = ntc.to_dict()
    json.dumps(serialized, indent=2)

    instantiated = ephys.serializer.instantiator(serialized)
    assert isinstance(instantiated, NestedClassforTesting)
    assert isinstance(instantiated.lists[0], ClassforTesting)
    assert isinstance(instantiated.dicts[0], ClassforTesting)


@pytest.mark.unit
def test_non_instantiable():
    """ephys.serializer: test non instantiable class"""
    with pytest.raises(Exception):
        ephys.serializer.instantiator(
            {'some': 'fake', 'class': ephys.serializer.SENTINAL, })
