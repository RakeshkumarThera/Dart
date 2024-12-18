#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: Dart wrapper!

import argparse
import os
import sys
import time
import json
import threading
import importlib
import Queue
import getopt
import ast
import logging
import traceback
import signal
import getpass
from pprint import pprint


# This code is not required if PYTHONPATH is set as an ENV variable
libPath = os.path.abspath(os.path.dirname(__file__)) + '/lib'
if libPath not in sys.path:
    sys.path.insert(0, libPath)
libPath = os.path.abspath(os.path.dirname(__file__)) + '/testsrc'
if libPath not in sys.path:
    sys.path.insert(0, libPath)

from SshConnect import SshConnect
from Dlog import dlog
from DartDBConnect import DartDBConnect
from DartUtility import DartUtility
from collections import OrderedDict
import datetime


DB_HOST = DartUtility.getDbHost()
DB_NAME = DartUtility.getDbName()


class Dart(object):

    def __init__(self, configFile, testFile, uploadTL = False, checkHealth = False, loadDatabase = True, timeScale = 1, dartRunner=False):
        '''
        The Dart test framework will read a config file as input file ...
        '''
        '''
        Setup Logging
        '''
        self.idList = set()
        self.checkHealth = checkHealth
        self.canContinueTest = True
        self.loadDatabase = loadDatabase
        self.timeScale = timeScale
        self.uploadTL = uploadTL
        self.localTest = False

        signal.signal(signal.SIGTERM, self.signalTermHandler)
        signal.signal(signal.SIGINT, self.signalTermHandler)

        self.dartRunner = dartRunner
        
        if self.dartRunner:
            test = testFile[testFile.keys()[0]][0]
            if 'LOCAL' in test:
                if test['LOCAL'] == 'True':
                    self.localTest = True

        if self.dartRunner and self.uploadTL:
            test = testFile[testFile.keys()[0]][0]
            if 'projectName' not in test or 'buildName' not in test or \
                        'tester' not in test:
                dlog.error('testProject, buildName, tester are required values for uploading to Testlink!')
                raise Exception('testProject, buildName, tester are required values for uploading to Testlink!')
            
        if self.loadDatabase:
            if not self.checkHealth and self.dartRunner:
                self.idList.add(testFile[testFile.keys()[0]][0]['id'])

        try:
            self.timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
            logDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log")

            try:
                if not os.path.exists(logDir):
                    os.makedirs(logDir)
            except OSError, e:
                if e.errno != 17:
                    dlog.error(e)
                    dlog.error('Exiting Program!')
                    traceback.print_exc()
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    self.canContinueTest = False
                    raise

            fh, ch = self.setLogInformation(logDir)
            dlog.info("Logfile is %s" % self.logFile)
        
            libPath = os.path.abspath(os.path.dirname(__file__))
            self.testSuite = {};
            self.testSuiteUnOrdered = {};
            self.testSuiteResults = OrderedDict({});
            self.testSuiteRunTime = {};
            configFileAbs = libPath + '/config/' + configFile
            localFileAbs = libPath + '/config/' + 'local.cfg'

            self.startRunTime = time.time()
            self.startTimeStamp = datetime.datetime.fromtimestamp(self.startRunTime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception, e:
            dlog.error(e)
            dlog.error('Exiting Program as Dart was not able to create a logfile!')
            traceback.print_exc()
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise
        finally:
            if not self.canContinueTest and self.loadDatabase:
                if not self.checkHealth and self.dartRunner:
                    testId = testFile[testFile.keys()[0]][0]['id']
                    handler = DartDBConnect(DB_HOST, DB_NAME)
                    updateData = {'status': 'SKIP'}
                    (msg, isSuccessful) = handler.updateRow("darttest", updateData, "id=%s" % testId)
                    if not isSuccessful:
                        dlog.info("Updating status to SKIP failed for %s" % testId)

        try:
            self.localJson = {}
            if os.path.isfile(localFileAbs):
                with open(localFileAbs, 'r' ) as localF:
                    self.localJson = json.load(localF)
                    
            if not self.localTest: 
                tempConfigFile = os.path.join('/tmp', configFile)
                fileT = open(tempConfigFile, 'w')
                with open(configFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
                 
                with open(tempConfigFile, 'r') as f:
                    self.cfgJson = json.load(f)

                    # If its a kubernetes cluster, get the queenNode and workerNode of Running cluster
                    # If no running pods assumes its a fresh kubernetes install(no aster yet)
                    if 'kubeCluster' in self.cfgJson:
                        self.kubemasters = self.cfgJson["kubeCluster"]["kubemaster"]
                        self.updateCfgJson()

                    self.cluster = self.cfgJson['cluster']
        
                if uploadTL:
                    self.testlinkInfo = self.cluster
                    if not self.dartRunner and (( 'testProject' not in self.testlinkInfo) or \
                        ('buildName' not in self.testlinkInfo ) or \
                        ('tester' not in self.testlinkInfo )):
                        dlog.error('testProject, buildName, tester are required values!')
                        dlog.error('Update CFG file or disable TestLink Update option!')
                        raise Exception('testProject, buildName, tester are required values!')
            
            else:
                self.cfgJson = {'cluster' : {'name' : 'local'}}
                self.cluster = self.cfgJson['cluster']
            
            for key in self.localJson:
                self.cfgJson[key] = self.localJson[key]
       
            if 'name' in self.cluster:
                self.clusterName = self.cluster['name']
            else:
                self.clusterName = configFile[:-4]
        
            if not isinstance(testFile, dict):
                testFileAbs = libPath + '/testset/' + testFile

            if isinstance(testFile, dict):
                suite = []
                tests = {}
                for testSet in testFile:
                    suite.append(dict(testFile[testSet][0]))
                    tests[testSet] = suite
                self.testSuiteUnOrdered = tests
                self.testSuite = testFile
            elif os.path.isfile(testFileAbs):
                tempTestFile = os.path.join('/tmp', testFile)
                fileT = open(tempTestFile, 'w')
                with open(testFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
                with open(tempTestFile, 'r') as f:
                    self.testSuite = json.load(f, object_pairs_hook=OrderedDict)
                with open(tempTestFile, 'r') as f:
                    self.testSuiteUnOrdered = json.load(f)
            else:
                self.testSuiteUnOrdered = json.loads(testFile)
                self.testSuite = json.loads(testFile, object_pairs_hook=OrderedDict)
        except ValueError as e:
            traceback.print_exc()
            dlog.error('The Json File may have syntax issues! Check the config file!')
            dlog.error(e)
            dlog.error('Exiting Program!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise
        except Exception as e:
            traceback.print_exc()
            dlog.error(e)
            dlog.error('The test raised an Unexpected Exception while reading the Input Files!!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise
        finally:
            if not self.canContinueTest and self.loadDatabase:
                if not self.checkHealth and self.dartRunner:
                    testId = testFile[testFile.keys()[0]][0]['id']
                    handler = DartDBConnect(DB_HOST, DB_NAME)
                    updateData = {'status': 'SKIP'}
                    (msg, isSuccessful) = handler.updateRow("darttest", updateData, "id=%s" % testId)
                    if not isSuccessful:
                        dlog.info("Updating status to SKIP failed for %s" % testId)

        self.dartTests = OrderedDict({})
        self.runId = ""
        if not self.checkHealth and not self.dartRunner:
            metadata = self.__getMetadata(self.cfgJson)
            if self.loadDatabase:
                metadata['run_id'] = DartUtility.generateRunId()
                self.runId = metadata['run_id']
                self.inserRunInfo(self.runId, self.startTimeStamp, metadata)

        if not self.checkHealth and not self.dartRunner:
            self.defaultTestDict = {}
            for testSet in self.testSuite:
                tests = self.testSuite[testSet]
                defaultTests = []
                for test in tests:
                    if 'TEMPLATE' in test:
                        if test['TEMPLATE'] == 'True':
                            defaultTests.append(test)
                self.defaultTestDict[testSet] = defaultTests

            # Update the missing test Fields with the Default Values
            for testSet in self.testSuite:
                tests = self.testSuite[testSet]
                newTests = []
                defaultTests = self.defaultTestDict[testSet]
                if defaultTests:
                    defaultTest = defaultTests[0]
                    for test in tests:
                        if 'TEMPLATE' in test:
                            if test['TEMPLATE'] == 'True':
                                continue
                        for key in defaultTest:
                            if (key not in test) and (key != 'NAME'):
                                test[key] = defaultTest[key]
                        newTests.append(test)
                    self.testSuite[testSet] = newTests

            self.testSuiteUnOrdered = dict(self.testSuite)

        for testSet in self.testSuite:
            dlog.info ('Test Set: %s ' % testSet)
            dartTestSet = []
            testSeq = 1
            for test in self.testSuiteUnOrdered[testSet]:
                testName = test['NAME']

                if not self.checkHealth and self.loadDatabase:
                    testMeta = self.__getTestMetadata(test)
                    if not self.dartRunner:
                        testMeta['testset'] = testSet
                        testMeta['test_params'] = json.dumps(test)
                        testMeta['test_seq'] = testSeq
                        testId = self.__insertMetadataToDatabase(metadata, testMeta)
                        testSeq = testSeq + 1
                    else:
                        testId = testFile[testFile.keys()[0]][0]['id']
                else:
                    testId = 0

                self.idList.add(testId)
                dartTestSet.append([testName, test, testId])

            self.dartTests[testSet] = dartTestSet

        for testset in self.dartTests:
            dlog.info('Running Testset: %s' % testset)
            tests = self.dartTests[testset]
            self.testSuiteResults[testset] = []
                
            testsetStartTime = time.time()
            for test in tests:
                dlog.info('        Running Test: %s on Cluster %s' % (test[0], configFile[:-4]))
                try:
                    self.runTest(testset, test[0], test[1], test[2])
                except Exception as e:
                    traceback.print_exc()
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    dlog.info('Continuing with the remaining tests!')
            testsetEndTime = time.time()
            testsetTotalTime = int(testsetEndTime - testsetStartTime)
            self.testSuiteRunTime[testset] = testsetTotalTime
            dlog.info ('Test Set : %s Total Execution Time: %d ' % (testset,testsetTotalTime))

        print('')
        print('')
        print('-'*60),
        print('FINAL RESULTS'),
        print('-'*60)
        print('-'*135)
        print('%20s%40s%10s%25s%25s%15s' % ('TESTSET', ' TESTNAME', ' STATUS','START TIME', 'END TIME', 'TIME (secs)'))
        self.totalExecTime = 0
        for testset in self.dartTests:
            testsetResults = self.testSuiteResults[testset]
            if len(testsetResults) == 0:
                continue
            for test in testsetResults:
                if test[2]:
                    testStatus = 'PASSED'
                else:
                    testStatus = 'FAILED'
                startTimeStr = test[3]
                endTimeStr = test[4]
                timeTaken = test[1]
                testName = test[0]
                print('%20s%40s%10s%25s%25s%15s' % (testset, testName, testStatus,startTimeStr, endTimeStr,timeTaken))
            testsetTotalTime = self.testSuiteRunTime[testset]
            self.totalExecTime = self.totalExecTime + int(testsetTotalTime)     
            print('%20s%115s'% ('Total Time:',testsetTotalTime))
            print('-'*135)
        print('%20s%115d' % ('Dart Execution Time:', self.totalExecTime))
        print('-'*135)
        print('-'*135)
        # Remove the logging handlers to avoid propagation
        if ch:
            dlog.removeHandler(ch)
        if fh:
            dlog.removeHandler(fh)

        if not self.checkHealth and self.loadDatabase:
            if not self.dartRunner:
                endRunTime = time.time()
                duration = endRunTime - self.startRunTime
                endTimeStamp = datetime.datetime.fromtimestamp(endRunTime).strftime('%Y-%m-%d %H:%M:%S')
                self.updateRunInfo(self.runId, endTimeStamp, duration)

    def updateCfgJson(self):
        """
        Update cfgjson with the queen and workernode values from kubernetes cluster if its up and running
        """
        username = self.cfgJson["kubeCluster"]["username"]
        password = self.cfgJson["kubeCluster"]["password"]
        domainName = self.cfgJson["kubeCluster"]['domain']

        kubemaster = self.kubemasters[0]
        if '.' not in kubemaster:
            if domainName is None:
                dlog.error("Cannot proceed without domainName")
                raise
            kubemaster = kubemaster + '.' + domainName
        kubeMasterCon = SshConnect(kubemaster, username, password)
        kubeMasterCon.connect()
        queenNodes = []
        workerNodes = []
        commandStr = 'kubectl get pods --namespace=cloud-aster'
        stdout, stderr, status = kubeMasterCon.execCommand(commandStr, timeout=30)
        dlog.info(stdout)
        if (not stdout) or ('kubectl: command not found' in stdout) :
            dlog.info("No Aster cluster installed on this cluster. Cannot update cfgjson for Aster")
        else:
            for line in stdout.splitlines():
                if ('NAME' in line) or (line is None):
                    continue
                podname = line.split()[0]
                dlog.info(podname)
                if 'consul' in podname:
                    continue
                cmdstr = 'kubectl get -o template po %s --namespace=cloud-aster --template={{.spec.nodeName}}' % podname
                dlog.info(cmdstr)
                stdout, stderr, status = kubeMasterCon.execCommand(cmdstr, timeout=30)
                dlog.info(stdout)
                if stdout is not None:
                    nodeName = stdout.splitlines()[0]
                    if '.' not in nodeName:
                        nodeName = stdout.splitlines()[0] + '.' + domainName
                    if 'queen' in podname:
                        queenNodes.append(nodeName)
                    else:
                        workerNodes.append(nodeName)
        self.cfgJson["cluster"]["queenNodes"] = queenNodes
        self.cfgJson["cluster"]["workerNodes"] = workerNodes

    def setLogInformation(self, logDir):
        self.logFile = os.path.join(logDir, "Dart-" + self.timeStamp + '.log')
        formatter = logging.Formatter('%(levelname)s: %(asctime)s:%(filename)s:%(lineno)s: %(message)s')

        fh = logging.FileHandler(self.logFile)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        dlog.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        if not self.dartRunner:
            dlog.addHandler(ch)

        return fh, ch


    def inserRunInfo(self, runId, startTimeStamp, clusterMeta):
        try:
            handler = DartDBConnect(DB_HOST, DB_NAME)
            meta = {"run_id": runId, "start_time": startTimeStamp, "release_name": clusterMeta['release_name'],
                "tester": clusterMeta['tester']}
            res = handler.insertRow("dartruninfo", meta)

            print('Done inserting the information of run %s' % runId)
            if res[1]:
                return res[0]
            return 0
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())


    def updateRunInfo(self, runId, runEndTimeStr, duration):
        try:
            handler = DartDBConnect(DB_HOST, DB_NAME)
            meta = {"end_time": runEndTimeStr, "duration": DartUtility.intToTimeFormat(duration)}
            (msg, isSuccessful) = handler.updateRow("dartruninfo", meta, "run_id='%s'" %runId)
            if not isSuccessful:
                print("Updating status to SKIP fail for run ID %s" % runId)
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())

    def signalTermHandler(self, signal, frame):
        handler = DartDBConnect(DB_HOST, DB_NAME)
        for testId in self.idList:
            handler.updateRow("darttest", {"status": "ABORT"}, "id=%s" % testId)

        endRunTime = time.time()
        duration = endRunTime - self.startRunTime
        endTimeStamp = datetime.datetime.fromtimestamp(endRunTime).strftime('%Y-%m-%d %H:%M:%S')
        self.updateRunInfo(self.runId, endTimeStamp, duration)

        sys.exit(1)


    def __getMetadata(self, cfgJson):
        info = {}
        try:
            cluster = cfgJson['cluster']
            if 'name' in cluster:
                info['cluster_name'] = cluster['name']
            else:
                if '.' in cluster['queenNodes'][0]:
                    dlog.error("You need to put the Cluster Name in config")
                    raise Exception("You need to put the Cluster Name in config")
                info['cluster_name'] = cluster['queenNodes'][0]

            info['cluster_type'] = cluster['clusterType']
            info['queen_nodes'] = ','.join(cluster['queenNodes'])
            info['worker_nodes'] = ','.join(cluster['workerNodes'])
            info['number_of_workers'] = len(cluster['workerNodes'])
            if 'loaderNodes' in cluster:
                info['loader_nodes'] = ','.join(cluster['loaderNodes'])
            info['cluster_info'] = info['cluster_name'] + ":" + info['queen_nodes'] + ":" + info['worker_nodes']
            if 'loader_nodes' in info:
                info['cluster_info'] = info['cluster_info'] + ":" + info['loader_nodes']

            if 'buildName' in cluster:
                info['build_name'] = cluster['buildName']
            else:
                info['build_name'] = "Private"

            if 'tester' in cluster:
                info['tester'] = cluster['tester']
            else:
                info['tester'] = getpass.getuser()

            info['platform_type'] = cluster['clusterType']

            if 'testProject' in cluster:
                info['release_name'] = cluster['testProject']
            else:
                info['release_name'] = "Private"

            if 'username' not in cluster:
                raise KeyError

            if 'buildNumber' in cluster:
                info['build_number'] = cluster['buildNumber']
            else:
                info['build_number'] = ""

            if 'branchName' in cluster:
                info['branch'] = cluster['branchName']
            else:
                info['branch'] = ""

            if 'kubeCluster' in cfgJson:
                kubeCluster = cfgJson['kubeCluster']
                info['kube_master'] = ','.join(kubeCluster['kubemaster'])
                info['kube_nodes'] = ','.join(kubeCluster['kubenodes'])

        except KeyError as e:
            print "KeyError: %s. Please check the config" %str(e)
            dlog.error("KeyError: %s. Please check the config" %str(e))
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            raise Exception("KeyError: %s. Please check the config" %str(e))

        return info


    def __getTestMetadata(self, testInfo):
        testMeta = {}

        try:
            testMeta['testcase'] = testInfo['NAME']
            if 'LOCATION' in testInfo:
                testMeta['testcase_loc'] = testInfo['LOCATION']
            if 'creator' in testInfo:
                testMeta['creator'] = testInfo['CREATOR']
            testMeta['owner'] = testInfo['OWNER']
            testMeta['test_category'] = testInfo['CATEGORY']
            testMeta['test_component'] = testInfo['COMPONENT']
            if 'feature' in testInfo:
                testMeta['test_feature'] = testInfo['FEATURE']
            testMeta['priority'] = testInfo.get('PRIORITY', 3)
            testMeta['status'] = 'WAITING'
            testMeta['timeout'] = testInfo['TIMEOUT']
            if 'TYPE' in testInfo:
                testMeta['type'] = testInfo['TYPE']
        except KeyError as e:
            print "KeyError: %s. Please check the config" % str(e)
            dlog.error("KeyError: %s. Please check the config" % str(e))
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            raise Exception("KeyError: %s. Please check the config" % str(e))

        return testMeta


    def __insertMetadataToDatabase(self, metadata, testMeta):
        try:
            testMeta.update(metadata)

            handler = DartDBConnect(DB_HOST, DB_NAME)
            res = handler.insertRow("darttest", testMeta)

            if res[1]:
                return res[0]

            print "Database access fail."
            dlog.error("Database access fail.")
            raise Exception("Database access fail.")
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            
            

    def __getRemainingMeta(self, releaseName, branchName):
        info = {}
        info['db_type'] = "Unknown"
        info['db_version'] = "Aster"
        info['build_info'] = ""

        try:
            info['build_info'] = self.getBuildInfo()
            if info['build_info'] is None:
                info['build_info'] = ""

            if branchName.lower() == "docker":
                info['db_type'] = "Docker"
                info['db_version'] = "Docker"
            else:
                info['db_type'] = "Hadoop"
                info['db_version'] = self.getHadoopVersion()
                if info['db_version'] == None:
                    dlog.info("The cluster is without Hadoop, change db_version to Aster")
                    info['db_type'] = "Classic"
                    info['db_version'] = "Aster"

            return info
        
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())

            return info


    def runTest(self, testsetName, testName, testParam, testId):
        try:
            totalTime = 0
            result = False
            startTime = None
            endTime = None
            th = None
            testLogFile = ''

            if 'TYPE' in testParam and testParam['TYPE'].lower().strip() != 'setup' \
                    and testParam['TYPE'].lower().strip() != 'teardown':
                logNameShort = testName
                filePath = testParam['COMPONENT']
                if testParam['TYPE'] == 'SQL':
                    #pathList = testParam['QUERY'].split("/")[1:-1]
                    #filePath = "/".join(pathList)
                    testNameShort = "SqlRun"
                elif testParam['TYPE'] == 'SQLMR':
                    testNameShort = "SqlMR"
                elif testParam['TYPE'] == 'CLI':
                    testNameShort = "Cli"
                elif testParam['TYPE'] == 'SQLH':
                    testNameShort = "SqlH"
                elif testParam['TYPE'] == 'AsterR':
                    testNameShort = "AsterR"
                elif testParam['TYPE'] == 'ASTERTOSPARK':
                    testNameShort = "AsterToSpark"
                elif testParam['TYPE'] == 'TDBTQ':
                    testNameShort = "TDBTQ"
                elif testParam['TYPE'] == 'PYTEST':
                    testNameShort = "Pytest"
                else:
                    dlog.info('The Test TYPE is UNDEFINED! Check the input parameter!')
                    raise
            else:
                testModuleFolder = ''
                items = testParam['LOCATION'].split('/')
                for item in items[:-1]:
                    testModuleFolder = testModuleFolder + '/' + item
                libPath = os.path.abspath(os.path.dirname(__file__)) + '/testsrc' + testModuleFolder
                if libPath not in sys.path:
                    sys.path.append(libPath)
                testNameShort = testParam['LOCATION'].split('/')[-1]
                pathList = testParam['LOCATION'].split("/")[:-1]
                filePath = "/".join(pathList)
                logNameShort = testNameShort
                
            startTime = time.time()
            startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
            logTimestamp = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d-%H%M%S')
            testLogShortName = self.clusterName + "_" + logNameShort + "_" + logTimestamp + '.log'
            testLogFile = os.path.abspath(os.path.dirname(__file__)) + "/log/" + filePath + '/' + testLogShortName
            testParam['logTimestamp'] = logTimestamp
            testParam['logPath'] = os.path.abspath(os.path.dirname(__file__))
            testParam['filePath'] = filePath

            if 'timeScale' not in testParam:
                testParam['timeScale'] = self.timeScale

            testLogDir = os.path.abspath(os.path.dirname(__file__)) + "/log/" + filePath
            try:
                if not os.path.isdir(testLogDir):
                    os.makedirs(testLogDir)
            except OSError, e:
                if e.errno != 17:
                    dlog.error(e)
                    dlog.error('Exiting Program!')
                    dlog.error(sys.exc_info())
                    dlog.error(traceback.format_exc(sys.exc_info()[2]))
                    traceback.print_exc()
                    self.canContinueTest = False
                    raise

            # Setup Test Logging
            th = logging.FileHandler(testLogFile)
            th.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s: %(asctime)s:%(filename)s:%(lineno)s: %(message)s')
            th.setFormatter(formatter)
            dlog.addHandler(th)

            testProject = ""
            branchName = ""
            if not self.checkHealth and self.loadDatabase:
                try:
                    handler = DartDBConnect(DB_HOST, DB_NAME)
                    if 'projectName' in testParam:
                        testProject = testParam['projectName']
                    elif 'testProject' in self.cfgJson['cluster']:
                        testProject = self.cfgJson['cluster']['testProject']

                    if 'branchName' in testParam:
                        branchName = testParam['branchName']
                    elif 'branchName' in self.cfgJson['cluster']:
                        branchName = self.cfgJson['cluster']['branchName']

                    meta = None
                    if not self.localTest:
                        meta = self.__getRemainingMeta(testProject, branchName)
                    
                    if meta is None:
                        meta = {}
                    updateData = {'status': 'RUNNING', 'start_time': startTimeStr}
                    updateData.update(meta)
                    (msg, isSuccessful) = handler.updateRow("darttest", updateData, "id=%s" % testId)
                    if not isSuccessful:
                        dlog.info("Updating status fail for %s" % testId)
                except Exception as e:
                    dlog.error(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())

            testModule = importlib.import_module(testNameShort)

            dlog.info('-'*50)
            #dlog.info('..................Running Test: %s.......................' % testNameShort)
            test = getattr(testModule, testNameShort)
            
            testInstance = test(self.cfgJson, testParam)
            #testInstance.__init__(self.cluster, testParam)
            result = testInstance.run()


        except ImportError as e:
            dlog.error('The TestName %s is not defined!' % testName)
            dlog.error(e)
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc(sys.exc_info()[2]))
            raise
        except Exception as e:
            dlog.error(e)
            dlog.error('The test raised an Unexpected Exception!')
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc(sys.exc_info()[2]))
            raise
        finally:
            if result:
                dlog.info('The test %s was successful!' % testName)
            else:
                dlog.info('The test %s has FAILED' % testName)
            
            if startTime:
                startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
            else:
                startTime = time.time()
                startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')

            endTime = time.time()
            totalTime = int(endTime - startTime)

            if endTime:
                endTimeStr = datetime.datetime.fromtimestamp(endTime).strftime('%Y-%m-%d %H:%M:%S')
            else:
                endTimeStr = 'UnDefined'

            if result:
                status = "PASS"
            else:
                status = "FAIL"

            if endTimeStr == "UnDefined":
                endTimeStrForDB = ""
            else:
                endTimeStrForDB = endTimeStr

            serverLogPath = "/root/DartLogs/" + testLogShortName
            updateData = {'status': status}
            if os.path.isfile(testLogFile):
                updateData['log_location'] = serverLogPath

            if endTimeStrForDB != "":
                updateData['end_time'] = endTimeStrForDB

            
            updateData['execution_time'] = DartUtility.intToTimeFormat(totalTime)

            info = {}
            if not self.localTest:
                info = self.__getInfoFromCluster()

            updateData.update(info)

            if not self.checkHealth and self.loadDatabase:
                try:
                    # select Jira information for this Testcase
                    if not result:
                        sql = "run_id=(select run_id from dartruninfo where branch='%s' " %branchName
                        sql = sql + "and release_name='%s' and " %testProject
                        sql = sql + "release='%s' and run_id<>'%s' " %(testParam['release'], testParam['runId'])
                        sql = sql + "order by start_time desc limit 1) "
                        sql = sql + "and testcase='%s' order by start_time limit 1;" %testName
                        jiraInfo = handler.selectRows("darttest", "jira_number", sql)

                        if len(jiraInfo) != 0 and jiraInfo[0]['jira_number'] is not None:
                            updateData['jira_number'] = jiraInfo[0]['jira_number']

                    # Update test result to DB
                    (msg, isSuccessful) = handler.updateRow("darttest", updateData, "id=%s" % testId)
                    if not isSuccessful:
                        dlog.info("Updating status fail for %s" %testId)
                except Exception as e:
                    dlog.error(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    
            response = [testName, totalTime, result, startTimeStr, endTimeStr, testLogFile]
            testResults = self.testSuiteResults[testsetName]
            testResults.append(response)
            self.testSuiteResults[testsetName] = testResults
            if self.uploadTL and not testParam['testSet'] == 'Install' and not self.localTest:
                self.uploadTestLink(testsetName, testName, testParam, status, totalTime, startTime)

            if not self.checkHealth and os.path.isfile(testLogFile) and self.loadDatabase:
                try:
                    (msg, isSuccessful) = handler.uploadLogFile(testLogFile, testLogShortName)
                    if not isSuccessful:
                        dlog.info("Upload log to server fail for %s" %testId)
                except Exception as e:
                    dlog.error(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
            if th:
                dlog.removeHandler(th)


    def __getInfoFromCluster(self):
        info = {}
        try:
            kernelVersion, osVersion = self.getKernelAndOSVersion()
            info['kernel_version'] = kernelVersion
            info['os_version'] = osVersion
        except Exception as e:
            dlog.error("Can't get kernel or os information from cluster")

        info['revision'] = self.getRevision()

        return info


    def uploadTestLink(self, testsetName, testName, testParam, status, totalTime, startTime):
        dlog.info('Updating Testlink for %s %s' % (testsetName, testName,))
        try:
            canUpdate = True
            testLinkResults = {}

            testLinkResults['testlinkDB'] = 'testlinkdb'
            testLinkResults['testlinkUser'] = 'testlink'
            testLinkResults['testlinkPass'] = 'testlink'
            testLinkResults['testlinkServer'] = '10.75.10.11'
            testLinkResults['testlinkPort'] = '5432'

            if self.dartRunner and 'testPlan' in testParam:
                testLinkResults['testPlan'] = testParam['testPlan']
            elif 'testPlan' in self.testlinkInfo:
                testLinkResults['testPlan'] = self.testlinkInfo['testPlan']
            else:
                testLinkResults['testPlan'] = self.testlinkInfo['testProject']

            if self.dartRunner:
                testLinkResults['testProject'] = testParam['projectName']
                testLinkResults['buildName'] = testParam['buildName']
                testLinkResults['tester'] = testParam['tester']
            else:
                testLinkResults['testProject'] = self.testlinkInfo['testProject']
                testLinkResults['buildName'] = self.testlinkInfo['buildName']
                testLinkResults['tester'] = self.testlinkInfo['tester']

            if 'testSuiteId' not in testParam:
                dlog.error('testSuiteId is not defined in the testRun File as part of testParams')
                canUpdate = False
            else:
                testLinkResults['testSuiteId'] = testParam['testSuiteId']

            testLinkResults['testCase'] = testName

            if 'tcVersion' not in testParam:
                testLinkResults['tcVersion'] = '1'
            else:
                testLinkResults['tcVersion'] = testParam['tcVersion']

            testLinkResults['status'] = status

            testLinkResults['duration'] = str(totalTime)
            testLinkResults['notes'] = 'Auto-Loaded by Dart'

            # Custom Fields

            name = None
            workerNodes = []
            loaderNodes = []
            queenNodes = []
            clusterInfo = None
            if 'name' in self.cluster:
                name = self.cluster['name']
            if "queenNodes" in self.cluster:
                queenNodes = self.cluster['queenNodes']
            if "workerNodes" in self.cluster:
                workerNodes = self.cluster['workerNodes']
            if "loaderNodes" in self.cluster:
                loaderNodes = self.cluster['loaderNodes']

            if name:
                clusterInfo = name

            if len(queenNodes) > 0:
                clusterInfo = queenNodes[0] + ': ' + str(len(workerNodes)) + ' Workers and ' \
                              + str(len(loaderNodes)) + 'Loaders'
                if name:
                    clusterInfo = name + ' ' + clusterInfo

            if clusterInfo:
                testLinkResults['clusterInfo'] = clusterInfo

            # Get the values from the cluster componentVersion and osVersion
            kernelVersion = None
            osVersion = None
            try:
                kernelVersion, osVersion = self.getKernelAndOSVersion()
            except Exception:
                dlog.info('Unable to get the KernelVersion and osVersion from the Cluster')

            if kernelVersion:
                testLinkResults['kernelVersion'] = kernelVersion
            if osVersion:
                testLinkResults['osVersion'] = osVersion

            try:
                testLinkResults['hadoopType'] = self.getHadoopVersion()
                testLinkResults['buildInfo'] = self.getBuildInfo()
            except Exception:
                dlog.info('Unable to get the HadoopVersion or BuildInfo from the Cluster')
            
            if 'clusterType' in self.testlinkInfo:
                testLinkResults['platformType'] = self.testlinkInfo['clusterType']

            if 'testCategory' in testParam:
                testLinkResults['testCategory'] = testParam['testCategory']

            if 'testComponent' in testParam:
                testLinkResults['testComponent'] = testParam['testComponent']

            executionTimeStamp = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H%M%S')
            testLinkResults['executionTimeStamp'] = executionTimeStamp

            if canUpdate:
                import UploadTestLink
                uploadTestLink = UploadTestLink.UploadTestLink(testLinkResults)
                returnStatus = uploadTestLink.load()
                if returnStatus:
                    dlog.info('Successfully uploaded the test Results for %s %s' % (testsetName, testName,))
                else:
                    dlog.error('The test Results Failed to upload! %s %s' % (testsetName, testName,))
            else:
                dlog.error('The test Results Failed to upload! %s %s' % (testsetName, testName,))
        except Exception:
            dlog.error('The test Results Failed to upload! %s %s' % (testsetName, testName,))
            traceback.print_exc()
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())



    def getKernelAndOSVersion(self):
        dlog.info('Attempting to get the Kernel and os information from the Cluster')
        if "domain" in self.cluster:
            domainName = self.cluster['domain']
        if "queenNodes" in self.cluster:
            queenNodes = self.cluster['queenNodes']

        if "privateKey" in self.cluster:
            privateKey = self.cluster['privateKey']
        else:
            privateKey = None
        username = self.cluster['username']
        password = self.cluster['password']

        queenNode = queenNodes[0]
        if '.' in queenNode:
            queenNodewithDomain = queenNode
        else:
            queenNodewithDomain = queenNode + '.' + domainName
        queenConnect = SshConnect(queenNodewithDomain, username, password, privateKey)
        queenConnect.connect()
        commandStr = 'lsb_release -a'
        stdout, stderr, status = queenConnect.execCommand(commandStr, timeout=30)
        lines = stdout.split('\n')
        kernelVersion = ''
        osVersion = ''
        for line in lines:
            if 'Distributor ID' in line:
                kernelVersion = line.split()[2]
                kernelVersion = kernelVersion.strip()
            if 'Release' in line:
                osVersion = line.split()[1]
                osVersion = kernelVersion + ' ' + osVersion.strip()
                if "SUSE" in osVersion:
                    cmd = "cat /etc/SuSE-release | grep PATCHLEVEL"
                    stdout, stderr, status = queenConnect.execCommand(cmd, timeout=30)
                    spNumber = stdout.split('=')[1].strip()
                    osVersion = osVersion + " SP " + spNumber

        commandStr = 'uname -r'
        stdout, stderr, status = queenConnect.execCommand(commandStr, timeout=30)
        kernelVersion = stdout.strip()

        return kernelVersion, osVersion


    def getBuildInfo(self):
        version = ""
        ncli_cmd = "cat /home/beehive/bin/.build | grep 'BUILD_VERSION'"
        stdout, stderr, status = self.runCommandOnQueen(ncli_cmd)
        if status == 0:
            line = stdout.splitlines()[0]
            version = line.split(" ")[1]

        return version

    def getRevision(self):
        revision = ""
        ncli_cmd = "cat /home/beehive/bin/.build | grep 'BUILD_VERSION'"
        stdout, stderr, status = self.runCommandOnQueen(ncli_cmd)
        if status == 0:
            line = stdout.splitlines()[0]
            revision = line.split("-")[1]

        return revision


    def getHadoopVersion(self):
        hdversion = None
        hd_cmd = "hadoop version"
        stdout, stderr, status = self.runCommandOnQueen(hd_cmd)
        dlog.info("getHadoopVersion stdout = %s" %stdout)
        dlog.info("getHadoopVersion stderr = %s" %stderr)
        dlog.info("getHadoopVersion status = %s" %status)
        if status == 0:
            for line in stdout.splitlines():
                if 'Hadoop' in line:
                    hdversion= line.split()[-1]
                    if 'cdh' not in hdversion:
                        hv = hdversion.split('.')
                        hdversion = '.'.join(hv[:3]) + '-hdp' + '.'.join(hv[-4:])

        dlog.info("hdversion = %s" %hdversion)

        return hdversion

    def runCommandOnQueen(self, cmd):
        stdout = None
        stderr = None
        status = 1
        try:
            if "domain" in self.cluster:
                domainName = self.cluster['domain']
            if "queenNodes" in self.cluster:
                queenNodes = self.cluster['queenNodes']
            if "privateKey" in self.cluster:
                privateKey = self.cluster['privateKey']
            else:
                privateKey = None

            username = self.cluster['username']
            password = self.cluster['password']

            queenNode = queenNodes[0]
            if '.' in queenNode:
                queenNodewithDomain = queenNode
            else:
                queenNodewithDomain = queenNode + '.' + domainName
            queenConnect = SshConnect(queenNodewithDomain, username, password, privateKey)
            queenConnect.connect()
            stdout, stderr, status = queenConnect.execCommand(cmd, timeout=180)

        except Exception:
            dlog.error('Unable to run the command %s' % cmd)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())

        return stdout, stderr, status


    def getResults(self):
        return self.testSuiteResults
        
            
