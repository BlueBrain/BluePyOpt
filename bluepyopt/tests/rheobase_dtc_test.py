import unittest
#!/usr/bin/env python
# coding: utf-8
import matplotlib

import numpy as np
from neuronunit.optimization.model_parameters import MODEL_PARAMS, BPO_PARAMS, to_bpo_param
from neuronunit.optimization.optimization_management import dtc_to_rheo,inject_and_plot_model
from neuronunit.optimization.data_transport_container import DataTC
from jithub.models import model_classes
import matplotlib.pyplot as plt
import quantities as qt

class testOptimization(unittest.TestCase):
    def setUp(self):
        self = self

    def test_opt_1(self):
        cellmodel = "ADEXP"

        if cellmodel == "IZHI":
            model = model_classes.IzhiModel()
        if cellmodel == "MAT":
            model = model_classes.MATModel()
        if cellmodel == "ADEXP":
            model = model_classes.ADEXPModel()

        dtc = DataTC()
        dtc.backend = cellmodel
        dtc._backend = model._backend
        dtc.attrs = model.attrs
        dtc.params = {k:np.mean(v) for k,v in MODEL_PARAMS[cellmodel].items()}
        other_params = BPO_PARAMS[cellmodel]
        dtc = dtc_to_rheo(dtc)
        assert dtc.rheobase is not None
        self.assertIsNotNone(dtc.rheobase)
        vm, plt, dtc = inject_and_plot_model(dtc, plotly=False)
        self.assertIsNotNone(vm)
        model = dtc.dtc_to_model()
        self.assertIsNotNone(model)


if __name__ == "__main__":
    unittest.main()
