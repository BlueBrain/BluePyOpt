import json

import nose.tools as nt

from bluepyopt.ephys.parameterscalers import (NrnSegmentLinearScaler,
                                              NrnSegmentSomaDistanceScaler, )
from bluepyopt.ephys.serializer import instantiator


def test_serialize():

    multiplier, offset, distribution = 12.12, 3.58, '1 + {distance}'
    paramscalers = (
        NrnSegmentLinearScaler('NrnSegmentLinearScaler', multiplier, offset),
        NrnSegmentSomaDistanceScaler('NrnSegmentSomaDistanceScaler', distribution),)

    for ps in paramscalers:
        serialized = ps.to_dict()
        nt.ok_(isinstance(json.dumps(serialized), str))
        deserialized = instantiator(serialized)
        nt.ok_(isinstance(deserialized, ps.__class__))
        nt.eq_(deserialized.name, ps.__class__.__name__)
