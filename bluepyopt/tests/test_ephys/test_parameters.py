import json

import nose.tools as nt

import utils
from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


def test_serialize():
    parameters = utils.make_parameters()

    for param in parameters:
        serialized = param.to_dict()
        nt.ok_(isinstance(json.dumps(serialized), str))
        deserialized = instantiator(serialized)
        nt.ok_(isinstance(deserialized, param.__class__))
        nt.eq_(deserialized.name, param.__class__.__name__)
