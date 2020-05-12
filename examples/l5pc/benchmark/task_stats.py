import sqlite3
import collections
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')


def get_engine_data():
    """Main"""
    conn = sqlite3.connect('tasks.db')

    cursor = conn.cursor()

    tasks = collections.defaultdict(list)

    SQL = 'SELECT started, completed, engine_uuid FROM "ipython-tasks";'

    TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
    for started, completed, engine_uuid in cursor.execute(SQL).fetchall():
        # TODO hardcoded 2016 for the moment, sometimes started contains strange
        # character (and is empty for the rest)
        if started and '2016' in started and completed:
            started = datetime.strptime(started, TIME_FORMAT)
            completed = datetime.strptime(completed, TIME_FORMAT)

            duration = (
                completed -
                started).total_seconds() if completed else None
            task = {'started': started,
                    'completed': completed,
                    'duration': duration,
                    'engine_uuid': engine_uuid,
                    }

            tasks[engine_uuid].append(task)

    # drop engines that only resolved a few tasks
    # TODO: figure out why there are 'ghost' engines that only exist at the
    # start
    for engine_uuid in tasks.keys():
        if len(tasks[engine_uuid]) < 10:
            del tasks[engine_uuid]

    engine_number_map = dict(zip(tasks.keys(), range(len(tasks.keys()))))
    return tasks, engine_number_map


def plot_usage(tasks, engine_number_map):
    fig, ax = plt.subplots(1, 1, facecolor='white')

    for engine_uuid, task_list in tasks.items():
        engine_number = engine_number_map[engine_uuid]
        number_list = [engine_number for _ in task_list]
        start_list = [task['started'] for task in task_list]
        completed_list = [task['completed'] for task in task_list]
        ax.plot(
            [number_list, number_list],
            [start_list, completed_list], linewidth=10,
            solid_capstyle="butt")

    ax.set_xlim(min(engine_number_map.values()) - 1,
                max(engine_number_map.values()) + 1)
    ax.set_xlabel('Compute engine number')
    ax.set_ylabel('Compute time')
    plt.show()


def plot_duration_histogram(tasks):
    durations = np.fromiter((t['duration']
                             for task_list in tasks.values()
                             for t in task_list),
                            dtype=np.float)
    plt.hist(durations, 100, range=(1, 160))

    plt.xlabel('Duration (s)')
    plt.ylabel('Count')
    plt.title('Histogram of task execution')
    plt.grid(True)
    plt.show()


def filter_start_time(start_time, tasks):
    ret = collections.defaultdict(list)
    for engine_uuid, task_list in tasks.items():
        for task in task_list:
            if task['started'] > start_time:
                ret[engine_uuid].append(task)
    return ret


def calculate_unused_compute(tasks):
    start_time, end_time = datetime.max, datetime.min
    total_time = timedelta()
    for task_lists in tasks.values():
        for task in task_lists:
            start_time = min(start_time, task['started'])
            end_time = max(end_time, task['completed'])
            total_time += timedelta(seconds=task['duration'])
    engines = len(tasks.keys())
    return engines * (end_time - start_time) - total_time


def main():
    tasks, engine_number_map = get_engine_data()
    plot_usage(tasks, engine_number_map)
    print('Unused compute total:', calculate_unused_compute(tasks))

    plot_duration_histogram(tasks)
    filtered_tasks = filter_start_time(datetime(2016, 4, 13, 13), tasks)
    plot_usage(filtered_tasks, engine_number_map)
    print('Unused compute last 30 minutes:', calculate_unused_compute(
        filtered_tasks))


if __name__ == '__main__':
    main()
