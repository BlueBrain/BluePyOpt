"""Get stats out of ipyparallel's tasks.db"""

from __future__ import print_function

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import sys
import os
import argparse
import sqlite3
import collections
import datetime
import dateutil.parser
import itertools

import numpy as np
import matplotlib.pyplot as plt


def get_engine_data(tasksdb_filename):
    """Main"""
    conn = sqlite3.connect(tasksdb_filename)

    cursor = conn.cursor()

    tasks = collections.defaultdict(list)

    SQL = 'SELECT started, completed, engine_uuid FROM "ipython-tasks";'

    for started, completed, engine_uuid in cursor.execute(SQL).fetchall():
        if started and completed:
            started = dateutil.parser.parse(started)
            completed = dateutil.parser.parse(completed)

            duration = (
                completed -
                started).total_seconds() if completed else None
            task = {'started': started,
                    'completed': completed,
                    'duration': duration,
                    'engine_uuid': engine_uuid}

            tasks[engine_uuid].append(task)

    if len(tasks) == 0:
        raise Exception("No completed tasks found in the db")

    engine_number_map = dict(zip(tasks.keys(), range(len(tasks.keys()))))
    return tasks, engine_number_map


def plot_usage(tasks, engine_number_map):
    """Plot usage stats"""

    plt.figure(figsize=(8, 8))
    for engine_uuid, task_list in tasks.items():
        engine_number = engine_number_map[engine_uuid]
        number_list = [engine_number] * len(task_list)
        start_list = [task['started'] for task in task_list]
        completed_list = [task['completed'] for task in task_list]
        plt.plot(
            [number_list, number_list],
            [start_list, completed_list], linewidth=10,
            solid_capstyle="butt")

    plt.xlim(min(engine_number_map.values()) - 1,
             max(engine_number_map.values()) + 1)
    plt.xlabel('Compute engine number')
    plt.ylabel('Compute time')

    idle_time, idle_perc = calculate_unused_compute(tasks)
    plt.title(
        'Cumulative idle time: %s, perc: %.2f %%' %
        (idle_time, idle_perc))


def plot_duration_histogram(tasks):
    """Plot duration histogram"""
    plt.figure(figsize=(8, 8))

    durations = np.fromiter((t['duration']
                             for task_list in tasks.values()
                             for t in task_list),
                            dtype=np.float)
    plt.hist(durations, 100)

    plt.xlabel('Duration (s)')
    plt.ylabel('Count')
    plt.title('Histogram of task execution')
    plt.grid(True)


def calculate_unused_compute(tasks):
    """Calculate unused compute time"""

    all_tasks = list(itertools.chain.from_iterable(tasks.values()))
    start_time = min(task['started'] for task in all_tasks)
    end_time = max(task['completed'] for task in all_tasks)
    total_compute_time = sum(
        (datetime.timedelta(seconds=task['duration'])
         for task in all_tasks), datetime.timedelta())

    n_of_engines = len(tasks.keys())

    idle_time = n_of_engines * (end_time - start_time) - total_compute_time
    idle_perc = 100 * \
        (idle_time.total_seconds() / total_compute_time.total_seconds())
    return idle_time, idle_perc


def run(arg_list):
    """Main run"""

    parser = argparse.ArgumentParser()
    parser.add_argument('tasksdb_filename')
    args = parser.parse_args(arg_list)

    if not os.path.isfile(args.tasksdb_filename):
        raise IOError('Tasks db file not found at: %s' % args.tasksdb_filename)

    tasks, engine_number_map = get_engine_data(args.tasksdb_filename)
    plot_usage(tasks, engine_number_map)
    plot_duration_histogram(tasks)

    plt.show()


def main():
    """Main"""

    run(sys.argv[1:])


if __name__ == '__main__':
    main()
