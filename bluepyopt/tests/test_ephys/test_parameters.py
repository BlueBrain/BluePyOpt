import json

import nose.tools as nt

from bluepyopt import ephys
from bluepyopt.ephys.parameters import (NrnGlobalParameter, NrnSectionParameter,
                                        NrnRangeParameter, )

from bluepyopt.ephys.locations import NrnSeclistLocation
from bluepyopt.ephys.serializer import instantiator


def test_serialize():
    value, frozen, bounds, param_name = 65, False, [0, 100.0], 'gSKv3_1bar_SKv3_1'
    value_scaler = ephys.parameterscalers.NrnSegmentLinearScaler()
    locations = (NrnSeclistLocation('Location0', 'somatic'),
                 NrnSeclistLocation('Location1', 'apical'),
                 )

    parameters = (
        NrnGlobalParameter('NrnGlobalParameter', value, frozen, bounds, param_name),
        NrnSectionParameter(
            'NrnSectionParameter', value, frozen, bounds, param_name, value_scaler, locations ),
        NrnRangeParameter(
            'NrnRangeParameter', value, frozen, bounds, param_name, value_scaler, locations),
    )

    for param in parameters:
        serialized = param.to_dict()
        nt.ok_(isinstance(json.dumps(serialized), str))
        deserialized = instantiator(serialized)
        nt.ok_(isinstance(deserialized, param.__class__))
        nt.eq_(deserialized.name, param.__class__.__name__)
