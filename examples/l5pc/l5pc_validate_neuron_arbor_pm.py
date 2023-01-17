#!/usr/bin/env python

import os
import sys
import traceback
import json
import argparse
import random
import itertools
try:
    import papermill
except ImportError:
    raise ImportError('Please install papermill to batch-process'
                      ' l5pc_validate_neuron_arbor notebook.')


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description=
    'Run l5pc_validate_neuron_arbor notebook with papermill using different options.')
parser.add_argument('--output-dir', type=str, default='.',
                    help='Output directory')
parser.add_argument('--regions', type=str, nargs='+',
                    help='L5PC mechanisms to use: region[:mech1,mech2,...].')
parser.add_argument('--powerset', type=int,
                    help='Process powerset of local mechs up to this size.')
parser.add_argument('--param-values', type=str,
                    help='JSON file with parameter values'
                         ' (instead of using random sampling).')
parser.add_argument('--prepare-only', action='store_true',
                    help='Prepare notebooks only, do not run them.)')
parser.add_argument('--default-dt', type=float, default=0.025,
                    help='dt used for time-integration by default.')
parser.add_argument('--run-fine-dt', action='store_true',
                    help='Run time-integration with fine dt (0.001).')
parser.add_argument('--rel-l1-tolerance', type=float, default=0.05,
                    help='Tolerance for rel. Arbor-Neuron L1-difference.')
args = parser.parse_args()

output_dir = os.path.abspath(args.output_dir)
os.makedirs(output_dir, exist_ok=True)
output_dir = os.path.relpath(output_dir, start=SCRIPT_DIR)

param_values_json = args.param_values
if param_values_json is not None:
    param_values_json = os.path.relpath(param_values_json, start=SCRIPT_DIR)

os.chdir(SCRIPT_DIR)

import l5pc_model

# load all mechs and params of L5PC
all_mechanisms = l5pc_model.load_mechanisms()

all_parameters = l5pc_model.load_parameters()

if param_values_json is None:
    param_values_json = os.path.join(output_dir, 'param_values.json')

    num_samples = 5
    with open(param_values_json, 'w') as f:
        param_values = [{param['param_name'] + '.' + param['sectionlist']:
                            random.uniform(*param['bounds'])
                        for param in all_parameters
                        if 'bounds' in param}
                        for i in range(num_samples)]

        if 'hh' in all_mechanisms.get('somatic', []):
            for i in range(len(param_values)):
                param_values[i].update({
                    'gnabar_hh.somatic': random.uniform(0.05, 0.125),
                    'gkbar_hh.somatic': random.uniform(0.01, 0.075)})
        json.dump(param_values, f, indent=4)

    logger.info('Dumped parameter values to %s.' % param_values_json)


def powerset(mechs):  # from itertools docs
    mechs = list(mechs)
    for count in range(len(mechs) + 1):
        for mech_comb in itertools.combinations(mechs, count):
            yield list(mech_comb)


def get_extra_params(loc, mechs):
    extra_params = {
        p['param_name']: p['type'] for p in all_parameters
        if p['type'] == 'global'
        }

    for p in all_parameters:
        if 'sectionlist' in p and \
        p['sectionlist'] in ['all', loc] and \
        'mech' not in p:
            if p['param_name'] == 'ena' and \
                not any([m[:2] in ['Na'] for m in mechs]):
                continue
            if p['param_name'] == 'ek' and \
                not any([m[:2] in ['Im', 'K_', 'SK'] for m in mechs]):
                continue
            if p['param_name'] == 'eca' and \
                not any([m[:2] in ['Ca'] for m in mechs]):
                continue
            if p['param_name'] not in extra_params:
                extra_params[p['param_name']] = [p['sectionlist']]
            else:
                extra_params[p['param_name']].append(p['sectionlist'])
    return extra_params


for loc, loc_mechs in all_mechanisms.items():

    if args.regions is not None:
        region = [r for r in args.regions if r.startswith(loc)]
        if len(region) == 0:
            continue
        elif len(region) > 1:
            raise ValueError('Multiple values supplied for region %s.' % loc)
        else:
            region = region[0]
            if ':' in region:  # filter for selected mechs
                loc_mechs_subset = region.split(':')[1].split(',')
                for mech in loc_mechs_subset:
                    if mech not in loc_mechs:
                        raise ValueError('Mechanism %s not in region %s.'
                                        % (mech, loc))
                logger.info('Reducing local mechs on %s from %s to %s.',
                    region, loc_mechs, loc_mechs_subset)
                loc_mechs = loc_mechs_subset


    # First test the entire region
    mechanism_defs = {
        'all': ['pas'],
        loc: loc_mechs
    }

    extra_params = get_extra_params(loc, loc_mechs)

    target_file = os.path.join(output_dir, 'l5pc_validate_neuron_arbor_%s.ipynb' % loc)
    if os.path.exists(target_file):
        raise FileExistsError('Invalid target file - exists already: ',
                              target_file)

    logger.info('Outputting l5pc_validate_neuron_arbor notebook to %s '
                'with all local mechs/params...\n'
                'mechs = %s\nextra_params = %s',
                target_file, mechanism_defs, extra_params)

    try:
        papermill.execute_notebook(
            'l5pc_validate_neuron_arbor.ipynb',
            target_file,
            parameters=dict(mechanism_defs=mechanism_defs,
                            extra_params=extra_params,
                            param_values_json=param_values_json,
                            default_dt=args.default_dt,
                            run_spike_time_analysis=False,
                            run_fine_dt=args.run_fine_dt,
                            voltage_residual_rel_l1_tolerance=
                                args.rel_l1_tolerance),
            prepare_only=args.prepare_only
        )
    except papermill.exceptions.PapermillException:
        traceback.print_exception(*sys.exc_info())

    # Test subsets of local mechanisms in ascending size
    if args.powerset is not None:
        for mechs in powerset(loc_mechs):
            if len(mechs) < 1 or len(mechs) > args.powerset or \
                len(mechs) == len(loc_mechs):
                continue

            mechanism_defs = {
                'all': ['pas'],
                loc: mechs
            }

            extra_params = get_extra_params(loc, mechs)

            target_file = os.path.join(output_dir, 'l5pc_validate_neuron_arbor_%s_%s.ipynb' % \
                (loc, '_'.join(mechs)))
            if os.path.exists(target_file):
                raise FileExistsError('Invalid target file - exists already: ',
                                      target_file)
            logger.info('Outputting l5pc_validate_neuron_arbor notebook to %s'
                        ' with...\nmechs = %s\nextra_params = %s',
                        target_file, mechanism_defs, extra_params)

            try:
                papermill.execute_notebook(
                    'l5pc_validate_neuron_arbor.ipynb',
                    target_file,
                    parameters=dict(mechanism_defs=mechanism_defs,
                                    extra_params=extra_params,
                                    param_values_json=param_values_json,
                                    default_dt=args.default_dt,
                                    run_spike_time_analysis=False,
                                    run_fine_dt=args.run_fine_dt,
                                    voltage_residual_rel_l1_tolerance=
                                        args.rel_l1_tolerance),
                    prepare_only=args.prepare_only
                )
            except papermill.exceptions.PapermillException:
                traceback.print_exception(*sys.exc_info())

