# author: Saif ali Karedia

import psycopg2
import datetime
import time
# from power_vm import power_node

from send_email import send_email_to_person, send_email_to_queue
from get_connection import get_connection_object

DAY_USE_START_TIME = 7
DAY_USE_END_TIME = 19
NIGHT_USE_START_TIME = 19
NIGHT_USE_END_TIME = 7
WEEKEND_USE_START_TIME = 19
WEEKEND_USE_END_TIME = 19
WEEKDAY_USE_START_TIME = 19
WEEKDAY_USE_END_TIME = 19

ON = 'ON'
OFF = 'OFF'


def powerManagement(conn):

    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_hour = int(current_date.split(" ")[1][0:2])
    current_day = datetime.datetime.now().weekday()
    # if current_hour not in [7,19]:
    #     return
    weekdays = [0, 1, 2, 3, 4]
    weekends = [5, 6]
    # check by using only one dictionary
    day_use_vm_list = {}
    night_use_vm_list = {}
    weekend_use_vm_list = {}
    weekday_use_vm_list = {}
    cur = conn.cursor()
    cur.execute(
        'Select c.cluster_name,c.reserved_by,c.cluster_status,n.node_status, n.node_ip, n.node_id, c.cluster_id, c.policy, n.hostname '
        'from node_info n inner join cluster_info c '
        'on c.cluster_id = n.cluster_id WHERE reserved_by is not NULL order by cluster_name')
    rows = cur.fetchall()

    for cluster_name, reserved_by, cluster_status, node_status, node_ip, node_id, cluster_id, policy, hostname in rows:
        if hostname is not None:
            hostname = str(hostname) # check code here for error
            vm_name = hostname.split(".")[0]
            if policy == 'Day-Use':
                if current_day in weekdays and current_hour == DAY_USE_START_TIME:
                    # update to online node status
                    day_use_vm_list[vm_name] = ON

                if current_day in weekdays and current_hour == DAY_USE_END_TIME:
                    # update to offline node status
                    day_use_vm_list[vm_name] = OFF
         
            if policy == 'Night-Use':
                if current_day in weekdays and current_hour == NIGHT_USE_START_TIME:
                    # update to online node status
                    night_use_vm_list[vm_name] = ON

                if current_day in [1,2,3,4,5] and current_hour == NIGHT_USE_END_TIME:
                    # update to offline node status
                    night_use_vm_list[vm_name] = OFF
                    
            if policy == 'Weekend-Use':
                if current_day == 4 and current_hour == WEEKEND_USE_START_TIME:
                    # update to online node status
                    weekend_use_vm_list[vm_name] = ON

                if current_day == 6 and current_hour == WEEKEND_USE_END_TIME:
                    # update to offline node status
                    weekend_use_vm_list[vm_name] = OFF

            if policy == 'Weekday-Use':
                if current_day == 6 and current_hour == WEEKDAY_USE_START_TIME:
                    # update to online node status
                    weekend_use_vm_list[vm_name] = ON

                if current_day == 4 and current_hour == WEEKDAY_USE_END_TIME:
                    # update to offline node status
                    weekend_use_vm_list[vm_name] = OFF

    print day_use_vm_list
    print night_use_vm_list
    print weekend_use_vm_list


myConnection = get_connection_object()
powerManagement(myConnection)
myConnection.close()
