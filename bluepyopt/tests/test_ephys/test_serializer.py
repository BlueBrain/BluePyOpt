import json
import nose.tools as nt

from bluepyopt.ephys.serializer import DictMixin, instantiator, SENTINAL


class TestClass(DictMixin):
    SERIALIZED_FIELDS = ('string', 'boolean', 'float_', 'list_', 'dict_')
    def __init__(self, string, boolean, float_, list_, dict_):
        self.string = string
        self.boolean = boolean
        self.float_ = float_
        self.list_ = list_
        self.dict_ = dict_


def test_serializer():
    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    nt.ok_(isinstance(serialized, dict))
    dumps = json.dumps(serialized)


def test_roundtrip_serializer():
    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    serialized = tc.to_dict()
    instantiated = instantiator(serialized)
    nt.ok_(isinstance(instantiated, TestClass))


def test_nested_serializer():
    class NestedTestClass(DictMixin):
        SERIALIZED_FIELDS = ('test', 'tuples', 'lists', 'dicts', )
        def __init__(self, test, tuples, lists, dicts):
            self.test = test
            self.tuples = tuples
            self.lists = lists
            self.dicts = dicts

    tc = TestClass('some string', False, 1.0, [1, 2, 3], {'0': 0})
    ntc = NestedTestClass(test=tc, tuples=(tc, ), lists=[tc]*3, dicts={0: tc})
    serialized = ntc.to_dict()
    dumps = json.dumps(serialized, indent=2)

    instantiated = instantiator(serialized)
    nt.ok_(isinstance(instantiated, NestedTestClass))
    nt.ok_(isinstance(instantiated.lists[0], TestClass))
    nt.ok_(isinstance(instantiated.dicts[0], TestClass))


@nt.raises(Exception)
def test_non_instatiable():
    instantiator({'some': 'fake', 'class': SENTINAL, })
