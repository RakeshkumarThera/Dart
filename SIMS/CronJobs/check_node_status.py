# author: Saif ali Karedia
import subprocess
import datetime
from send_email import send_email_to_person
from get_connection import get_connection_object


# add maintenance flag and filter during querying
def email_helper_on_to_off(reserved_by, cluster_name):
    """To = ['Saifali.karedia@teradata.com']  # admin list
    Subject = 'Node Currently Not Available'
    Body = 'Hi,\n\nCluster ' + cluster_name + ' has one or more node down. Please monitor it.' \
                                              '\n\nBest Regards,\nTeradata SIMS.'

    send_email_to_person(To, Subject, Body) ask boon to get email when user cluster is down"""

    reserved_by_email = reserved_by.replace(" ", ".") + "@teradata.com"
    To = [reserved_by_email]
    Subject = 'Reserved Cluster Node down for owner'
    Body = 'Hi,\n\nCluster ' + cluster_name + ' has one or more node down. Please monitor it.' \
                                              '\n\nBest Regards,\nTeradata SIMS.'
    send_email_to_person(To, Subject, Body)


def check_node_status(conn):
    cur = conn.cursor()
    cur.execute(
        'Select c.cluster_name,c.reserved_by,c.email_sent_date,c.cluster_status,n.node_status,n.node_location,n.node_ip, n.node_id, c.cluster_id, c.policy, c.maintenance_flag '
        'from node_info n  left join cluster_info c '
        'on c.cluster_id = n.cluster_id order by cluster_name')
    rows = cur.fetchall()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_hour = int(current_date.split(" ")[1][0:2])
    current_day = datetime.datetime.now().weekday()
    weekdays = [0, 1, 2, 3, 4]
    weekends = [5, 6]
    # current_date = datetime.datetime.strptime(str(current_date), '%Y-%m-%d %H:%M:%S')
    # print str(current_hour) + " hour----------"
    # print str(current_day) + " day----------"
    filter_list = []
    for cluster_name, reserved_by, email_sent_date, cluster_status, node_status, node_location, node_ip, node_id, cluster_id, policy, maintenance_flag in rows:
        node_ip = str(node_ip)
        prev_node_status = node_status

        if node_ip.find('.') > 0 and len(node_ip.split(".")) == 4 and len(node_ip) == 12:
            print cluster_name, node_ip, policy
            test = subprocess.Popen(["ping", node_ip, "-c", "1"], stdout=subprocess.PIPE)
            output = test.communicate()[0]
            if output.find('100%') > 0:  # node is now offline

                if 'online' == 'online':  # node is now offline from online
                    # print 'online to offline--->' + node_ip
                    cur.execute("update node_info set node_status = 'offline' where node_id=" + str(node_id))
                    if reserved_by is not None and maintenance_flag == 'No':

                        print email_sent_date
                        if email_sent_date is None and cluster_id not in filter_list:
                            filter_list.append(cluster_id)

                            if policy == 'Full-Use':  # and 5 < current_hour < 7 and 17 < current_hour < 19:
                                print 'email will be sent!!!'
                                cur.execute(
                                    "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                                        cluster_id))
                                conn.commit()
                                email_helper_on_to_off(reserved_by, cluster_name)

                            if policy == 'Day-Use' and 7 <= current_hour < 20 and current_day in weekdays:
                                print 'email will be sent!!!'
                                cur.execute(
                                    "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                                        cluster_id))
                                conn.commit()
                                email_helper_on_to_off(reserved_by, cluster_name)

                            if policy == 'Night-use' and ((current_day in [0, 1, 2, 3, 4] and (
                                        19 <= current_hour <= 23 or 0 <= current_hour <= 7)) or (
                                    current_day == 5 and 0 <= current_hour <= 7)):
                                print 'email will be sent!!!'
                                cur.execute(
                                    "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                                        cluster_id))
                                conn.commit()
                                email_helper_on_to_off(reserved_by, cluster_name)

                            if policy == 'Weekend-Use' and (
                                    (current_day == 4 and 19 <= current_hour <= 23) or (current_day == 5) or (
                                    current_day == 6 and current_hour <= 19)):
                                print 'email will be sent!!!'
                                cur.execute(
                                    "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                                        cluster_id))
                                conn.commit()
                                email_helper_on_to_off(reserved_by, cluster_name)

                            if policy == 'Weekday-Use' and (
                                    (current_day == 6 and 19 <= current_hour <= 23) or (current_day in [0, 1, 2, 3]) or (
                                    current_day == 4 and current_hour <= 19)):
                                print 'email will be sent!!!'
                                cur.execute(
                                    "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                                        cluster_id))
                                conn.commit()
                                email_helper_on_to_off(reserved_by, cluster_name)

                        else:
                            print 'Email wont be send'
                    else:
                        print 'status only updated, no changes, not reserved by anyone and maintenance is on so no ' \
                              'email '
            else:
                if prev_node_status == 'offline':
                    cur.execute("update node_info set node_status = 'online' where node_id=" + str(node_id))
                    cur.execute(
                        "update cluster_info set email_sent_date = '" + current_date + "' where cluster_id = " + str(
                            cluster_id))
                    conn.commit()


myConnection = get_connection_object()
check_node_status(myConnection)
myConnection.close()
