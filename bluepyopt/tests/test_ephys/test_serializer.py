"""Test for ephys.serializer"""

import json
import nose.tools as nt
from nose.plugins.attrib import attr

import bluepyopt.ephys as ephys


class TestClass(ephys.serializer.DictMixin):

    """Test class for serializer"""
    SERIALIZED_FIELDS = ('string', 'boolean', 'float_', 'list_', 'dict_')

    def __init__(self, string, boolean, float_, list_, dict_):
        self.string = string
        self.boolean = boolean
        self.float_ = float_
        self.list_ = list_
        self.dict_ = dict_


class NestedTestClass(ephys.serializer.DictMixin):

    """Nested test class for serializer"""

    SERIALIZED_FIELDS = ('test', 'tuples', 'lists', 'dicts', )

    def __init__(self, test, tuples, lists, dicts):
        self.test = test
        self.tuples = tuples
        self.lists = lists
        self.dicts = dicts


@attr('unit')
def test_serializer():
    """ephys.serializer: test serialization of test class"""
    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    nt.ok_(isinstance(serialized, dict))
    json.dumps(serialized)


@attr('unit')
def test_roundtrip_serializer():
    """ephys.serializer: test round trip of serialization of test class"""

    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    instantiated = ephys.serializer.instantiator(serialized)
    nt.ok_(isinstance(instantiated, TestClass))


@attr('unit')
def test_nested_serializer():
    """ephys.serializer: test a nested serialization of test class"""

    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    ntc = NestedTestClass(
        test=tc, tuples=(tc,),
        lists=[tc] * 3, dicts={0: tc})
    serialized = ntc.to_dict()
    json.dumps(serialized, indent=2)

    instantiated = ephys.serializer.instantiator(serialized)
    nt.ok_(isinstance(instantiated, NestedTestClass))
    nt.ok_(isinstance(instantiated.lists[0], TestClass))
    nt.ok_(isinstance(instantiated.dicts[0], TestClass))


@attr('unit')
@nt.raises(Exception)
def test_non_instantiable():
    """ephys.serializer: test non instantiable class"""
    ephys.serializer.instantiator(
        {'some': 'fake', 'class': ephys.serializer.SENTINAL, })
