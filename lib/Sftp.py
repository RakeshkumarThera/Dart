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
# DESCRIPTION: Sftp Class to establish SFtp connection to the system

import paramiko
import os

class Sftp(object):

    def __init__(self, hostname, username=None, password=None, privateKey=None):
        self.port = 22
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.pem = None
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
        else:
            self.key = None
            
    def connect(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        if self.pem:
            self.client.connect(hostname=self.hostname, username=self.username, password=self.password, pkey=self.key)
        else:
            self.client.connect(hostname=self.hostname, username=self.username, password=self.password, key_filename=self.key)    
        self.sftp =self.client.open_sftp()


    def put(self, localFile, remoteFile):
        self.connect()
        self.sftp.put(localFile, remoteFile)
        self.sftp.close()
        self.client.close()

    def get(self, remoteFile, localFile):
        self.connect()
        self.sftp.get(remoteFile, localFile)
        self.sftp.close()
        self.client.close()
 
    def close(self):
        self.sftp.close()
        self.client.close()
