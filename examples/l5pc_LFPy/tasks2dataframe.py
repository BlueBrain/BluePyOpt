#!/usr/bin/env python
'''Utility functions to read the tasks.db from ipyparallel when used
with BluePyOpt.

The script is executable, as an example on how to extract the top 10
longest running engines for the l5pc model.
'''

import sqlite3

import pandas
import numpy as np

from ipyparallel.controller import sqlitedb


def _open_db(dbfile):
    '''open the sqlite file, and set up the converters to serialize data'''
    sqlite3.register_adapter(dict, sqlitedb._adapt_dict)
    sqlite3.register_converter('dict', sqlitedb._convert_dict)
    sqlite3.register_adapter(list, sqlitedb._adapt_bufs)
    sqlite3.register_converter('bufs', sqlitedb._convert_bufs)
    db = sqlite3.connect(dbfile,
                         detect_types=sqlite3.PARSE_DECLTYPES,
                         cached_statements=64)
    return db


def _add_buffers(df, arg_names=None, result_names=None, delete_buffers=False):
    '''add argument and result buffers to the dataframe'''
    if arg_names is None:
        row = df['buffers'][0]
        count = len(sqlitedb._convert_bufs(row[3])[0])
        arg_names = ['arg_%02d' % i for i in range(count)]

    args = np.empty(shape=(df.shape[0], len(arg_names)))
    for i, row in enumerate(df['buffers']):
        # row[0] is pickled ref to __builtin__.map,
        # row[1] is pickled description of args:
        #  {'kw_keys': [], 'nargs': 2, 'narg_bufs': 2}
        # row[2] is pickled function to be mapped
        # row[3] are the pickled arguments, packed into a list
        args[i, :] = sqlitedb._convert_bufs(row[3])[0]
    args_df = pandas.DataFrame(args, columns=arg_names)

    if result_names is None:
        row = df['result_buffers'][0]
        count = len(sqlitedb._convert_bufs(row[0])[0])
        result_names = ['res_%02d' % i for i in range(count)]

    results = np.empty(shape=(df.shape[0], len(result_names)))
    for i, row in enumerate(df['result_buffers']):
        if row:
            # row[0] are the pickled results, in a list
            results[i, :] = sqlitedb._convert_bufs(row[0])[0]
        else:
            # either the task didn't return, or returned an error
            results[i, :] = float('NaN')
    results_df = pandas.DataFrame(results, columns=result_names)

    if delete_buffers:
        df.drop(['buffers', 'result_buffers'], axis=1, inplace=True)

    return pandas.concat(
        [df, args_df, results_df],
        axis=1, join_axes=[df.index])


def create_df(db, arg_names=None, result_names=None):
    '''convert a tasks_db to a pandas dataframe'''
    df = pandas.read_sql('select * from `ipython-tasks`;', db,
                         parse_dates=('submitted', 'started', 'completed',))
    df = _add_buffers(df, arg_names, result_names)
    return df


if __name__ == '__main__':
    import sys

    from l5pc_model import define_parameters
    arg_names = [p.name for p in define_parameters() if not p.frozen]

    from l5pc_evaluator import (define_protocols, define_fitness_calculator)
    fitness_protocols = define_protocols()
    fitness_calculator = define_fitness_calculator(fitness_protocols)
    result_names = [o.name for o in fitness_calculator.objectives]

    db_filename = sys.argv[1]
    db = _open_db(db_filename)
    df = create_df(db, arg_names, result_names)
    df['run_time'] = df['completed'] - df['started']

    pandas.set_option('display.expand_frame_repr', False)
    title = '10 Longest times'
    print('%s\n%s' % (title, '*' * len(title)))
    print(
        df.nlargest(10, 'run_time')
        [['run_time', ] + arg_names + result_names])
