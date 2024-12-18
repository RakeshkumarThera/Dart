#
# Unpublished work.
# Copyright (c) 2016-2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: TestBase Class to establish SSH connection to the system
import random
import base64
import json
import os
import subprocess
import re
import datetime
import time
import tempfile
import signal
import codecs

from os import stat
from Cluster import Cluster
from Dlog import dlog
from lib.ActShellOnQueen import ActShellOnQueen
from lib.Kubernetes import Kubernetes

class AETestBase(object):
    def __init__(self, cfgJson, testParams={}):
        if 'logTimestamp' in testParams:
            self.logTimestamp = testParams['logTimestamp']
        if 'timeScale' in testParams:
            self.timeScale = int(testParams['timeScale'])
        else:
            self.timeScale = 1

        dlog.debug('AETestBase Called!')
        if not testParams:
            testParams = {}
        self.testParams = testParams
        dlog.info('          Using the following Test Parameters:')
        dlog.info('-' * 50)
        for key in self.testParams:
            dlog.info('          %s : %s ' % (key, self.testParams[key]))
        dlog.info('-' * 50)

        self.cfgJson = cfgJson
        self.clusterDict = cfgJson['cluster']
        self.cluster = Cluster(self.cfgJson)
        self.username = self.clusterDict['username']
        self.password = self.clusterDict['password']

        self.buildLoc = None
        self.deployment = None
        self.sparkMaster = None

        if "common" in self.cfgJson:
            commonDict = cfgJson['common']
            if "buildLoc" in commonDict:
                self.buildLoc = commonDict['buildLoc']

        if "deployment" in self.clusterDict:
            self.deployment = self.clusterDict['deployment']

        if "sparkMaster" in self.clusterDict:
            self.sparkMaster = self.clusterDict['sparkMaster']
        if "sparkWorkers" in self.clusterDict:
            self.sparkWorkers = self.clusterDict['sparkWorkers']
        if "sparkManager" in self.clusterDict:
            self.sparkManager = self.clusterDict['sparkManager']
        if "sparkthriftserver" in self.clusterDict:
            self.sparkthriftserver = self.clusterDict['sparkthriftserver']

        self.kubeInstance = Kubernetes(self.cfgJson)

    def getPodName(self, namespace='sparknamespace', podtype='sparkapp-manager'):
        """
        returns a list of podNames for the specified podtype
        """
        cmd = 'kubectl get pods -n %s |grep %s' % (namespace, podtype)
        stdout, stderr, status = self.kubeInstance.execKubeMaster(cmd)
        podList = []
        for line in stdout.splitlines():
            podName = line.split()[0]
            podList.append(podName)
        return podList

    def sparkManagerContainerExecCommand(self, commandStr, namespace='sparknamespace', timeout=60):
        """
        Execute a command on queenDb container
        """
        timeoutValue = timeout * self.timeScale
        sparkManager = self.getPodName(namespace)[0]
        dlog.info("Executing command on the spark-manager %s" %  sparkManager)

        cmdstr = 'kubectl -n %s exec  %s -- %s ' % (namespace, sparkManager, commandStr)

        stdout, stderr, status = self.kubeInstance.execKubeMaster(cmdstr, timeout=timeout)

        return stdout, stderr, status

    def execCmdLocal(self, cmd):
        '''
        Run command locally on the DartRunner machine/workstation
        '''
        # TODO: Add timeout to command
        dlog.info("Executing local command: %s" % cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)

        stdout, stderr = proc.communicate()
        status = proc.poll()

        if status != 0:
            dlog.error("Failed to execute command %s" % cmd)
        return status, stdout, stderr