if __name__ == "__main__":


    def printUsage():
        usage = '''
        Dart.py -c configFileName -t testFile
        Usage Examples:
        Dart.py -c configFileName -t '{"AcceptanceTest" : 
            [{"NAME" : "NCLI02", "TYPE" : "CLI", "COMMAND": "ncli",
             "ARG1" : "node", "ARGMIX" : "showversion, info, show", "LOCATION": "/tmp/xxx/aaa",
              "CREATOR": "alen.cheng@teradata.com", "OWNER": "alen.cheng@teradata.com", 
              "CATEGORY": "unittest", "COMPONENT": "cli", "PRIORITY":2,  "TIMEOUT": 10 }]}'
        Dart.py -c tdh140e1.cfg -t sanityTest.tst
        Dart.py -c cdh251.cfg -t BAT.tst -l
        Note: -l is used to load the results into the Web
        Dart.py -c hrh013.cfg -t ACT.tst -u
        Dart.py -h
        Note: -u option is used to upload Test Results into TestLink Test Case Management System. 
        Make sure that your config file and the test run file has all the necessary details for this feature to work!
        '''
        print(usage)

    try:
        parser = argparse.ArgumentParser(description='Dart - Test framework engine')
        parser.add_argument('-c', '--config', required=False, default=None, help='List of Clusters: Example cdh251.cfg')
        parser.add_argument('-t', '--testFile', required=False, default=None, help='TestRunFile which contains the list of tests')
        parser.add_argument('-l', '--loadDB', required=False, default=False, action='store_true',
                            help='Do not load the results to the Database for Reports')
        parser.add_argument('-u', '--uploadTestLink', required=False, default=False, action='store_true',
                            help='Upload test results to TestLink')
        parser.add_argument('--timeoutScale', required=False, default=1,
                            help='This value will increase the timeout value for the entire execution')
        parser.add_argument('--usage', required=False, default=None, action='store_true',
                            help='Show usage of Dart')

        args = parser.parse_args()

        if args.usage:
            printUsage()
            sys.exit(2)

        if not args.config:
            print "Cluster config file is required"
            printUsage()
            sys.exit(2)

        if not args.testFile:
            print "Test Run file is required"
            printUsage()
            sys.exit(2)

        loadDatabase = False
        if args.loadDB:
            loadDatabase = True

        testlinkUpload = False
        if args.uploadTestLink:
            testlinkUpload = True

        darttest = Dart(configFile=args.config, testFile=args.testFile, uploadTL=testlinkUpload, \
                        loadDatabase=loadDatabase, timeScale=args.timeoutScale)
    except Exception as e:
        print sys.exc_info()
        print traceback.format_exc(sys.exc_info()[2])
        print(e)
        printUsage()
        sys.exit(2)
