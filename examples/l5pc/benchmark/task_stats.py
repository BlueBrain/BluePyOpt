import sqlite3
import collections
import datetime


def main():
    """Main"""
    conn = sqlite3.connect('tasks.db')

    cursor = conn.cursor()

    tasks = collections.defaultdict(list)
    engine_uuids = []

    for msg_id, \
            header, meta_data, content, \
            buffers, \
            submitted, \
            client_uuid, engine_uuid, \
            started, completed, resubmitted, received, \
            result_header, result_metadata, result_content, result_buffers, \
            queue, \
            pyin, pyout, pyerr, \
            stdout, stderr in cursor.execute('SELECT * FROM "ipython-tasks";').fetchall():
        # TODO hardcoded 2016 for the moment, sometimes started contains strange
        # character (and is empty for the rest)
        if started and '2016' in started and completed:
            time_format = '%Y-%m-%d %H:%M:%S.%f'
            started = datetime.datetime.strptime(started, time_format)
            completed = datetime.datetime.strptime(completed, time_format)

            task = {}
            task['started'] = started
            task['completed'] = completed
            task['duration'] = completed - \
                started if completed else None
            task['engine_uuid'] = engine_uuid
            engine_uuids.append(engine_uuid)
            tasks[engine_uuid].append(task)
            del task

    engine_number_map = dict(zip(tasks.keys(), range(len(tasks.keys()))))

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, facecolor='white')

    for engine_uuid, task_list in tasks.iteritems():
        engine_number = engine_number_map[engine_uuid]
        number_list = [engine_number for _ in task_list]
        start_list = [task['started'] for task in task_list]
        completed_list = [task['completed'] for task in task_list]
        ax.plot(
            [number_list, number_list],
            [start_list, completed_list], linewidth=10,
            solid_capstyle="butt")

    ax.set_xlim(min(engine_number_map.values()) -
                1, max(engine_number_map.values()) +
                1)
    ax.set_xlabel('Compute engine number')
    ax.set_ylabel('Compute time')
    plt.show()

if __name__ == '__main__':
    main()
