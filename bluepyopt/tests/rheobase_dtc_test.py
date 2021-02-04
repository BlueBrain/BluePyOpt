import unittest

#!/usr/bin/env python
# coding: utf-8
import matplotlib

import numpy as np
from neuronunit.optimization.model_parameters import (
    MODEL_PARAMS,
    BPO_PARAMS,
    to_bpo_param
)
from neuronunit.optimization.optimization_management import (
    dtc_to_rheo,
    inject_and_plot_model
)
from neuronunit.optimization.data_transport_container import DataTC
from jithub.models import model_classes
import matplotlib.pyplot as plt
import quantities as qt


class testOptimization(unittest.TestCase):
    def setUp(self):
        self = self

    def test_opt_1(self):
        model_type = "ADEXP"

        if model_type == "IZHI":
            from jithub.models.model_classes import IzhiModel
            cellmodel = IzhiModel()
        #    model = model_classes.IzhiModel()
        #if cellmodel == "MAT":
        #    model = model_classes.MATModel()
        if model_type == "ADEXP":
            from jithub.models.model_classes import ADEXPModel
            cellmodel = ADEXPModel()

        #    model = model_classes.ADEXPModel()

        #dtc = DataTC(backend=cellmodel)
        #assert dtc.backend == cellmodel
        cellmodel.params = {k: np.mean(v) for k, v in MODEL_PARAMS[model_type].items()}
        #other_params = BPO_PARAMS[cellmodel]
        cellmodel = dtc_to_rheo(cellmodel)
        print(cellmodel.rheobase)
        assert cellmodel.rheobase is not None
        self.assertIsNotNone(cellmodel.rheobase)
        vm, plt, cellmodel = inject_and_plot_model(cellmodel, plotly=False)
        self.assertIsNotNone(vm)

        self.assertIsNotNone(cellmodel)


if __name__ == "__main__":
    unittest.main()
