#!/usr/bin/env python
# coding: utf-8

import unittest
import matplotlib

matplotlib.use("Agg")
SILENT = True
import warnings

if SILENT:
    warnings.filterwarnings("ignore")

from neuronunit.allenapi.allen_data_driven import opt_setup, opt_setup_two, opt_exec
from neuronunit.allenapi.allen_data_driven import opt_to_model, wrap_setups
from neuronunit.allenapi.utils import dask_map_function
from neuronunit.optimization.model_parameters import (
    MODEL_PARAMS,
    BPO_PARAMS,
    to_bpo_param,
)
from neuronunit.optimization.optimization_management import (
    inject_and_plot_model
)
import numpy as np
from neuronunit.models.optimization_model_layer import OptimizationModel
from jithub.models import model_classes
import matplotlib.pyplot as plt
import quantities as qt
import os

from sciunit.scores import RelativeDifferenceScore, ZScore
from sciunit.utils import config_set, config_get

config_set("PREVALIDATE", False)
assert config_get("PREVALIDATE") is False


class testOptimizationAllenMultiSpike(unittest.TestCase):
    def setUp(self):
        self = self
        # In principle any index into data should work
        # but '1' is chosen here. Robust tests would use any index.
        self.ids = [
            324257146,
            325479788,
            476053392,
            623893177,
            623960880,
            482493761,
            471819401,
        ]
        self.specimen_id = self.ids[1]
    def optimize_job(self, model_type, score_type=ZScore):
        find_sweep_with_n_spikes = 8
        from jithub.models.model_classes import ADEXPModel
        model = ADEXPModel()
        model.params = BPO_PARAMS[model_type]
        fixed_current = 122 * qt.pA
        if model_type == "ADEXP":
            NGEN = 55
            MU = 16
        else:
            NGEN = 45
            MU = 100

        mapping_funct = dask_map_function
        cell_evaluator, simple_cell, suite, target_current, spk_count = wrap_setups(
            self.specimen_id,
            model_type,
            find_sweep_with_n_spikes,
            template_model=model,
            fixed_current=False,
            cached=False,
            score_type=score_type,
        )
        final_pop, hall_of_fame, logs, hist = opt_exec(
            MU, NGEN, mapping_funct, cell_evaluator
        )
        opt, target, scores, obs_preds, df = opt_to_model(
            hall_of_fame, cell_evaluator, suite, target_current, spk_count
        )
        best_ind = hall_of_fame[0]
        fitnesses = cell_evaluator.evaluate_with_lists(best_ind)
        target.vm_soma = suite.traces["vm_soma"]
        return np.sum(fitnesses)

    def test_opt_relative_diff(self):
        model_type = "ADEXP"
        sum_fit = self.optimize_job(model_type, score_type=RelativeDifferenceScore)
        assert sum_fit < 42.0

    # this is just to speed up CI tests to avoid timeout.
    @unittest.skip
    def test_opt_ZScore(self):
        model_type = "ADEXP"
        sum_fit = self.optimize_job(model_type, score_type=ZScore)
        assert sum_fit < 2.1

    @unittest.skip
    def test_opt_relative_diff_izhi(self):
        model_type = "IZHI"
        self.optimize_job(model_type, score_type=RelativeDifferenceScore)
        assert sum_fit < 32.0

    # this is just to speed up CI tests to avoid timeout.
    @unittest.skip
    def test_opt_ZScore_izhi(self):
        model_type = "IZHI"
        self.optimize_job(model_type, score_type=ZScore)
        assert sum_fit < 2.1
