#
# Unpublished work.
# Copyright (c) 2011-2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: Cluster to establish SSH connection to the system

import paramiko
import traceback
import SshInteract
from Dlog import dlog

class SshConnect(object):

    def __init__(self, hostname, username=None, password=None, privateKey=None):
        self.hostname = hostname
        self.key = None
        self.pem = None

        # Create a new SSH client object
        self.client = paramiko.SSHClient()
        # Set SSH key parameters to auto accept unknown hosts
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if username:
            self.username = username
        if password:
            self.password = password
        if privateKey:
            self.password = None
            if 'CERTIFICATE' in open(privateKey).read():
                self.pem = True
                self.key = paramiko.RSAKey.from_private_key_file(privateKey)
            else:
                self.key = privateKey


    def connect(self):
        if self.pem:
            self.client.connect(hostname=self.hostname, username=self.username, password=self.password, pkey=self.key)
        else:
            self.client.connect(hostname=self.hostname, username=self.username, password=self.password, key_filename=self.key)
    
    def interact(self, timeout=60, buffer_size=1024, display=True ):
        return SshInteract.SshInteract(self.client, timeout=timeout, buffer_size= buffer_size, display=display)

    def execCommand(self, command=None, timeout=60 ):
        if not command:
            raise Exception ('Must provide a command for execCommand!')
        dlog.debug('Executing Command: %s ' % command)
        stdin, stdout, stderr  =  self.client.exec_command(command=command, timeout=timeout)
        return ( stdout.read(), stderr.read(), stdout.channel.recv_exit_status() )

    def execCommandBackground(self, command=None):
        """
        execute a non-blocking command. Do not return anything
        """
        if not command:
            raise Exception('Must provide a command for execCommand!')
        dlog.debug('Executing Command: %s ' % command)
        self.client.exec_command(command=command)

    def close(self):
        self.client.close()


if __name__ == '__main__':

    # Set login credentials and the server prompt
    hostname = '10.80.190.130'
    username = 'root'
    password = 'aster4data'
    prompt = '~]# $'

    # Use SSH client to login
    try:

        queenCon = SshConnect(hostname, username, password)
        queenCon.connect()
        commandStr = 'ls -l'

        print 'running command on hostname %s' % hostname

        stdout, stderr, status = queenCon.execCommand(commandStr)

        print(stdout)
        print(stderr)
        print(status)

        # Create a client interaction class which will interact with the host
        queenInteract = queenCon.interact(display=False)
        # Flush the output to start with a clean plate
        queenInteract.flush()
        
        queenInteract.send('uname -a')
        index, out = queenInteract.expect(prompt)
        print '-'*79
        print(index)
        print(out)
        print '-'*79        
        # Now let's do the same for the ls command
        #interact.flush()
        queenInteract.send('ls -l ')
        index, out = queenInteract.expect(prompt)
        print '-'*79
        print(index)
        print(out)
        print '-'*79
        queenInteract.close()
        queenCon.close()
    except Exception:
        traceback.print_exc()
    finally:
        try:
            queenCon.close()
        except:
            pass
