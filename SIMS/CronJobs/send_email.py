# author: Saif ali Karedia

import smtplib
EMAIL = False


def send_email_to_person(To, Subject, Body):
    global EMAIL
    if EMAIL:
        server = smtplib.SMTP()
        From = 'saifali.karedia@teradata.com'
        try:
            server = smtplib.SMTP('localhost', 25)
            to = ','.join(To)
            print('Sending mail to ' + to)
            msg = 'From:' + From + '\n' + 'To:' + to + '\n' + 'Subject:' + Subject + '\n\n' + Body
            server.set_debuglevel(1)

            server.sendmail(From, To, msg)

        except Exception as e:

            print e
            print 'error'
        finally:
            server.quit()


def send_email_to_queue(cluster_id, cluster_name, next_person_in_line):
    # queue = session.query(Cluster.next_person_in_line).filter_by(cluster_id=cluster_id).first()
    # next_person_in_line = str(queue[0])
    next_person_in_line = next_person_in_line.split(', ')
    del next_person_in_line[-1]
    next_person_in_line_list = [name.replace(" ", ".") + "@teradata.com" for name in next_person_in_line]
    To = next_person_in_line_list
    Subject = 'Cluster available for reservation '
    Body = 'Hi,\n\nCluster ' + cluster_name + ' is available for reservation. Please reserve it before anyone else ' \
                                              'reserves the cluster.\n\nBest Regards,\nTeradata SIMS.'
    send_email_to_person(To, Subject, Body)
