import unittest
import nose as nt
import jithub
from jithub.models import model_classes
import quantities as pq
cellmodels = ["IZHI","ADEXP"]
import numpy as np
import matplotlib.pyplot as plt
import collections
import quantities as pq
import time

DELAY = 0*pq.ms
DURATION = 250 *pq.ms

# https://www.izhikevich.org/publications/spikes.htm
type2007 = collections.OrderedDict([
  #              C    k     vr  vt vpeak   a      b   c    d  celltype
  ('RS',        (100, 0.7,  -60, -40, 35, 0.03,   -2, -50,  100,  1)),
  ('IB',        (150, 1.2,  -75, -45, 50, 0.01,   5, -56,  130,   2)),
  ('TC',        (200, 1.6,  -60, -50, 35, 0.01,  15, -60,   10,   6)),
  ('LTS',       (100, 1.0,  -56, -42, 40, 0.03,   8, -53,   20,   4)),
  ('RTN',       (40,  0.25, -65, -45, 0,  0.015, 10, -55,  50,    7)),
  ('FS',        (20,  1,    -55, -40, 25, 0.2,   -2, -45,  -55,   5)),
  ('CH',        (50,  1.5,  -60, -40, 25, 0.03,   1, -40,  150,   3))])



trans_dict = collections.OrderedDict([(k,[]) for k in ['C','k','vr','vt','vPeak','a','b','c','d','celltype']])
for i,k in enumerate(trans_dict.keys()):
    for v in type2007.values():
        trans_dict[k].append(v[i])


reduced_cells = collections.OrderedDict([(k,[]) for k in ['RS','IB','TC','LTS','RTN','FS','CH']])
for index,key in enumerate(reduced_cells.keys()):
    reduced_cells[key] = {}
    for k,v in trans_dict.items():
        reduced_cells[key][k] = v[index]


for cellmodel in cellmodels:
    if cellmodel == "IZHI":
        model = model_classes.IzhiModel()
    if cellmodel == "MAT":
        model = model_classes.MATModel()
    if cellmodel == "ADEXP":
        model = model_classes.ADEXPModel()
    ALLEN_DELAY = 1000.0 * pq.ms
    ALLEN_DURATION = 2000.0 * pq.ms
    uc = {
        "amplitude": 25*pq.pA,
        "duration": ALLEN_DURATION,
        "delay": ALLEN_DELAY,
    }
    model.inject_square_current(**uc)
    vm = model.get_membrane_potential()
    try:
        assert float(int(np.round(vm.times[-1],0))) == float(ALLEN_DELAY) + float(ALLEN_DURATION)
    except:
        print(float(int(np.round(vm.times[-1],0))) == float(ALLEN_DELAY) + float(ALLEN_DURATION))
cellmodel = "IZHI"
IinRange = [60,70,85,100];

params = {}
params['amplitude'] = 500*pq.pA
params['delay'] = DELAY
params['duration'] = 600*pq.ms

model = model_classes.ADEXPModel()
model.set_attrs({'b':reduced_cells['RS']['b']})
assert model.attrs['b'] == reduced_cells['RS']['b']
for i,amp in enumerate(IinRange):

    model = model_classes.IzhiModel()
    model.set_attrs(reduced_cells['RS'])
    assert model.attrs['a'] == reduced_cells['RS']['a']
    params['amplitude'] = amp*pq.pA

    t1 = time.time()

    model.inject_square_current(**params)
    vm = model.get_membrane_potential()
    nt.tools.assert_is_not_none(vm)
    t2 = time.time()
    if i==0:
        print('compile time taken on block {0} '.format(t2-t1))
    else:
        print('time taken on block {0} '.format(t2-t1))



IinRange = [290,370,500,550];

params = {}
params['delay'] = DELAY
params['duration'] = 600*pq.ms


for i,amp in enumerate(IinRange):
    model = model_classes.IzhiModel()

    model.set_attrs(reduced_cells['IB'])
    assert model.attrs['a'] == reduced_cells['IB']['a']

    params['amplitude'] = amp


    model.inject_square_current(**params)
    vm = model.get_membrane_potential()
    nt.tools.assert_is_not_none(vm)
