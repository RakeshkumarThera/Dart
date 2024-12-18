# author: Saif ali Karedia

import datetime
from send_email import send_email_to_person
from get_connection import get_connection_object

NOTIFICATION_DAYS = 3


# merged two scheduler together
# Simple routine to run a query on a database and print the results:
def send_expiry_notification(conn):
    global NOTIFICATION_DAYS
    current_date = datetime.datetime.now()
    print current_date.strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.cursor()

    cur.execute("update cluster_info set email_sent_date = NULL ")    # empty last email sent date everyday
    cur.commit()

    cur.execute(
        "SELECT cluster_id, cluster_name, reserved_by, end_date FROM cluster_info where reserved_by is not null")

    for cluster_id, cluster_name, reserved_by, end_date in cur.fetchall():
        delta = end_date - current_date
        if delta.days == NOTIFICATION_DAYS:
            print cluster_name, reserved_by, end_date, delta.days
            reserved_by_email = reserved_by.replace(" ", ".") + "@teradata.com"
            To = [reserved_by_email]

            Subject = "Cluster Expiration Notification"
            Body = "Hi " + reserved_by + ',\n\nCluster ' + cluster_name + ' reservation will expire on ' + \
                   str(end_date) + ' You have ' + str(NOTIFICATION_DAYS) + ' days of reservation left.\n\n Thank you.'
            send_email_to_person(To, Subject, Body)

myConnection = get_connection_object()
send_expiry_notification(myConnection)
myConnection.close()
