import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import quantities as qt
import os

from neuronunit.allenapi.allen_data_driven import opt_exec
from neuronunit.allenapi.allen_data_driven import opt_to_model, wrap_setups
from neuronunit.allenapi.utils import dask_map_function
from neuronunit.optimization.model_parameters import (
    MODEL_PARAMS,
    BPO_PARAMS,
    to_bpo_param,
)
from neuronunit.optimization.optimization_management import inject_and_plot_model

#from neuronunit.optimization.data_transport_container import DataTC
from jithub.models import model_classes

from sciunit.scores import RelativeDifferenceScore, ZScore
from sciunit.utils import config_set

config_set("PREVALIDATE", False)

SILENT = True
import warnings

if SILENT:
    warnings.filterwarnings("ignore")


def rounding(params):
    for k,v in params.items():
        if np.round(v, 1) != 0:
            params[k] = np.round(v, 1)
    return params

def optimize_job(
    specimen_id,
    model_type,
    score_type=RelativeDifferenceScore,
    efel_filter_iterable=None,NGEN = 100, MU=20
):
    find_sweep_with_n_spikes = 8

    if model_type is str("ADEXP"):
        from jithub.models.model_classes import ADEXPModel
        model = ADEXPModel()
    if model_type is str("IZHI"):
        from jithub.models.model_classes import IzhiModel
        model = IzhiModel()

    model.params = BPO_PARAMS[model_type]
    fixed_current = 122 *qt.pA

    mapping_funct = dask_map_function
    [ cell_evaluator,
    simple_cell,
    suite,
    target_current,
    spk_count ] = wrap_setups(
        specimen_id,
        model_type,
        find_sweep_with_n_spikes,
        template_model=model,
        fixed_current=False,
        cached=False,
        score_type=score_type,
        efel_filter_iterable=efel_filter_iterable

    )
    final_pop, hall_of_fame, logs, hist = opt_exec(
        MU, NGEN, mapping_funct, cell_evaluator,neuronunit=True
    )
    opt, target, scores, obs_preds, df = opt_to_model(
        hall_of_fame, cell_evaluator, suite, target_current, spk_count
    )
    best_ind = hall_of_fame[0]
    fitnesses = cell_evaluator.evaluate_with_lists(best_ind)
    target.vm_soma = suite.traces["vm_soma"]
    return np.sum(fitnesses), scores, obs_preds, opt, target,hall_of_fame,cell_evaluator
