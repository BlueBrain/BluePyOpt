"""Simple cell test model"""

import os

import bluepyopt.ephys as ephys

nrn_sim = ephys.simulators.NrnSimulator()

morph = ephys.morphologies.NrnFileMorphology(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'simple.swc'))
somatic_loc = ephys.locations.NrnSeclistLocation(
    'somatic',
    seclist_name='somatic')
hh_mech = ephys.mechanisms.NrnMODMechanism(
    name='hh',
    prefix='hh',
    locations=[somatic_loc])


cm_param = ephys.parameters.NrnSectionParameter(
    name='cm',
    param_name='cm',
    value=1.0,
    locations=[somatic_loc],
    frozen=True)


gnabar_param = ephys.parameters.NrnSectionParameter(
    name='gnabar_hh',
    param_name='gnabar_hh',
    locations=[somatic_loc],
    bounds=[0.05, 0.125],
    frozen=False)
gkbar_param = ephys.parameters.NrnSectionParameter(
    name='gkbar_hh',
    param_name='gkbar_hh',
    bounds=[0.01, 0.075],
    locations=[somatic_loc],
    frozen=False)

cell_model = ephys.models.CellModel(
    name='simple_cell',
    morph=morph,
    mechs=[hh_mech],
    params=[cm_param, gnabar_param, gkbar_param])

default_param_values = {'gnabar_hh': 0.1, 'gkbar_hh': 0.03}
