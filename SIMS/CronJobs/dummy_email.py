# author: Saif ali Karedia
import smtplib
server = smtplib.SMTP()
From = 'ojas.gupta@teradata.com'  # add here the service account.
try:
    print 'sending'
    server = smtplib.SMTP('localhost', 25)  # configure smtp server.
    To = 'ojas.gupta@teradata.com'
    msg = 'From:' + From + '\n' + 'To:' + To + '\n' + 'Subject:' + "You are hacked!!" + '\n\n' + 'I am anonymous. Can you figure who sent this email?? HAHAHA its you!!'
    server.set_debuglevel(1)

    server.sendmail(From, To, msg)  # send_email
    print 'sent!!'

except Exception as e:
    print e
    print 'error'
finally:
    server.quit()