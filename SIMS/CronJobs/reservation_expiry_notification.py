# author: Saif ali Karedia

import psycopg2
import datetime
import time
# from power_vm import power_node
from send_email import send_email_to_person, send_email_to_queue
from get_connection import get_connection_object
from power_vm import power_node


# Simple routine to run a query on a database and print the results:
def send_expiry_notification(conn):
    power_off_cluster = []
    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    current_date = datetime.datetime.strptime(str(current_date), '%Y-%m-%d %H:%M:%S')

    # print current_date
    current_ts = time.mktime(current_date.timetuple())
    cur = conn.cursor()

    cur.execute(
        "SELECT cluster_name, reserved_by, cluster_id, next_person_in_line, end_date, start_date FROM cluster_info "
        "where reserved_by is not null")

    rows = cur.fetchall()

    for cluster_name, reserved_by, cluster_id, next_person_in_line, end_date, start_date in rows:

        # print type(end_date)
        end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(str(end_date),'%Y-%m-%d %H:%M:%S')

        end_ts = time.mktime(end_date.timetuple())

        minutes = (current_ts - end_ts)/60

        if 0 <= minutes < 60:
            print 'all end date less than '+ str(current_date) + ' should expire'
            print cluster_name, reserved_by, end_date, current_date, minutes
            print '\n'
            reserved_by = reserved_by
            next_person_in_line = next_person_in_line
            cur.execute("update cluster_info set policy = NULL, start_date = NULL, "
                        "end_date = NULL, reserved_by = NULL, user_comments = NULL, next_person_in_line = NULL, maintenance_flag='No'"
                        "where cluster_id = "+str(cluster_id))
            power_off_cluster.append(cluster_id)
            conn.commit()

            # power_node([],'OFF')
            reserved_by_email = reserved_by.replace(" ", ".") + "@teradata.com"
            To = [reserved_by_email]

            Subject = "Cluster Expiration Notification"
            Body = "Hi " + reserved_by + ',\n\nCluster ' + cluster_name + ' reservation has expired.\n\nThank you.'
            send_email_to_person(To, Subject, Body)

            if next_person_in_line is not None:
                send_email_to_queue(cluster_id, cluster_name, next_person_in_line)

    return power_off_cluster


def nodes_list_to_power_off(cluster_list, conn):
    power_off_list = {}
    cur = conn.cursor()
    for cluster_id in cluster_list:
        cur.execute(
            "SELECT n.hostname,n.cluster_id FROM cluster_info c inner join node_info n on c.cluster_id = n.cluster_id where n.cluster_id = " + str(
                cluster_id))
        rows = cur.fetchall()
        for hostname in rows:
            hostname = hostname[0]
            if hostname is not None:
                host = hostname.split(".")[0]
                power_off_list[host] = 'OFF'

    return [power_off_list]


myConnection = get_connection_object()
cluster_list_to_power_off = send_expiry_notification(myConnection)
power_off_list_1 = nodes_list_to_power_off(cluster_list_to_power_off,myConnection)
# call power_vm py file to power off the cluster
power_node(power_off_list_1)
myConnection.close()
