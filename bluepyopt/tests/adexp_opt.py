#!/usr/bin/env python
# coding: utf-8
SILENT = True
import warnings

if SILENT:
    warnings.filterwarnings("ignore")


import numpy as np
import efel
import matplotlib.pyplot as plt
import quantities as qt

from neuronunit.allenapi.allen_data_efel_features_opt import (
    opt_to_model,
    opt_setup,
    opt_exec,
)
from neuronunit.allenapi.allen_data_efel_features_opt import opt_to_model
from neuronunit.allenapi.utils import dask_map_function

from neuronunit.optimization.model_parameters import (
    MODEL_PARAMS,
    BPO_PARAMS,
    to_bpo_param,
)
from neuronunit.optimization.optimization_management import inject_model_soma
from neuronunit.models.optimization_model_layer import OptimizationModel
from jithub.models import model_classes
from sciunit.scores import RelativeDifferenceScore

from nose.plugins.attrib import attr
import unittest
import nose.tools as nt


@attr("unit")
def test_import():
    """bluepyopt: test importing neuronunit"""
    from neuronunit.allenapi.allen_data_efel_features_opt import (
        opt_to_model,
        opt_setup,
        opt_exec,
    )
    from neuronunit.allenapi.allen_data_efel_features_opt import opt_to_model
    from neuronunit.allenapi.utils import dask_map_function

    from neuronunit.optimization.model_parameters import (
        MODEL_PARAMS,
        BPO_PARAMS,
        to_bpo_param,
    )
    from neuronunit.optimization.optimization_management import inject_model_soma
    from jithub.models import model_classes
    from sciunit.scores import RelativeDifferenceScore


class testOptimization(unittest.TestCase):
    def setUp(self):
        self.ids = [
            324257146,
            325479788,
            476053392,
            623893177,
            623960880,
            482493761,
            471819401,
        ]

    @attr("unit")
    def test_opt_1(self):
        specimen_id = self.ids[1]
        cellmodel = "ADEXP"

        if cellmodel == "IZHI":
            model = model_classes.IzhiModel()
        if cellmodel == "MAT":
            model = model_classes.MATModel()
        if cellmodel == "ADEXP":
            model = model_classes.ADEXPModel()

        target_num_spikes = 9

        efel_filter_iterable = [
            "ISI_log_slope",
            "mean_frequency",
            "adaptation_index2",
            "first_isi",
            "ISI_CV",
            "median_isi",
            "Spikecount",
            "all_ISI_values",
            "ISI_values",
            "time_to_first_spike",
            "time_to_last_spike",
            "time_to_second_spike",
        ]
        [suite, target_current, spk_count, cell_evaluator, simple_cell] = opt_setup(
            specimen_id,
            cellmodel,
            target_num_spikes,
            template_model=model,
            fixed_current=False,
            cached=False,
            score_type=RelativeDifferenceScore,
            efel_filter_iterable=efel_filter_iterable,
        )

        NGEN = 55
        MU = 35

        mapping_funct = dask_map_function
        final_pop, hall_of_fame, logs, hist = opt_exec(
            MU, NGEN, mapping_funct, cell_evaluator, cxpb=0.4, mutpb=0.01
        )
        opt, target, scores, obs_preds, df = opt_to_model(
            hall_of_fame, cell_evaluator, suite, target_current, spk_count
        )
        best_ind = hall_of_fame[0]
        fitnesses = cell_evaluator.evaluate_with_lists(best_ind)
        assert np.sum(fitnesses) < 10.7
        nt.assert_is_instance(10.7, np.sum(fitnesses))
        self.assertGreater(10.7, np.sum(fitnesses))


if __name__ == "__main__":
    unittest.main()
