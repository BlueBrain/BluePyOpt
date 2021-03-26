#!/usr/bin/env python
# coding: utf-8
import unittest


#import matplotlib

import numpy as np
from neuronunit.optimization.model_parameters import (
    MODEL_PARAMS,
    BPO_PARAMS,
    to_bpo_param
)
from neuronunit.optimization.optimization_management import (
    model_to_rheo,
    inject_and_plot_model
)
from jithub.models import model_classes
import matplotlib.pyplot as plt
import quantities as qt
import unittest
import nose.tools as nt



class testOptimization(unittest.TestCase):
    def setUp(self):
        self = self
    #@attr('unit')
    def test_opt_1(self):
        model_type = "ADEXP"

        if model_type == "IZHI":
            from jithub.models.model_classes import IzhiModel
            cellmodel = IzhiModel()
        if model_type == "ADEXP":
            from jithub.models.model_classes import ADEXPModel
            cellmodel = ADEXPModel()

        cellmodel.params = {k: np.mean(v) for k, v in MODEL_PARAMS[model_type].items()}
        cellmodel = model_to_rheo(cellmodel)
        #assert cellmodel.rheobase is not None
        self.assertIsNotNone(cellmodel.rheobase)
        vm, plt, cellmodel = inject_and_plot_model(cellmodel, plotly=False)
        self.assertIsNotNone(vm)
        self.assertIsNotNone(cellmodel)


if __name__ == "__main__":
    unittest.main()
