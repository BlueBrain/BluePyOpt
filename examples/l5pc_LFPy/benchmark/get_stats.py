
import datetime
from ipyparallel import Client
rc = Client()
# rc.get_result('77cdf201-5925-4199-bdd8-0eae0d833d2a')
# incomplete = rc.db_query({'completed' : None}, keys=['msg_id', 'started'])
completed = rc.db_query(
    {'completed': {'$ne': None}}, keys=['msg_id', 'started', 'completed',
                                        'engine_uuid'])
total_time = datetime.timedelta()
for task in completed:
    # print task['started'], task['completed'] - task['started']
    total_time += task['completed'] - task['started']
print(total_time, total_time / len(completed))
print(len(set(task['engine_uuid'] for task in completed)), len(completed))
