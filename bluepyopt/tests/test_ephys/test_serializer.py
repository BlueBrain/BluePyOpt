import json
import nose.tools as nt

from bluepyopt.ephys.serializer import DictMixin, instantiator


class TestClass(DictMixin):
    SERIALIZED_FIELDS = ('string', 'boolean', 'float_', )
    def __init__(self, string, boolean, float_):
        self.string = string
        self.boolean = boolean
        self.float_ = float_


def test_serializer():
    tc = TestClass('some string', False, 1.0)
    serialized = tc.to_dict()
    nt.ok_(isinstance(serialized, dict))
    dumps = json.dumps(serialized)


def test_roundtrip_serializer():
    tc = TestClass('some string', False, 1.0)
    serialized = tc.to_dict()
    instantiated = instantiator(serialized)
    nt.ok_(isinstance(instantiated, TestClass))


def test_nested_serializer():
    class NestedTestClass(DictMixin):
        SERIALIZED_FIELDS = ('tuples', 'lists', 'dicts', )
        def __init__(self, tuples, lists, dicts):
            self.tuples = tuples
            self.lists = lists
            self.dicts = dicts

    tc = NestedTestClass((TestClass('some string', False, 1.0), ),
                         [TestClass('some string', False, 1.0)]*3,
                         {0: TestClass('some string', False, 2.0)})
    serialized = tc.to_dict()
    dumps = json.dumps(serialized)

    instantiated = instantiator(serialized)
    nt.ok_(isinstance(instantiated, NestedTestClass))
    nt.ok_(isinstance(instantiated.lists[0], TestClass))
    nt.ok_(isinstance(instantiated.dicts[0], TestClass))
