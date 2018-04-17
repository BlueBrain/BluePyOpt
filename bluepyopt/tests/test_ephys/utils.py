"""EPhys test utils"""

from bluepyopt import ephys
from bluepyopt.ephys.parameters import (
    NrnGlobalParameter, NrnSectionParameter, NrnRangeParameter,)
from bluepyopt.ephys.locations import NrnSeclistLocation


def make_mech():
    """Create mechanism"""
    basal = ephys.locations.NrnSeclistLocation('basal', seclist_name='basal')
    apical = ephys.locations.NrnSeclistLocation(
        'apical', seclist_name='apical')
    return ephys.mechanisms.NrnMODMechanism(
        'Ih',
        suffix='Ih',
        locations=[
            basal,
            apical,
        ])


def make_parameters():
    """Create parameters"""
    value, frozen, bounds, param_name = 65, False, [
        0, 100.0], 'gSKv3_1bar_SKv3_1'
    value_scaler = ephys.parameterscalers.NrnSegmentLinearScaler()
    locations = (NrnSeclistLocation('Location0', 'somatic'),
                 NrnSeclistLocation('Location1', 'apical'),)
    parameters = (
        NrnGlobalParameter(
            'NrnGlobalParameter',
            value,
            frozen,
            bounds,
            param_name),
        NrnSectionParameter(
            'NrnSectionParameter',
            value,
            frozen,
            bounds,
            param_name,
            value_scaler,
            locations),
        NrnRangeParameter(
            'NrnRangeParameter',
            value,
            frozen,
            bounds,
            param_name,
            value_scaler,
            locations),
    )
    return parameters
