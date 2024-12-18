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
# Version = 1.1
# Removing TestLink Code and other code that is not required

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

from DartUtility import DartUtility
from DartDBConnect import DartDBConnect
DB_HOST = DartUtility.getDbHost()
DB_NAME = DartUtility.getDbName()
from SshConnect import SshConnect
from Dlog import dlog

from collections import OrderedDict
import datetime
from DartExceptions import LogFileCreationError
from DartExceptions import ConfigFileValidationError
from DartExceptions import TestRunFileValidationError
from DartExceptions import UpdateCfgFileValidationError
from DartExceptions import RaisedKillSignalError


class Dart(object):

    def __init__(self, configFile, testFile, timeScale = 1, dartRunner=False, loadDatabase=False):
        '''
        The Dart test framework will read a config file as input file ...
        '''
        '''
        Setup Logging
        '''
        self.idList = set()
        self.canContinueTest = True
        self.timeScale = timeScale
        self.localTest = False

        signal.signal(signal.SIGTERM, self.signalTermHandler)
        signal.signal(signal.SIGINT, self.signalTermHandler)

        self.dartRunner = dartRunner
        self.loadDatabase = loadDatabase
        
        
        # Initialize these for interrupt handling
        self.Gtest = False
        self.GtestLogShortName = False
        self.GtestLogFile = False
        self.GendTimeStr = False
        self.GendTimeStr = False
        self.GtotalTime = False      

    
        self.runId = None
        self.testName = None
        if self.dartRunner:
            test = testFile[testFile.keys()[0]][0]
            if 'LOCAL' in test:
                if test['LOCAL'] == 'True':
                    self.localTest = True
            if 'runId' in test:
                self.runId = test['runId']
            if 'NAME' in test:
                self.testName = test['NAME']

        try:
            self.timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
            self.timeStampSecs = datetime.datetime.fromtimestamp(time.time()).strftime('%H%M%S')
            logDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log")

            try:
                if not os.path.exists(logDir):
                    os.makedirs(logDir)
            except OSError, e:
                if e.errno != 17:
                    dlog.error(e)
                    dlog.error('Unable to create the Log Folder!')
                    traceback.print_exc()
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    self.canContinueTest = False
                    raise LogFileCreationError

            fh, ch = self.setLogInformation(logDir)
            dlog.info("Logfile is %s" % self.logFile)
        
            libPath = os.path.abspath(os.path.dirname(__file__))
            self.testSuite = {}
            self.testSuiteUnOrdered = {}
            self.testSuiteResults = OrderedDict({})
            self.testSuiteRunTime = {}
            configFileAbs = libPath + '/config/' + configFile
            localFileAbs = libPath + '/config/' + 'local.cfg'

            self.startRunTime = time.time()
            self.startTimeStamp = datetime.datetime.fromtimestamp(self.startRunTime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            dlog.error(e)
            dlog.error('Exiting Program as Dart was not able to create a logfile!')
            traceback.print_exc()
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise LogFileCreationError

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
                        if "deployment" in self.cfgJson["cluster"]:
                            deployment = self.cfgJson["cluster"]["deployment"]
                            if deployment.lower() == 'docker':
                                self.cfgJson = self.updateCfgJson(self.cfgJson)
                            if deployment.lower() == 'spark':
                                self.cfgJson = self.updateSparkCluster(self.cfgJson)

                    self.cluster = self.cfgJson['cluster']

            else:
                self.cfgJson = {'cluster' : {'name' : 'local'}}
                self.cluster = self.cfgJson['cluster']
            
            for key in self.localJson:
                self.cfgJson[key] = self.localJson[key]
       
            if 'name' in self.cluster:
                self.clusterName = self.cluster['name']
            else:
                self.clusterName = configFile[:-4]

        except UpdateCfgFileValidationError as e:
            traceback.print_exc()
            dlog.error('Unable to update the Cfg for Kubernetes Env')
            dlog.error(e)
            dlog.error('Exiting Dart Test!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise UpdateCfgFileValidationError
        
        except ValueError as e:
            traceback.print_exc()
            dlog.error('The Json File may have syntax issues! Check the config file!')
            dlog.error(e)
            dlog.error('Exiting Dart Test!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise ConfigFileValidationError
        
        except Exception as e:
            traceback.print_exc()
            dlog.error(e)
            dlog.error('The test raised an Unexpected Exception while reading the Input Files!!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise ConfigFileValidationError

        try:

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
            raise TestRunFileValidationError
        except Exception as e:
            traceback.print_exc()
            dlog.error(e)
            dlog.error('The test raised an Unexpected Exception while reading the Input Files!!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            self.canContinueTest = False
            raise TestRunFileValidationError


        self.dartTests = OrderedDict({})

        if not self.dartRunner:
            metadata = self.__getMetadata(self.cfgJson)
            

        if not self.dartRunner:
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
                    self.Gtest = test
                    dlog.info(test)
                    self.runTest(testset, test[0], test[1], test[2])
                except Exception as e:
                    dlog.error(e)
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

    def kubeExecute(self, commandStr, cfgJson):

        if "privateKey" in cfgJson["cluster"]:
            privateKey = cfgJson['cluster']['privateKey']

        else:
            privateKey = None
        username = cfgJson["kubeCluster"]["username"]
        password = cfgJson["kubeCluster"]["password"]
        domainName = cfgJson["kubeCluster"]['domain']
        kubemaster = self.kubemasters[0]
        if '.' not in kubemaster:
            if domainName is None:
                dlog.error("Cannot proceed without domainName")
                raise UpdateCfgFileValidationError
            kubemaster = kubemaster + '.' + domainName
        kubeMasterCon = SshConnect(kubemaster, username, password, privateKey)
        kubeMasterCon.connect()
        stdout, stderr, status = kubeMasterCon.execCommand(commandStr, timeout=30)
        dlog.info(stdout + stderr)
        return stdout + stderr

    def updateCfgJson(self, cfgJson):
        """
        Update cfgjson with the queen and workernode values from kubernetes cluster if its up and running
        """
        if len(cfgJson["cluster"]["queenNodes"]) > 0 and len(cfgJson["cluster"]["workerNodes"]) > 0:
            dlog.info('The Queen and Worker Nodes are manually entered in the config file!')
            dlog.info('Skipping the Update Cfg Json File!')
            return cfgJson

        domainName = cfgJson["kubeCluster"]['domain']

        commandStr = "kubectl get pods --namespace=cloud-aster"
        queenNodes = []
        workerNodes = []
        stdout = self.kubeExecute(commandStr, cfgJson)
        if (not stdout) or ('kubectl: command not found' in stdout):
            dlog.info("No Aster cluster installed on this cluster. Cannot update cfgjson for Aster")
            dlog.info("#hack:Using kubemaster and kubenodes as queenNode and workerNodes")
            queenNodes = cfgJson["kubeCluster"]["kubemaster"]
            workerNodes = cfgJson["kubeCluster"]["kubenodes"]
        else:
            for line in stdout.splitlines():
                if ('NAME' in line) or (line is None):
                    continue
                podname = line.split()[0]
                dlog.info(podname)
                if 'consul' in podname:
                    continue
                if 'heapster' in podname:
                    continue
                commandStr = 'kubectl get -o template po %s --namespace=cloud-aster --template={{.spec.nodeName}}' % podname
                dlog.info(commandStr)
                stdout = self.kubeExecute(commandStr, cfgJson)
                dlog.info(stdout)
                if stdout is not None:
                    nodeName = stdout.splitlines()[0]
                    dlog.info(nodeName)
                    if cfgJson["cluster"]["clusterType"] == 'AWS':
                        if "awsIpMapping" in cfgJson:
                            if nodeName not in cfgJson["awsIpMapping"]:
                                if '.' in nodeName:
                                    nodeNameWithOutDomain = nodeName.split('.')[0]
                                    dlog.info(nodeNameWithOutDomain)
                                    if nodeNameWithOutDomain in cfgJson["awsIpMapping"]:
                                        nodeName = cfgJson["awsIpMapping"][nodeNameWithOutDomain]
                                        dlog.info(nodeName)
                                    else:
                                        dlog.info(cfgJson)
                                        dlog.info('The awsIpMapping is not found in the cluster Config File!')
                                        dlog.error(
                                            "WARNING! WARNING! Please check the cluster config file for AWS IP/hostname Mapping!!")
                            else:
                                nodeName = cfgJson["awsIpMapping"][nodeName]
                        else:
                            dlog.info(cfgJson)
                            dlog.info('The awsIpMapping is not found in the cluster Config File!')
                            dlog.error(
                                "WARNING! WARNING! Please check the cluster config file for AWS IP/hostname Mapping!!")
                    if '.' not in nodeName:
                        nodeName = nodeName + '.' + domainName
                        dlog.info(nodeName)
                    if 'queen' in podname:
                        queenNodes.append(nodeName)
                    else:
                        workerNodes.append(nodeName)
        cfgJson["cluster"]["queenNodes"] = queenNodes
        cfgJson["cluster"]["workerNodes"] = workerNodes
        dlog.info(queenNodes)
        dlog.info(workerNodes)
        return cfgJson

    def updateSparkCluster(self, cfgJson):
        commandStr = "kubectl get pods -n sparknamespace  -o wide"
        sparkMaster = []
        sparkWorkers = []
        sparkManager = []
        sparkthriftserver = []
        stdout = self.kubeExecute(commandStr, cfgJson)
        for line in stdout.splitlines():
            podName = line.split()[0]
            nodeIp = line.split()[6]
            if 'spark-master' in podName:
                sparkMaster.append(nodeIp)
            if 'spark-thriftserver' in podName:
                sparkthriftserver.append(nodeIp)
            if 'spark-worker' in podName:
                sparkWorkers.append(nodeIp)
            if 'sparkapp-manager' in podName:
                sparkManager.append(nodeIp)

        cfgJson["cluster"]["sparkMaster"] = sparkMaster
        cfgJson["cluster"]["sparkWorkers"] = sparkWorkers
        cfgJson["cluster"]["sparkManager"] = sparkManager
        cfgJson["cluster"]["sparkthriftserver"] = sparkthriftserver

        dlog.info(sparkMaster)
        dlog.info(sparkWorkers)
        dlog.info(sparkManager)
        dlog.info(sparkthriftserver)

        return cfgJson
    
    def setLogInformation(self, logDir):
        if self.dartRunner:
            logfileShortName = "Dart-%s-%s-%s.log"%(self.testName,self.runId,self.timeStampSecs)
            self.logFile = os.path.join(logDir, logfileShortName)
        else:
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


    def signalTermHandler(self, signal, frame):
        
        ## The Test hsa been aborted ###

        endRunTime = time.time()
        duration = endRunTime - self.startRunTime
        endTimeStamp = datetime.datetime.fromtimestamp(endRunTime).strftime('%Y-%m-%d %H:%M:%S')
        
        if not self.dartRunner:
            sys.exit(1)
        else:
            if self.loadDatabase:
                if self.GtestLogShortName:            
                    serverLogPath = "/root/DartLogs/" + self.GtestLogShortName
                    columns = {'status': 'ABORT'}
                
                if self.GtestLogFile and os.path.isfile(self.GtestLogFile):
                    columns['log_location'] = serverLogPath
                        
                columns['execution_time'] = DartUtility.intToTimeFormat(duration)
                
                if self.GendTimeStr:
                    columns['end_time'] = self.GendTimeStr
                else:
                    endTime = time.time()
                    endTimeStr = datetime.datetime.fromtimestamp(endTime).strftime('%Y-%m-%d %H:%M:%S')
                    columns['end_time'] = endTimeStr
                if self.GtotalTime:
                    columns['execution_time'] = DartUtility.intToTimeFormat(self.GtotalTime)
            
                self.updateTest(self.Gtest[1], columns)
                
                if self.GtestLogShortName != '' and os.path.isfile(self.GtestLogFile):
                    self.uploadLogFile(self.GtestLogFile, self.GtestLogShortName)   
                        
            os._exit(1)
            #raise RaisedKillSignalError

    def __getMetadata(self, cfgJson):
        info = {}
        try:
            cluster = cfgJson['cluster']
            if 'name' in cluster:
                info['cluster_name'] = cluster['name']
            else:
                if '.' in cluster['queenNodes'][0]:
                    dlog.error("You need to put the Cluster Name in config")
                    raise ConfigFileValidationError("You need to put the Cluster Name in config")
                info['cluster_name'] = cluster['queenNodes'][0]

            info['cluster_type'] = cluster['clusterType']
            if 'queen_nodes' in cluster:
                info['queen_nodes'] = ','.join(cluster['queenNodes'])
            if 'worker_nodes' in cluster:
                info['worker_nodes'] = ','.join(cluster['workerNodes'])
                info['number_of_workers'] = len(cluster['workerNodes'])
            if 'remoteNode' in cluster:
                info['remote_node'] = cluster['remoteNode'] 
            if 'loaderNodes' in cluster:
                info['loader_nodes'] = ','.join(cluster['loaderNodes'])
            if 'queen_nodes' in cluster:
                info['cluster_info'] = info['cluster_name'] + ":" + info['queen_nodes'] + ":" + info['worker_nodes']
            if 'remote_node' in cluster:
                info['cluster_info'] = info['cluster_name'] + ":" + info['remote_node']
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
                dlog.error('The username is not in the cluster config file!')
                raise KeyError

            if 'buildNumber' in cluster:
                info['build_number'] = cluster['buildNumber']
            else:
                info['build_number'] = ""

            if 'branchName' in cluster:
                info['branch'] = cluster['branchName']
            else:
                info['branch'] = ""

        except KeyError as e:
            print "KeyError: %s. Please check the config" %str(e)
            dlog.error("KeyError: %s. Please check the config" %str(e))
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            raise ConfigFileValidationError("KeyError: %s. Please check the config" %str(e))

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
            dlog.error("KeyError: %s. Please check the config" % str(e))
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            raise TestRunFileValidationError("KeyError: %s. Please check the config" % str(e))
        
        except Exception as e:       
            dlog.error(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            raise TestRunFileValidationError

        return testMeta
            

    def runTest(self, testsetName, testName, testParam, testId):
        try:
            totalTime = 0
            result = False
            startTime = None
            endTime = None
            th = None
            testLogFile = ''
            testLogShortName = ''

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
                elif testParam['TYPE'] == 'TeradataR':
                    testNameShort = "TeradataR"
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

            self.GtestLogShortName = testLogShortName
            self.GtestLogFile = testLogFile
                 
        
            
                
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


            testModule = importlib.import_module(testNameShort)

            dlog.info('-'*50)
            #dlog.info('..................Running Test: %s.......................' % testNameShort)
            test = getattr(testModule, testNameShort)
            
            testInstance = test(self.cfgJson, testParam)
            #testInstance.__init__(self.cluster, testParam)
            result = testInstance.run()
            dlog.info('Running Cleanup of the Test Instance!')
            try:
                testInstance.cleanUp()
            except Exception as e:
                dlog.info('The Cleanup of the test failed!')

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

            endTimeStr = datetime.datetime.fromtimestamp(endTime).strftime('%Y-%m-%d %H:%M:%S')
            self.GendTimeStr = endTimeStr
            self.GtotalTime = totalTime 
                
            response = [testName, totalTime, result, startTimeStr, endTimeStr, testLogFile, testLogShortName]
            testResults = self.testSuiteResults[testsetName]
            testResults.append(response)
            self.testSuiteResults[testsetName] = testResults
            
            
            if th:
                dlog.removeHandler(th)

    def getResults(self):
        return self.testSuiteResults
        
    def updateTest(self, test, columns):
        #Because the Test id is generated by the database insert operation
        try:
            dlog.info('Updating the columns!')
            dlog.info(test)
            dlog.info(columns)
            if 'id' not in test:
                return
            handler = DartDBConnect(DB_HOST, DB_NAME)
            (msg, isSuccessful) = handler.updateRow("darttest", columns, "id=%s" % test['id'])
            if not isSuccessful:
                dlog.info("Update Failed for %s" % test['id'])
            else:
                dlog.info('Updated Status: On test %s' % (test['NAME']))
            dlog.info(columns)
            
        except Exception as e:
            dlog.info('The Database Update Operation for SKIP operation!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            
    def uploadLogFile(self, testLogFile, testLogShortName):
        try:
            handler = DartDBConnect(DB_HOST, DB_NAME)
            (msg, isSuccessful) = handler.uploadLogFile(testLogFile, testLogShortName)
            if not isSuccessful:
                dlog.info("Upload log to server fail for %s" %testLogFile)
            else:
                dlog.info('Successfully uploaded the Dart Test Log: %s' % testLogShortName)
        
        except Exception as e:
            dlog.info('The Database Update Operation for SKIP operation!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())               
            
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
        Dart.py -h
        
        '''
        print(usage)

    try:
        parser = argparse.ArgumentParser(description='Dart - Test framework engine')
        parser.add_argument('-c', '--config', required=False, default=None, help='List of Clusters: Example cdh251.cfg')
        parser.add_argument('-t', '--testFile', required=False, default=None, help='TestRunFile which contains the list of tests')
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


        darttest = Dart(configFile=args.config, testFile=args.testFile, timeScale=args.timeoutScale)
    except Exception as e:
        print sys.exc_info()
        print traceback.format_exc(sys.exc_info()[2])
        print(e)
        printUsage()
        sys.exit(2)
