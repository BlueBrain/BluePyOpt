import json

import nose.tools as nt

import utils
from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


def test_mechanism_serialize():
    mech = utils.make_mech()
    serialized = mech.to_dict()
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.mechanisms.NrnMODMechanism))
