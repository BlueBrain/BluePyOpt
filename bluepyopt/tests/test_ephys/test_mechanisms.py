import json
from os.path import join as joinp

import nose.tools as nt

from bluepyopt import ephys
from bluepyopt.ephys.serializer import instantiator


def test_mechanism_serialize():
    basal = ephys.locations.NrnSeclistLocation('basal', seclist_name='basal')
    apical = ephys.locations.NrnSeclistLocation('apical', seclist_name='apical')
    mech = ephys.mechanisms.NrnMODMechanism('Ih', prefix='Ih', locations=[basal, apical, ])
    serialized = mech.to_dict()
    nt.ok_(isinstance(json.dumps(serialized), str))
    deserialized = instantiator(serialized)
    nt.ok_(isinstance(deserialized, ephys.mechanisms.NrnMODMechanism))
