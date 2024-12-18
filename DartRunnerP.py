#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner: alen.cheng@teradata.com
#
# Description: Dart Runner runs a list of tests on a list of Clusters in parallel
# Version 2.3

import ast
import argparse
import json
import os
import sys
import time
import requests
from collections import OrderedDict
import threading
import Queue
import multiprocessing
from Dart import Dart
import traceback
import datetime
import getpass
import subprocess
import signal
from pprint import pprint
from os import walk


# This code is not required if PYTHONPATH is set as an ENV variable
libPath = os.path.abspath(os.path.dirname(__file__)) + '/lib'
sys.path.insert(0, libPath)
libPath = os.path.abspath(os.path.dirname(__file__)) + '/testsrc'
sys.path.insert(0, libPath)

from SshConnect import SshConnect
from Sftp import Sftp
from DartUtility import DartUtility
from DartDBConnect import DartDBConnect
from Dlog import dlog
import logging
from DartFailedTestParser import DartFailedTestParser

DB_HOST = DartUtility.getDbHost()
DB_NAME = DartUtility.getDbName()


class DartRunner(object):

    def __init__(self, metaDict, clusterList , testRunFile, loadDatabase = True):
        """
        @summary: Dart Runner schedules tests in a Queue from a list of available clusters
        """
        self.failedTestOwnerDict = {}
        self.clusterConfigsForDb = {}
        self.runId = ""
        self.retryCount = 0
        self.runCommand = "python " + " ".join(sys.argv)
        print self.runCommand

        # Get the Project Name
        if "noTestLog" in metaDict:
            self.noTestLog = metaDict['noTestLog']
            print(self.noTestLog)
            
            
        self.runStartTime = time.time()

        signal.signal(signal.SIGTERM, self.signalTermHandler)
        signal.signal(signal.SIGINT, self.signalTermHandler)

        #Setup Logger#
        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
        logDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log")

        self.timeStamp = timeStamp
        
        try:
            if not os.path.exists(logDir):
                os.makedirs(logDir)
        except OSError, e:
            if e.errno != 17:
                dlog.error(e)
                dlog.error('Unable to create Log Directory! Exiting Program!')
                traceback.print_exc()
                raise

        self.logFile = os.path.join(logDir, "DartRunner-" + timeStamp + '.log')
        fh = logging.FileHandler(self.logFile)
        fh.setLevel(logging.INFO)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)
        formatter= logging.Formatter('%(levelname)s: %(asctime)s:%(filename)s:%(lineno)s: %(message)s')
        self.ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        dlog.addHandler(self.ch)
        dlog.addHandler(fh)
        dlog.info("Logfile is %s" % self.logFile)
        #End of Logger Setup

        self.absTouchFileName = None
        self.beginTests = False
        self.fileTouched = False
        
        # Get the Project Name
        if "projectName" in metaDict:
            self.projectName = metaDict['projectName']
    
        # Check if the load is Public/Private
        if "load" in metaDict:
            load = metaDict['load']
            if load == 'Public' or load == 'Private':
                self.load = load
            else:
                self.load = 'noLoad'

        # Get the Release Name
        if "releaseName" in metaDict:
            self.releaseName = metaDict['releaseName']
        else:
            self.releaseName = ""
        
        self.releaseName = self.releaseName.upper()
        
        # Get the Keywords
        if "keywords" in metaDict:
            self.keywords = metaDict['keywords']
        else:
            self.keywords = ""    
        
        self.keywords = self.keywords.upper()
        
        # Get the Comments
        if "comments" in metaDict:
            self.comments = metaDict['comments']
        else:
            self.comments = "" 
            
        # Get the Run Label
        if "runLabel" in metaDict:
            self.runLabel = metaDict['runLabel']
        else:
            self.runLabel = ""
            
        
        self.loadDatabase = loadDatabase
        libPath = os.path.abspath(os.path.dirname(__file__))
        self.testSuite = OrderedDict();
        self.checkHealthDict = {}
        self.installTestDict = {}
        self.defaultTimeout = 600
        
        
        
        #Read the cluster Config Files
        self.clusterConfigDict = {}
        # Get the ClusterList
        self.clusterList = clusterList
        dlog.info("clusterList = %s " % clusterList)
        clustersStr = self.clusterList.split(',')
        self.clusters = []
        for clusterName in clustersStr:
            self.clusters.append(clusterName.strip())
            
        print "self.clusters = ", self.clusters
        for cluster in self.clusters:
            dlog.info(cluster)
        self.loadClusterConfigs()
        # Get the MetaDict
        

        # Get the Build Name
        if "buildName" in metaDict:
            self.buildName = metaDict['buildName']
        else:
            self.buildName = 'Private'

        if 'testPlan' in metaDict:
            self.testPlan = metaDict['testPlan']
        else:
            self.testPlan = metaDict['projectName']
        
        # Get the TimeOut Scale
        if "timeScale" in metaDict:
            self.timeScale = metaDict['timeScale']
        else:
            self.timeScale = 1
        
        # Get the Retry Count
        if "retry" in metaDict:
            self.retryCount = int(metaDict['retry'])
        else:
            self.retryCount = 0
        
        # Get the Threshold Percentage
        if "threshold" in metaDict:
            self.threshold = int(metaDict['threshold'])
        else:
            self.threshold = 0
        # Get the Tester from OS
        
        if "tester" in metaDict:
            self.tester = metaDict['tester']
            if not self.tester:
                self.tester = getpass.getuser()
        
        if "branchName" in metaDict:
            self.branchName = metaDict['branchName']
        else:
            self.branchName = ''
         
        
        # Get the Install Test
        self.installTest = None
        if "installTest" in metaDict:
            self.installTest = metaDict['installTest']
        
        # Get the Install Test
        self.checkHealthTest = None
        if "checkHealthTest" in metaDict:
            self.checkHealthTest = metaDict['checkHealthTest']
        
        #Get the testTag parameter
        self.testTags = []
        if 'testTag' in metaDict and metaDict['testTag']:
            tags = metaDict['testTag'].split(',')
            for tag in tags:
                self.testTags.append(tag.strip())
            
        # Get the testRunFile information
        testRunFileList = testRunFile.split(',')
        #Check the testRunFile for any folders and recreate the testRunFile.
        testRunFileListNew = []
        for testFile in testRunFileList:
            runFile = libPath + '/testset/' + testFile.strip()
            dlog.info(runFile)
            if os.path.isdir(runFile):
                testFiles = self.getTestRunFiles(runFile)
                testRunFileListNew.extend(testFiles)
                
            elif os.path.isfile(runFile) and os.stat(runFile).st_size != 0 and '.tst' in runFile:
                testRunFileListNew.append(runFile)
        
        
        for testFile in testRunFileListNew:
            runFile = testFile
            dlog.info('Scanning File: %s ' % runFile)
            if not os.path.isfile(runFile):
                dlog.info('The TestRun File is not present: %s !' % runFile)
                dlog.info('The test raised an Unexpected Exception!')
                raise
            runFileBaseName = os.path.basename(runFile)
            try:
                tempRunFile = os.path.join('/tmp', runFileBaseName)
                fileT = open(tempRunFile, 'w')
                with open(runFile, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
                dlog.info('Reading tempRunFile : %s'%tempRunFile)
                with open(tempRunFile, 'r') as f:
                    runFileOrderedDict = json.load(f, object_pairs_hook=OrderedDict)
                    for testSet in runFileOrderedDict:
                        if testSet in self.testSuite:
                            newTestSet = self.testSuite[testSet]
                        else:
                            newTestSet = []
                        for test in runFileOrderedDict[testSet]:
                            if 'SETUP' in test and test['SETUP'] == 'True':
                                newTestSet.append(test)
                            elif 'TEARDOWN' in test and test['TEARDOWN'] == 'True':
                                newTestSet.append(test)
                            elif 'TEMPLATE' in test and test['TEMPLATE'] == 'True':
                                newTestSet.append(test)
                            elif self.testTags:
                                testMatch = False
                                for tag in self.testTags:
                                    if 'TESTTAG' in test:
                                        localTestTags = test['TESTTAG'].split(',')
                                        for localTag in localTestTags:
                                            if tag == localTag.strip():
                                                testMatch = True
                                                break
                                if testMatch:
                                    newTestSet.append(test)
                            else:
                                newTestSet.append(test)            
                        self.testSuite[testSet] = newTestSet
                        
            except ValueError as e:
                dlog.info('The testrun_file may be not present or have issues. Please fix and rerun!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                dlog.info('Exiting Program!')
                if self.fileTouched and os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
                sys.exit(2)
            except Exception as e:
                dlog.info('The testrun_file may be not present or have issues. Please fix and rerun!')
                dlog.info('The test raised an Unexpected Exception!')
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                dlog.info(e)
                if self.fileTouched and os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
                raise

        if 'rerunFailedTests' in metaDict and metaDict['rerunFailedTests'] is not None \
                   and len(metaDict['rerunFailedTests']) != 0:
            runner = DartFailedTestParser(DB_HOST, DB_NAME)
            self.testSuite = runner.ParseFailedTest(testRunFileListNew, metaDict['rerunFailedTests'])

            print "rerun test that self.testSuite = ", self.testSuite
        
        try:
                
            if self.checkHealthTest:
                checkHealthRunFileAbs = libPath + '/testset/' + self.checkHealthTest
                checkHealthRunFileBaseName = os.path.basename(checkHealthRunFileAbs)
                tempCheckHealthRunFile = os.path.join('/tmp', checkHealthRunFileBaseName )
                fileT = open(tempCheckHealthRunFile, 'w')
                with open(checkHealthRunFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
                    
                with open(tempCheckHealthRunFile, 'r') as f:
                    self.checkHealthDict = json.load(f, object_pairs_hook=OrderedDict)
                    self.printTestSet(self.checkHealthDict)
                        
            if self.installTest:
                installTestRunFileAbs = libPath + '/testset/' + self.installTest
                installTestRunFileBaseName = os.path.basename(installTestRunFileAbs)
                tempInstallTestRunFile = os.path.join('/tmp', installTestRunFileBaseName )
                fileT = open(tempInstallTestRunFile, 'w')
                with open(installTestRunFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
                    
                with open(tempInstallTestRunFile, 'r') as f:
                    self.installTestDict = json.load(f, object_pairs_hook=OrderedDict)
                    dlog.info(self.installTestDict)
                
                    
        except ValueError as e:
            dlog.info('The testrun_file may be not present or have issues. Please fix and rerun!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            dlog.info('Exiting Program!')
            if self.fileTouched and os.path.isfile(self.absTouchFileName):
                os.remove(self.absTouchFileName)
            sys.exit(2)
        except Exception as e:
            dlog.info('The testrun_file may be not present or have issues. Please fix and rerun!')
            dlog.info('The test raised an Unexpected Exception!')
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            dlog.info(e)
            if self.fileTouched and os.path.isfile(self.absTouchFileName):
                os.remove(self.absTouchFileName)
            raise
        
        self.allTrForRpmList = []
        
        self.noDownload = False
        if 'noDownload' in metaDict and metaDict['noDownload']:
            self.noDownload = True
            
        if 'buildUrl' in metaDict and metaDict['buildUrl']:
            bNumber, rNumber = self.parseUrlToGetBuildNumberAndRevision(clusterList, metaDict['buildUrl'])
            if not self.noDownload:
                self.downloadRpm(clusterList,metaDict['buildUrl'] )
            
        # Get the Build Number
        if 'buildUrl' in metaDict and metaDict['buildUrl']:
            self.buildNumber = bNumber
        elif "buildNumber" in metaDict:
            self.buildNumber = metaDict['buildNumber']
        else:
            self.buildNumber = ''
        
        # Get the Revision Number
        if 'buildUrl' in metaDict and metaDict['buildUrl']:
            self.revisionNumber = rNumber
        elif "revisionNumber" in metaDict:
            self.revisionNumber = metaDict['revisionNumber']
        else:
            self.revisionNumber = ''
     
        if 'buildLoc' in metaDict and metaDict['buildLoc']:
            buildLoc = metaDict['buildLoc']
            if not os.path.isdir(buildLoc):
                dlog.error(e)
                dlog.error('The BuildLoc specified is not a directory! Exiting Program!')
                traceback.print_exc()
                raise
            self.transferRpmsToQueen(clusterList, metaDict['buildLoc'])

        self.disableNotify = False
        if 'disableNotify' in metaDict and metaDict['disableNotify']:
            self.disableNotify = True

        #Initialize Cluster States      
        self.clusterState = {}
        for cluster in self.clusters:
            if self.pingCluster(cluster):
                self.clusterState[cluster] = 'free'
            else:
                self.clusterState[cluster] = 'stale'


        #Initialize Cluster Current Assigned Test      
        self.clusterCurrentTest = {}
        for cluster in self.clusters:
            self.clusterCurrentTest[cluster] = None
            

        #Initialize CheckHealthFailCnt = {}
        self.checkHealthFailCnt = {}
        for cluster in self.clusters:
            self.checkHealthFailCnt[cluster] = 0
        
        #Get the Default test for each TestSet
        self.defaultTestDict = {}
        for testSet in self.testSuite:
            tests = self.testSuite[testSet]
            defaultTests = []
            for test in tests:
                if 'TEMPLATE' in test:
                    if test['TEMPLATE'] == 'True':
                        defaultTests.append(test)
            self.defaultTestDict[testSet] = defaultTests

        #Update the missing test Fields with the Default Values
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
            
        self.setupTearDownDict = {}
        for testSet in self.testSuite:
            tests = self.testSuite[testSet]
            setupTests = []
            tearDownTests = []
            for test in tests:
                if 'SETUP' in test: 
                    if test['SETUP'] == "True":
                        setupTests.append(test)
                if 'TEARDOWN' in test: 
                    if test['TEARDOWN'] =="True":
                        tearDownTests.append(test)
            self.setupTearDownDict[testSet] = [setupTests, tearDownTests]

        self.localSetupDict = {}
        self.localTearDownDict = {}
        for testSet in self.testSuite:
            self.localSetupDict[testSet] = False
            self.localTearDownDict[testSet] = False
    
    def main(self):
        #Generate a Unique DartRunner Run Id
        try:
            for cluster in self.clusters:
                clusterCfg = self.clusterConfigDict[cluster]
                meta = self.getClusterMeta(clusterCfg)
                self.clusterConfigsForDb[cluster] = meta
        except Exception as e:
            dlog.info('Some required fields needs to be put in cluster config')
            dlog.info('The test raised an Unexpected Exception!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            if self.fileTouched:
                if os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
            raise

        try:
            self.runId = DartUtility.generateRunId()
        except Exception as e:
            dlog.info('Unable to generate RunID. Database Operation Failed!')
            dlog.info('The test raised an Unexpected Exception!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            if self.fileTouched:
                if os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
            raise
        #Initialize the testCount or testSequence Number 
        testCnt = 1
        queue = multiprocessing.Queue()

        runStartTimeStr = datetime.datetime.fromtimestamp(self.runStartTime).strftime('%Y-%m-%d %H:%M:%S')
        if self.loadDatabase:
            try:
                self.insertRunInfo(self.runId, runStartTimeStr)
            except Exception as e:
                dlog.info('The RunId and Run Information Insert Operation Failed!')
                dlog.info('The test raised an Unexpected Exception!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                if self.fileTouched and os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
                raise
        conns = []
        self.testResults = []
        self.testTimeOutDict = {}
        threadCount = 0
        testExecCount = 0
        canProceed = True
              
        #Initialize the Cluster Setup     
        #Wait till one Install job is complete before start running the tests!
   
        if self.installTest:
            self.installTests = []
            
            test = self.installTestDict['Install'][0]    
            test['runId'] = self.runId
            test['testSet'] = 'Install'
            test['testId'] = testCnt
            test['timeScale'] = self.timeScale

            for cluster in self.clusters:
                testCopid = dict(test)
                testCopid['testId'] = testCnt
                testCnt = testCnt + 1  
                        
                if self.loadDatabase:
                    try:
                        dbId = self.insertMeta(testCopid)
                        if dbId == 0:
                            raise Exception("Database Insert operation fail")
                        testCopid['id'] = dbId
                    except Exception as e:
                        dlog.info('The Database Insert Operation!')
                        dlog.info(e)
                        dlog.error(str(sys.exc_info()))
                        dlog.error(traceback.format_exc())

                    time.sleep(0.5)
                                                   
                self.installTests.append(testCopid)

            installTestCnt = 0
            for cluster in self.clusters:
                #Get the first test Only
                time.sleep(3)
                test = self.installTests[installTestCnt]
                #Get the test NAME value
                if 'NAME' in test:
                    testName = test['NAME']
                else:
                    dlog.info('The Install Test requires a NAME!Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue
                
                #Get the test timeout value
                if 'TIMEOUT' in test:
                    timeout = test['TIMEOUT']
                    testId = test['testId']
                    testTimeOutValues = {'TIMEOUT' : timeout, 'STARTTIME' : None, 'ENDTIME' : None, 'TEST' : test, 'CLUSTER' : cluster }
                    self.testTimeOutDict[testId] = testTimeOutValues
                else:
                    dlog.info('The Install Test requires a timeout! Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue
            
                
                
                #Get the test location or type value
                if 'LOCATION' in test:
                    testLoc = test['LOCATION']
                else:
                    dlog.info('The Install Test requires  a LOCATION! Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue
                
                #Get the test OWNER value
                if 'OWNER' in test:
                    testOwner = test['OWNER']
                else:
                    dlog.info('The Install Test requires an OWNER! Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue
                
                #Get the test OWNER value
                if 'CATEGORY' in test:
                    testCategory = test['CATEGORY']
                else:
                    dlog.info('The Install Test requires a CATEGORY! Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue
                #Get the test COMPONENT value
                if 'COMPONENT' in test:
                    testComponent = test['COMPONENT']
                else:
                    dlog.info('The Install Test requires a COMPONENT!Skipping the Install Test!')
                    dlog.info('Cannot use this cluster! Marking the cluster: %s as stale!' % cluster)
                    self.clusterState[cluster] = 'stale'
                    dlog.info(test)
                    continue

                self.clusterState[cluster] = 'install'
                self.clusterCurrentTest[cluster] = test['NAME']
                threadCount = threadCount + 1
                testId = test['testId']
                testTimeOutValues =   self.testTimeOutDict[testId]
                startTime = int(time.time())
                testTimeOutValues['STARTTIME'] = startTime 
                testTimeOutValues['CLUSTER'] = cluster
                dlog.info('\nRunning Install Test: %s on Cluster: %s Thread Count: %d  \n' % (test['NAME'], cluster, threadCount))
                #testThread = threading.Thread(target=self.runTest, args=(testName, test, cluster, queue, timeout))
                testThread = multiprocessing.Process(target=self.runTest, args=(testName, test, cluster, queue, timeout))
                testThread.daemon = False
                testThread.start()
                conns.append(testThread)
                testTimeOutValues['THREAD'] = testThread
                self.testTimeOutDict[testId] = testTimeOutValues

                installTestCnt = installTestCnt + 1
        
        self.allTests = []
        self.testStatus = {}
        self.testSets = []
        self.realTestsPerTestSet = {}
        self.testRetryCountDict = {}
        for testSet in self.testSuite:
            tests = self.testSuite[testSet]
            self.testSets.append(testSet)
            realTests = []
            for test in tests:
                test['runId'] = self.runId
                test['testSet'] = testSet
                test['testId'] = testCnt
                test['timeScale'] = self.timeScale
                test['projectName'] = self.projectName
                test['testPlan'] = self.testPlan
                test['buildName'] = self.buildName
                test['buildNumber'] = self.buildNumber
                test['tester'] = self.tester
                test['release'] = self.releaseName
                test['branchName'] = self.branchName
                test['reTryCnt'] = 0
                self.testRetryCountDict[testCnt] = 0
                

                setupTest = False
                teardownTest = False
                if 'SETUP' in test:
                    if test['SETUP'] == "True":
                        setupTest = True
                if 'TEARDOWN' in test:
                    if test['TEARDOWN'] == "True":
                        teardownTest = True
                        
                if not (setupTest or teardownTest):
                    self.testStatus[testCnt] = 'WAITING'
                    realTests.append(test)
                    if self.loadDatabase:
                        try:
                            rowId = self.insertMeta(test)
                            if rowId == 0:
                                raise Exception("Database Insert operation fail")
                            test['id'] = rowId
                        except Exception as e:
                            dlog.info('The Database Insert Operation!')
                            dlog.info(e)
                            dlog.error(str(sys.exc_info()))
                            dlog.error(traceback.format_exc())
                        time.sleep(0.5)
                self.allTests.append(test)
                testCnt = testCnt + 1
            self.realTestsPerTestSet[testSet] = realTests
        #Initialize the States of the Setup and TearDown for each cluster
        self.setupTearDownStatesPerCluster = {}
        for cluster in self.clusters:
            clusterState = {}
            for testSet in self.setupTearDownDict:
                clusterState[testSet] = {'Setup' : False, 'TearDown' : False, 'Failed' : False}
            self.setupTearDownStatesPerCluster[cluster] = clusterState
        #self.printSetupStates(self.setupTearDownStatesPerCluster)
        #dlog.info('TearDown List:')
        #dlog.info(self.setupTearDownDict)        
        
        self.tearDownStatus = {}
        for testSet in self.testSets:
            self.tearDownStatus[testSet] = False
            
        clusterCurrentTestSet = {}
        for cluster in self.clusters:
            clusterCurrentTestSet[cluster] = None
        
        mainLoopCnt = 0
        while (self.getTestWaitingCnt() > 0) and ( not self.isAllClustersStale() ) and canProceed:
            #This is the main loop which runs till all the tests are executed!
            mainLoopCnt = mainLoopCnt + 1
            time.sleep(1)
            dlog.info('Looping the Main Loop: %d' %mainLoopCnt)
            if mainLoopCnt > 100000:
                dlog.info('Exceeded more than 100000 Main Loops. Exiting the Main Loop!')
                canProceed = False
                
            testExecCount = 0
            while (self.getFreeClusterCnt() > 0) and (self.getTestWaitingCnt() > 0) and (testExecCount < len(self.allTests)):
                self.beginTests = True
                #dlog.info(self.clusterState)
                test = self.allTests[testExecCount]
                testSet = test['testSet']
                testId = test['testId']
                testExecCount = testExecCount + 1
                time.sleep(0.1)
                
                if 'SETUP' in test:
                    if test['SETUP'] == "True":
                        #dlog.info('Setup tests are handled separately!')
                        self.testStatus[testId] = 'SKIP'
                        continue
                 
                if 'TEARDOWN' in test:
                    if test['TEARDOWN'] == "True":
                        #dlog.info('TearDown tests are handled separately!')
                        self.testStatus[testId] = 'SKIP'
                        continue
                    
                if self.testStatus[testId] != 'WAITING':
                    continue
                
                #Get the test timeout value
                if 'TIMEOUT' in test:
                    timeout = test['TIMEOUT']
                    try:
                        timeout = int(timeout)
                    except Exception as e:
                        timeout = self.defaultTimeout
                    testTimeOutValues = {'TIMEOUT' : timeout, 'STARTTIME' : None, 'ENDTIME' : None, 'TEST' : test, 'CLUSTER' : None }
                    self.testTimeOutDict[testId] = testTimeOutValues
                else:
                    dlog.info('The Test requires a timeout! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
            
                #Get the test NAME value
                if 'NAME' in test:
                    testName = test['NAME']
                else:
                    dlog.info('The Test requires a NAME! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
                
                #Get the test location or type value
                if 'LOCATION' in test:
                    testLoc = test['LOCATION']
                    
                elif 'TYPE' in test:
                        testType = test['TYPE']
                else:
                    dlog.info('The Test requires a LOCATION or TYPE! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
                #Get the test OWNER value
                if 'OWNER' in test:
                    testOwner = test['OWNER']
                else:
                    dlog.info('The Test requires an OWNER! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
                #Get the test OWNER value
                if 'CATEGORY' in test:
                    testCategory = test['CATEGORY']
                else:
                    dlog.info('The Test requires a CATEGORY! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
                #Get the test COMPONENT value
                if 'COMPONENT' in test:
                    testComponent = test['COMPONENT']
                else:
                    dlog.info('The Test requires a COMPONENT! Skipping the test!')
                    self.testStatus[testId] = 'SKIP'
                    dlog.info(test)
                    continue
                
                
                #Check if the clusterState is required for the test
                requiredClusterState = 'UP'
                if 'clusterState' in test:
                    requiredClusterState = test['clusterState']
                
                if 'SERIAL' in test:
                    cannotRunNow = False
                    if test['SERIAL'] == 'True':
                        #dlog.info('Checking if the previous test in the testset has completed!')
                        testSetTests = self.testSuite[testSet]
                        for testx in testSetTests:
                            testIdx = testx['testId']
                            if testId > testIdx and \
                                ( self.testStatus[testIdx] == 'WAITING' or self.testStatus[testIdx] == 'RUNNING' ):
                                cannotRunNow = True
                                break
                        if cannotRunNow:
                            dlog.info('This test is a serial test which cannot be executed at this time due to serial order!')
                            time.sleep(1)   
                            continue
                        
                envReqs = {}
                if 'ENVREQS' in test:
                    envReqs = test['ENVREQS']
                
                clusterList = self.getClusterList(envReqs)
                #Check if the clusterList is empty. Make sure that there are clusters which are matching the test env
                if not clusterList:
                    dlog.info('The Test is skipped as there are no clusters which match the test environment!')
                    testId = test['testId']
                    self.testStatus[testId] = 'SKIP'
                    if self.loadDatabase:
                        self.updateTestStatus(test, "SKIP")
                    continue
                #Check if the Setup failed for this test in all the clusterList
                if self.checkIfSetupFailedInAll(clusterList, testSet):
                    dlog.info('The Test is skipped as the setup failed in all the Clusters!')
                    self.testStatus[testId] = 'SKIP'
                    if self.loadDatabase:
                        self.updateTestStatus(test, "SKIP")
                    continue
                
                cluster = self.getFreeCluster(clusterList, requiredClusterState, testSet, testExecCount)
                
                if not cluster:   
                    if not self.isAnyClusterBusy(clusterList):
                        dlog.info(self.clusterState)
                        dlog.info('All clusters matching the test ENV are free and are not in the desired state to allocate tests!')
                        dlog.info('!!Skipping the Test as there are no clusters which can be allocated for this test!!')
                        self.testStatus[testId] = 'SKIP'
                        if self.loadDatabase:
                            self.updateTestStatus(test, "SKIP")
                        continue
                    dlog.info('Some clusters are running tests and the free clusters are not in a desired state to allocate new tests!')
                    dlog.info(self.clusterState)
                    continue
                
                
                
                currentTestSet = clusterCurrentTestSet[cluster]
                #dlog.info('Current Test Set %s for  Cluster %s ' % (currentTestSet, cluster))
                if not currentTestSet:
                    currentTestSet = testSet
                    clusterCurrentTestSet[cluster] = currentTestSet
                elif currentTestSet != testSet:
                    clusterCurrentTestSet[cluster] = testSet
                
                
                # Check if TearDown is Required for the TestSet
                testSetList = self.getTestSetsForTearDown()   
                for testSetForTearDown in testSetList:
                    tearDownTestList = self.setupTearDownDict[testSetForTearDown][1]
                    if len(tearDownTestList) != 0:
                        
                        dlog.info('Running TearDown for TestSet %s' % (testSetForTearDown))
                        for cluster1 in self.clusterState:
                            if ( self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['Setup'] and 
                                                not self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['TearDown'] ):
                                self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['TearDown'] = True
                                #dlog.info(self.setupTearDownStatesPerCluster)
                                tearDownStatus = self.runTearDown(cluster1, testSetForTearDown, tearDownTestList)
                                if not tearDownStatus:
                                    dlog.info('TearDown Failed for Testset %s on cluster %s' % (testSetForTearDown, cluster1))
                        #HouseKeeping
                        tearDownComplete = True
                        for cluster1 in self.clusterState:
                            if not self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['TearDown']:
                                tearDownComplete = False
                        self.tearDownStatus[testSet] = tearDownComplete
                        
                #Check if the Setup is Required for the TestSet    
                testSetStatus =  self.setupTearDownStatesPerCluster[cluster][testSet]
                #dlog.info(testSetStatus)
                if not testSetStatus['Setup'] and not testSetStatus['Failed']:
                    dlog.info('Running Setup for the TestSet')
                    setupTestList = self.setupTearDownDict[testSet][0]
                    self.setupTearDownStatesPerCluster[cluster][testSet]['Setup'] = True
                    #self.printSetupStates(self.setupTearDownStatesPerCluster)
                    if len(setupTestList) != 0:
                        setupStatus = self.runSetup(cluster,testSet, setupTestList)
                        if not setupStatus:
                            self.setupTearDownStatesPerCluster[cluster][testSet]['Failed'] = True
                            #dlog.info(self.setupTearDownStatesPerCluster)
                            testExecCount = testExecCount - 1
                            #Unable to proceed with the current test as the Setup Failed for the cluster
                            #Check if the Setup failed for this test in all the clusterList
                            if self.checkIfSetupFailedInAll(clusterList, testSet):
                                dlog.info('The Test is skipped as the setup failed in all the Clusters or LOCAL Test Failed!')
                                self.testStatus[testId] = 'SKIP'
                                if self.loadDatabase:
                                    self.updateTestStatus(test, "SKIP")
                                continue
                            else:
                                continue
                
                self.clusterState[cluster] = 'busy'
                self.clusterCurrentTest[cluster] = test['NAME']
                dlog.info(self.clusterState)
                dlog.info(self.clusterCurrentTest)
                               
                threadCount = threadCount + 1
                
                testTimeOutValues =   self.testTimeOutDict[testId]
                startTime = int(time.time())
                testTimeOutValues['STARTTIME'] = startTime 
                testTimeOutValues['CLUSTER'] = cluster
                self.testRetryCountDict[testId] = self.testRetryCountDict[testId] + 1
                test['reTryCnt'] = self.testRetryCountDict[testId] -1
                dlog.info('\nRunning Test: %s on Cluster: %s Thread Count: %d  \n' % (test['NAME'], cluster, threadCount))
                self.testStatus[testId] = 'RUNNING'
                #Dart will take care of updating the status of the test for RUNNING
                testThread = multiprocessing.Process(target=self.runTest, args=(testName, test, cluster, queue, timeout))
                testThread.daemon = False
                testThread.start()
                conns.append(testThread)
                testTimeOutValues['THREAD'] = testThread
                self.testTimeOutDict[testId] = testTimeOutValues
          
            #Book Keeping
            while not queue.empty():
                dlog.info('Return Value:')
                returnValue = queue.get()
                testResults = returnValue['testResults']
                self.printTestResults(testResults)
                self.getFailedTestFromReturnValue(returnValue)
                threadCount = threadCount -1
                dlog.info('Thread Count Went Down %d ' % threadCount)
                cluster = returnValue['clusterName']
                testReturn = returnValue['test']
                #Update the EndTime in the testTimeOutDict
                testId = testReturn['testId']
                testName = returnValue['testName']
                dlog.info('The TestName: %s has been released from the Job Queue' % testName)
                endTime = int(time.time())
                testTimeOutValues =   self.testTimeOutDict[testId]
                testTimeOutValues['ENDTIME'] = endTime
                self.testTimeOutDict[testId] = testTimeOutValues
                self.testStatus[testId] = 'Complete'
                dlog.info(testTimeOutValues)
                
                
                testResult = False
                testResults = returnValue['testResults']
                for testSet in testResults:
                    testResultSet = testResults[testSet]
                    testResult = testResultSet[0][2]
                dlog.info('The test %s returned back with the following result: %s' % (testName, testResult))
                
                ##Retry Logic ##
                if not testResult and self.clusterState[cluster] != 'install' and testId in self.testRetryCountDict:
                    if self.testRetryCountDict[testId] <= self.retryCount :
                        dlog.info('Attempting to re-run the test %s as the Retry count is enabled! %d' % (testName, self.testRetryCountDict[testId]))
                        self.testStatus[testId] = 'WAITING'
                    
                #Verify if the cluster is in Install phase
                if self.clusterState[cluster] == 'install':
                    #Verify if the install was successful. If not do not free up the cluster.
                    if testResult:
                        self.clusterState[cluster] = 'free'
                    else:
                        self.clusterState[cluster] = 'stale'
                elif self.pingCluster(cluster):
                    #Verify if the cluster state is stale.
                    dlog.info(self.clusterCurrentTest)
                    if testName == self.clusterCurrentTest[cluster]:
                        self.clusterCurrentTest[cluster] = None
                        if self.clusterState[cluster] != 'stale':
                            self.clusterState[cluster] = 'free'
                    else:
                        dlog.info('Not freeing the Cluster as a Test is currently assigned to the Cluster which is not the same as the test which came out of the queue!')
                        dlog.info('Current Test: %s' % self.clusterCurrentTest[cluster])
                        dlog.info('TestName from the Queue: %s' % testName)
                    dlog.info(self.clusterCurrentTest)
                else:
                    self.clusterCurrentTest[cluster] = None
                    self.clusterState[cluster] = 'stale'    
                self.testResults.append(returnValue)
            
            #Check for any test timeouts and kill the thread if the test exceeds!
            for testId in self.testTimeOutDict:
                testTimeOutValues =   self.testTimeOutDict[testId]
                if testTimeOutValues['STARTTIME'] and not testTimeOutValues['ENDTIME']:
                    currentTime = int(time.time())
                    timeout = testTimeOutValues['TIMEOUT']
                    startTime = testTimeOutValues['STARTTIME']
                    elapsedTime = currentTime - startTime
                    if elapsedTime > timeout:
                        dlog.info('The test Id : %d has exceeded timeout value!' %testId)
                        dlog.info('Current Elapsed Time: %d TimeOut for this Test: %d' % (elapsedTime,timeout ))
                        test = testTimeOutValues['TEST']
                        cluster = testTimeOutValues['CLUSTER']
                        testName = test['NAME']
                        
                        
                        status = 'RUNNING'
                        if self.loadDatabase:
                            statusRows = self.selectTestStatus(test)
                            dlog.info(statusRows)
                            if statusRows:
                                status = statusRows[0][0]
                                
                        
                        if status == 'RUNNING':
                            dlog.info('!!Killing the test!!')
                            testThread = testTimeOutValues['THREAD']
                            testThread.terminate()
                            time.sleep(1)
                            self.testStatus[testId] = 'Timeout'
                        else:
                            dlog.info('The test %s has already completed!' % testName)
                            self.testStatus[testId] = 'Complete'
                        
                        
                        ##Retry Logic ##
                        if status != 'PASS' \
                            and self.clusterState[cluster] != 'install' and testId in self.testRetryCountDict:
                            
                            if self.testRetryCountDict[testId] <= self.retryCount :
                                dlog.info('Attempting to re-run the test %s as the Retry count is enabled! %d' % (testName, self.testRetryCountDict[testId]))
                                self.testStatus[testId] = 'WAITING'
                        
                        testTimeOutValues['ENDTIME'] = currentTime
                        self.testTimeOutDict[testId] = testTimeOutValues
                        
                        testResults = {}
                        response = {'testName' : testName, 'test' : test, 'totalTime' : -1, 'clusterName': cluster }   
                        response['testResults'] = testResults
                        returnValue = response
                        dlog.info('Freeing up the Cluster %s!' % cluster)
                        if self.clusterState[cluster] == 'install':
                            self.clusterState[cluster] = 'stale'
                        elif self.pingCluster(cluster):
                            #Verify if the cluster state is stale.
                            dlog.info('Waiting for 60 seconds before releasing the cluster for other tests!')
                            time.sleep(60)
                            self.clusterCurrentTest[cluster] = None
                            if self.clusterState[cluster] != 'stale':
                                self.clusterState[cluster] = 'free'
                        else:
                            self.clusterCurrentTest[cluster] = None
                            self.clusterState[cluster] = 'stale'  
                        dlog.info(self.clusterCurrentTest)
                        self.testResults.append(returnValue)
                        if self.loadDatabase and status == 'RUNNING':
                            try:
                                columns = {'status' : 'ABORT' } 
                                self.updateTest(test, columns)
                            except Exception as e:
                                dlog.info('The Database Update Operation Failed!')
                                dlog.info(e)
                                dlog.error(str(sys.exc_info()))
                                dlog.error(traceback.format_exc())
            
                   
            dlog.info('Tests may be currently running..Sleeping for 10 seconds before checking the Queue!')
            dlog.info(self.clusterState)
            time.sleep(10)
         
        dlog.info('Done with initiating all the tests!')
        
        
        testRunning = True
        #Check for any test timeouts and kill the thread if the test exceeds!
        while testRunning:
            testRunning = False
            for testId in self.testTimeOutDict:
                testTimeOutValues =   self.testTimeOutDict[testId]
                if testTimeOutValues['STARTTIME'] and not testTimeOutValues['ENDTIME']:
                    testRunning = True
                    currentTime = int(time.time())
                    timeout = testTimeOutValues['TIMEOUT']
                    startTime = testTimeOutValues['STARTTIME']
                    elapsedTime = currentTime - startTime
                    
                    if elapsedTime > timeout:
                        dlog.info('The test Id : %d has exceeded timeout value!' %testId)
                        dlog.info('Current Elapsed Time: %d TimeOut for this Test: %d' % (elapsedTime,timeout ))
                        test = testTimeOutValues['TEST']
                        cluster = testTimeOutValues['CLUSTER']
                        testName = test['NAME']
                        
                        status = 'RUNNING'
                        if self.loadDatabase:
                            statusRows = self.selectTestStatus(test)
                            if statusRows:
                                status = statusRows[0][0]
                        
                        if status == 'RUNNING':
                            dlog.info('!!Killing the test!!')
                            testThread = testTimeOutValues['THREAD']
                            testThread.terminate()
                            time.sleep(1)
                            self.testStatus[testId] = 'Timeout'
                        else:
                            dlog.info('The test %s has already completed!' % testName)
                            self.testStatus[testId] = 'Complete'
                        
                        testTimeOutValues['ENDTIME'] = currentTime
                        self.testTimeOutDict[testId] = testTimeOutValues
                    
                        testResults = {}
                        response = {'testName' : testName, 'test' : test, 'totalTime' : -1, 'clusterName': cluster }   
                        response['testResults'] = testResults
                        returnValue = response
                        dlog.info('Freeing up the Cluster %s!' % cluster)
                        if self.clusterState[cluster] == 'install':
                            self.clusterState[cluster] = 'stale'
                        elif self.pingCluster(cluster):
                            #Verify if the cluster state is stale.
                            dlog.info('Waiting for 60 seconds before releasing the cluster for other tests!')
                            time.sleep(60)
                            self.clusterCurrentTest[cluster] = None
                            if self.clusterState[cluster] != 'stale':
                                self.clusterState[cluster] = 'free'
                        else:
                            self.clusterCurrentTest[cluster] = None
                            self.clusterState[cluster] = 'stale'  
                        dlog.info(self.clusterCurrentTest)   
                        self.testResults.append(returnValue)
                        if self.loadDatabase and status == 'RUNNING':
                            try:
                                columns = {'status' : 'ABORT' } 
                                self.updateTest(test, columns)
                            except Exception as e:
                                dlog.info('The Database Update Operation Failed!')
                                dlog.info(e)
                                dlog.error(str(sys.exc_info()))
                                dlog.error(traceback.format_exc())
            if not testRunning:
                dlog.info('All the tests have been executed!')
            else:
                dlog.info('Some tests are still running! Waiting for 10 seconds!')
                time.sleep(10)
                #Book Keeping
                while not queue.empty():
                    dlog.info('Return Value:')
                    returnValue = queue.get()
                    testResults = returnValue['testResults']
                    self.printTestResults(testResults)
                    self.getFailedTestFromReturnValue(returnValue)
                    threadCount = threadCount -1
                    dlog.info('Thread Count Went Down %d ' % threadCount)
                    cluster = returnValue['clusterName']
                    testReturn = returnValue['test']
                    #Update the EndTime in the testTimeOutDict
                    testId = testReturn['testId']
                    testName = returnValue['testName']
                    endTime = int(time.time())
                    testTimeOutValues =   self.testTimeOutDict[testId]
                    testTimeOutValues['ENDTIME'] = endTime
                    self.testStatus[testId] = 'Complete'
                    self.testTimeOutDict[testId] = testTimeOutValues
                    #Verify if the cluster is in Install phase
                    if self.clusterState[cluster] == 'install':
                        #Verify if the install was successful. If not do not free up the cluster.
                        testResults = returnValue['testResults']
                        testResult = False
                        for testSet in testResults:
                            testResultSet = testResults[testSet]
                            testResult = testResultSet[0][2]
                        if testResult:
                            self.clusterState[cluster] = 'free'
                        else:
                            self.clusterState[cluster] = 'stale'
                    elif self.pingCluster(cluster):
                        if testName == self.clusterCurrentTest[cluster]:
                            self.clusterCurrentTest[cluster] = None
                            if self.clusterState[cluster] != 'stale':
                                self.clusterState[cluster] = 'free'
                                dlog.info('Freeing up the cluster %s' % cluster)
                        else:
                            dlog.info('Not Freeing the cluster %s as it could be already assigned!' % cluster)
                            dlog.info('Current Test: %s' % self.clusterCurrentTest[cluster])
                            dlog.info('TestName from the Queue: %s' % testName)
                    else:
                        self.clusterCurrentTest[cluster] = None
                        self.clusterState[cluster] = 'stale'     
                    self.testResults.append(returnValue)
            #Continue to wait or timeout for the remaining tests!    
                  
        #Run the Final TearDown if it exists!
        # Check if TearDown is Required for the TestSet
        testSetList = self.getTestSetsForTearDown()   
        for testSetForTearDown in testSetList:
            tearDownTestList = self.setupTearDownDict[testSetForTearDown][1]
            if len(tearDownTestList) != 0:
                dlog.info('Running TearDown for TestSet %s' % (testSetForTearDown))
                for cluster1 in self.clusterState:
                    if (self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['Setup'] and 
                            not self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['TearDown'] ):
                        self.setupTearDownStatesPerCluster[cluster1][testSetForTearDown]['TearDown'] = True
                        dlog.info(self.setupTearDownStatesPerCluster)
                        tearDownStatus = self.runTearDown(cluster1, testSetForTearDown, tearDownTestList)
                        if not tearDownStatus:
                            dlog.info('TearDown Failed for Testset %s on cluster %s' % (testSetForTearDown, cluster1))
                    
        if self.loadDatabase:
            try:
                self.updateWaitingTestByRunId(self.runId)
            except Exception as e:
                dlog.info('The Database Update Operation Failed!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())

        runEndTime = time.time()
        runEndTimeStr = datetime.datetime.fromtimestamp(runEndTime).strftime('%Y-%m-%d %H:%M:%S')
        duration = runEndTime - self.runStartTime
        
        if self.loadDatabase:
            try:
                self.updateRunInfo(self.runId, runEndTimeStr, duration)
            except Exception as e:
                dlog.info('The Database Update Operation!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                
        dlog.info(self.clusterState)
        

        if self.loadDatabase and not self.disableNotify:
            try:
                #send email if user wants to load data to database
                self.sendMailToFailedTestOwner()
            except Exception as e:
                dlog.info('The Database Update Operation!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())

        if self.fileTouched and os.path.isfile(self.absTouchFileName) and not self.beginTests:
            try:
                os.remove(self.absTouchFileName)
            except Exception as e:
                dlog.info('The Database Update Operation!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
        # Send DartRunner Log to server
        if self.loadDatabase:
            try:
                self.sendFrameworkLogToServer(self.logFile, "DartRunner_%s.log" % self.runId)
            except Exception as e:
                dlog.info('The Database Update Operation!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
        
        self.printFinalTestResults(self.testResults)
        thresholdStatus = self.verifyTestResults(self.testResults,self.threshold)
        dlog.info('Dart DashBoard URL: %s'%self.dashBoardURL)
        if thresholdStatus:
            sys.exit(0)
        else:
            sys.exit(1)

    #End of the main Program
    
    
    def sendFrameworkLogToServer(self, localLog, logShortName):

        try:
            handler = DartDBConnect(DB_HOST, DB_NAME)
            (msg, isSuccessful) = handler.uploadLogFile(localLog, logShortName)
            if not isSuccessful:
                dlog.info("Upload log to server fail for %s" % self.runId)
        except Exception as e:
            dlog.error(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())


    def getRevisionAndBuildNumber(self, data):
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(data.encode("utf-8"), "html5lib")
            head = soup.find('head')
            title = head.findAll('title')[0].get_text().strip()

            tmpStr = title.split('#')[-1]
            buildNumber = tmpStr.split(' ')[0]

            body = soup.find('body', {'id': 'jenkins'})
            pageBody = body.find('div', {'id': 'page-body'})
            mainPanelContent = pageBody.find('div', {'id': 'main-panel-content'})
            if mainPanelContent is None:
                mainPanelContent = pageBody.find('div', {'id': 'main-panel'})
            fileList = mainPanelContent.find('table', {'class': 'fileList'})
            self.allTrForRpmList = fileList.findAll('tr')
            self.allTrForRpmList = self.allTrForRpmList[:-1]
            for tr in self.allTrForRpmList:
                td = tr.findAll('td')[1]
                tmpStr = td.get_text()
                if "coordinator" in tmpStr:
                    tmpStr = tmpStr.split("-r")[-1]
                    if '-' in tmpStr:
                        revisionNumber = tmpStr.split("-")[0]
                    else:
                        revisionNumber = tmpStr.split(".")[0]

            return buildNumber, revisionNumber
        except:
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc())
            sys.exit(1)


    def parseWebPage(self, url):
        try:
            dlog.info('Parsing the URL : %s to get the buildNumber and RevisionNumber' % url)
            ret = requests.get(url)

            if ret.status_code != 200:
                dlog.info("Get Jenkins page failed!")
                sys.exit(1)

            buildNumber, revisionNumber = self.getRevisionAndBuildNumber(ret.text)
            dlog.info('BuildNumber Parsed: %s' %buildNumber)
            dlog.info('RevisionNumber Parsed: %s' % revisionNumber)
            return buildNumber, revisionNumber
        except:
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc())
            sys.exit(1)


    def parseUrlToGetBuildNumberAndRevision(self, clusterList, url):
        buildNumber, revisionNumber = self.parseWebPage(url)
        if self.runLabel != "" and self.projectName != 'Private':
            touchFileName = '__' + self.projectName + '_' + self.runLabel + '_' + self.branchName + '_' + buildNumber + '_' + revisionNumber + '__'
            currentDir = os.path.dirname(__file__)
            absDirectoryLoc = os.path.join(currentDir, 'revisions')
            if not os.path.exists(absDirectoryLoc):
                os.makedirs(absDirectoryLoc)
            absTouchFileName = os.path.join(absDirectoryLoc, touchFileName)
            self.absTouchFileName = absTouchFileName
        
            if os.path.isfile(absTouchFileName):
                dlog.info('This build has already been run once! Please remove the file %s to re-run it again!' % absTouchFileName)
                sys.exit(0)
            else:
                self.fileTouched = True
                with open(absTouchFileName, "w") as f:
                    f.write("")
                    
        return buildNumber, revisionNumber


    def getQueenIpUserNameAndPassword(self, clusters):
        clustersInfo = []
        for cluster in clusters:
            clusterCfg = cluster + ".cfg"
            clusterDict = {}
            with open(os.path.abspath(os.path.dirname(__file__)) + "/config/" + clusterCfg, "r") as f:
                cfgJson = json.loads(f.read())
                cluster = cfgJson['cluster']
                if '.' in cluster['queenNodes'][0]:
                    clusterDict['workerNodes'] = cluster['workerNodes']
                    clusterDict['ip'] = cluster['queenNodes'][0]
                else:
                    if 'domain' not in cluster:
                        dlog.error("Either IP or domain name is required in cluster config")
                        raise
                    clusterDict['ip'] = cluster['queenNodes'][0] + "." + cluster['domain']

                workerNodes = []
                for worker in cluster['workerNodes']:
                    if '.' in worker:
                        workerNodes.append(worker)
                    else:
                        workerNodes.append(worker + "." + cluster['domain'])
                clusterDict['workerNodes'] = workerNodes
                clusterDict['username'] = cluster['username']
                clusterDict['password'] = cluster['password']

            clustersInfo.append(clusterDict)

        return clustersInfo


    def downloadRpm(self, clusterStr, url):
        clusters = clusterStr.split(",")
        dlog.info('Downloading the RPMS from the buildURL Location...')
        clustersInfo = self.getQueenIpUserNameAndPassword(clusters)
        rpmList = []

        try:
            #dlog.info(self.allTrForRpmList)
            for tr in self.allTrForRpmList:
                td = tr.findAll('td')[1]
                fileName = td.get_text()
                currentDir = os.path.dirname(__file__)
                absDirectoryLoc = os.path.join(currentDir, self.timeStamp)
                if not os.path.exists(absDirectoryLoc):
                    os.makedirs(absDirectoryLoc)
                fileNameAbs = os.path.join(absDirectoryLoc, fileName)
            
                rpmList.append(fileNameAbs)
                fileLink = url + "/" + fileName
                ret = requests.get(fileLink)
                rpmFile = ret.content
                with open(fileNameAbs, "w") as f:
                    f.write(rpmFile)
            dlog.info(rpmList)
            self.scpRpmToQueen(clustersInfo, rpmList)
            for fileNameAbs in rpmList:
                os.remove(fileNameAbs)
            os.rmdir(absDirectoryLoc)
        except:
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc())
            if self.fileTouched and os.path.isfile(self.absTouchFileName) and not self.beginTests:
                os.remove(self.absTouchFileName)
            sys.exit(1)

    def transferRpmsToQueen(self, clusterStr, buildLoc):
        clusters = clusterStr.split(",")

        clustersInfo = self.getQueenIpUserNameAndPassword(clusters)
        rpmList = []

        try:       
            for fileName in os.listdir(buildLoc):
                if '.rpm' in fileName:
                    rpmList.append(os.path.abspath(os.path.join(buildLoc,fileName)))
            self.scpRpmToQueen(clustersInfo, rpmList)
            
        except:
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc())
            if self.fileTouched and os.path.isfile(self.absTouchFileName) and not self.beginTests:
                os.remove(self.absTouchFileName)
            sys.exit(1)


    def cleanupRemoteFolders(self, clusterDict):
        try:
            queenCon = None
            queenIp = clusterDict['ip']
            username = clusterDict['username']
            password = clusterDict['password']
            if "privateKey" in clusterDict:
                privateKey = clusterDict['privateKey']
            else:
                privateKey = None
            
            queenCon = SshConnect(queenIp, username, password, privateKey)
            queenCon.connect()
            stdout, stderr, status = queenCon.execCommand("rm -rf /tmp/rpms/*", timeout=300)
            stdout, stderr, status = queenCon.execCommand("mkdir -p /tmp/rpms")
            for workerIp in clusterDict['workerNodes']:
                workerCon = SshConnect(workerIp, username, password, privateKey)
                workerCon.connect()
                stdout, stderr, status = workerCon.execCommand("rm -rf /tmp/rpms/*", timeout=300)
        except:
            dlog.error("Create /tmp/rpms on Queen failed")
            dlog.error(sys.exc_info())
            dlog.error(traceback.format_exc())
            if self.fileTouched and os.path.isfile(self.absTouchFileName) and not self.beginTests:
                os.remove(self.absTouchFileName)
        finally:
            if queenCon:
                queenCon.close()
            



    def scpRpmToQueen(self, clustersInfo, rpmList):
        for cluster in clustersInfo:
            try:
                self.cleanupRemoteFolders(cluster)
                conn = Sftp(cluster['ip'], username=cluster['username'], password=cluster['password'])
                conn.connect()
                for localFile in rpmList:
                    baseFileName = os.path.basename(localFile)
                    conn.put(localFile, "/tmp/rpms/" + baseFileName)
            except:
                dlog.error("Transfer file to Queen failed")
                dlog.error(sys.exc_info())
                dlog.error(traceback.format_exc())
                if self.fileTouched and os.path.isfile(self.absTouchFileName) and not self.beginTests:
                    os.remove(self.absTouchFileName)


    def signalTermHandler(self, signal, frame):
        if self.loadDatabase:
            handler = DartDBConnect(DB_HOST, DB_NAME)
            handler.updateRow("darttest", {"status": "ABORT"}, "run_id='%s' and status='WAITING'" % self.runId)

            endRunTime = time.time()
            duration = endRunTime - self.runStartTime
            endTimeStamp = datetime.datetime.fromtimestamp(endRunTime).strftime('%Y-%m-%d %H:%M:%S')
            self.updateRunInfo(self.runId, endTimeStamp, duration)
            
        if self.fileTouched and os.path.isfile(self.absTouchFileName):
            os.remove(self.absTouchFileName)
        sys.exit(1)

    def sendMailToFailedTestOwner(self):
        mailContentHeader = ""
        mailContentHeader = mailContentHeader + "Below is the failed test report. Please review it!\n"
        mailContentHeader = mailContentHeader + "------------------------------------------------------------ FINAL RESULTS "
        mailContentHeader = mailContentHeader + "------------------------------------------------------------\n"
        mailContentHeader = mailContentHeader + "---------------------------------------------------------------------------"
        mailContentHeader = mailContentHeader + "------------------------------------------------------------\n"
        mailContentHeader = mailContentHeader + "%20s%40s%25s%25s%15s\n" % ('TESTSET', ' TESTNAME','START TIME', 'END TIME', 'TIME (secs)')
        mailContentFooter = "-----------------------------------------------------------------------------------------------"
        mailContentFooter = mailContentFooter + "----------------------------------------\n\n"
        for owner in self.failedTestOwnerDict:
            results = self.failedTestOwnerDict[owner]
            content = "Hi %s, \n\n" %owner
            content = content + mailContentHeader
            for result in results:
                testset = result['testset']
                testName = result['testname']
                startTimeStr = result['startTime']
                endTimeStr = result['endTime']
                timeTaken = result['duration']
                runId = result['run_id']
                content = content + "%20s%40s%25s%25s%15s\n" %(testset, testName, startTimeStr, endTimeStr, timeTaken)

            content = content +  mailContentFooter
            content = content + "Click the following link to see the details: \n"
            content = content + "http://%s/failTestByOwner?owner=%s&run_id=%s" %(DB_HOST, owner, runId)
            content = content + "\n\n"
            content = content + "Thanks,\n"
            content = content + "Dart team"


            cmd = 'echo "%s" | mail -s "[Dart] Failed Tests Report" %s@teradata.com' %(content, owner)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            if status != 0 and stdout != None:
                dlog.error("Send email fail: %s" % stdout)


    def getFailedTestFromReturnValue(self, returnValue):
        dlog.info("-------------------------------------------------------------------------------------------------")        
        dlog.info("returnValue = %s" % returnValue)        
        dlog.info("-------------------------------------------------------------------------------------------------")
        try:
            testResults = returnValue['testResults']
            if len(testResults) != 0:
                for key in testResults:
                    if not testResults[key][0][2]:
                        result = {'testset': key, 'testname': testResults[key][0][0], \
                                  'startTime': testResults[key][0][3], 'endTime': testResults[key][0][4], \
                                  'duration': testResults[key][0][1], 'run_id': returnValue['test']['runId']}

                        if result['testset'] != "Install":
                            owner = returnValue['test']['OWNER']
                            self.addFailedTestInfoToDict(owner, result)
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())


    def addFailedTestInfoToDict(self, owner, testResult):
        if owner not in self.failedTestOwnerDict:
            self.failedTestOwnerDict[owner] = []

        self.failedTestOwnerDict[owner].append(testResult)


    def getTestWaitingCnt(self):
        count = 0
        for testId in self.testStatus:
            if self.testStatus[testId] == 'WAITING':
                count = count + 1
        return count
    
    def checkIfSetupFailedInAll(self, clusterList, testSet) :
        setupFailed = True
        for cluster in clusterList:
            if not self.setupTearDownStatesPerCluster[cluster][testSet]['Failed']:
                setupFailed = False
        return setupFailed
                    
    def insertRunInfo(self, runId, runStartTimeStr):
        handler = DartDBConnect(DB_HOST, DB_NAME)
        meta = {"run_id": runId, "start_time": runStartTimeStr, "release_name": self.projectName,
                "build_number": self.buildNumber, "branch": self.branchName, "revision": self.revisionNumber,
                "tester": self.tester, "run_label": self.runLabel, "run_command": self.runCommand, 
                "run_type" : self.load, "release" : self.releaseName, "keywords" : self.keywords, "comments": self.comments}
        res = handler.insertRow("dartruninfo", meta)

        dlog.info('Done inserting the information of run %s' % runId)
        if res[1]:
            return res[0]

        return 0


    def updateRunInfo(self, runId, runEndTimeStr, duration):
        handler = DartDBConnect(DB_HOST, DB_NAME)
        meta = {"end_time": runEndTimeStr, "duration": DartUtility.intToTimeFormat(duration)}
        (msg, isSuccessful) = handler.updateRow("dartruninfo", meta, "run_id='%s'" %runId)
        if not isSuccessful:
            dlog.info("Updating status to SKIP fail for run ID %s" % runId)



    def updateWaitingTestByRunId(self, runId):
        handler =  DartDBConnect(DB_HOST, DB_NAME)
        meta = {"status": "SKIP"}
        (msg, isSuccessful) = handler.updateRow("darttest", meta, "run_id='%s' and status='WAITING'" %runId)
        if not isSuccessful:
            dlog.info("Updating status to SKIP fail for run ID %s" % runId)
 
    

    def isAllClustersStale(self):
        staleClusterCnt = 0
        for cluster in self.clusterState:
            if self.clusterState[cluster] == 'stale':
                staleClusterCnt = staleClusterCnt + 1
        if staleClusterCnt < len(self.clusters):
            return False
        else:
            return True
        
    def isAnyClusterBusy(self, clusterList):
        busyClusterCnt = 0
        for cluster in clusterList:
            if self.clusterState[cluster] == 'busy' or self.clusterState[cluster] == 'install':
                busyClusterCnt = busyClusterCnt + 1
        if busyClusterCnt == 0:
            return False
        else:
            return True
        
    def getFreeCluster(self, clusterList, requiredClusterState, testSet, testExecCount):
        for cluster in clusterList:
            testSetStatus =  self.setupTearDownStatesPerCluster[cluster][testSet]
            if self.clusterState[cluster] == 'free' and not testSetStatus['Failed']:
                #Reset the counter if it grows more than 10
                if self.checkHealthFailCnt[cluster] > 10:
                    self.checkHealthFailCnt[cluster] = 0
                if requiredClusterState == 'UP':
                    
                    if self.checkHealthFailCnt[cluster] > 3 and self.checkHealthFailCnt[cluster] <= 10:
                        if testExecCount <= 1:
                            dlog.info('The Check Health Already failed for cluster %s' % cluster)
                            self.checkHealthFailCnt[cluster] = self.checkHealthFailCnt[cluster] + 1
                        continue
                    if not self.checkHealthWithTimeOut(cluster,900):
                        self.checkHealthFailCnt[cluster] = self.checkHealthFailCnt[cluster] + 1
                        dlog.info('The Check Health failed for cluster %s' % cluster)
                        dlog.info('Checking for a next free cluster!')
                        continue
                    else:
                        return cluster
                else:
                    self.checkHealthFailCnt[cluster] = 0
                    return cluster
        dlog.info('Unable to Get free Cluster!')
        return False
     
    def getClusterList(self, envReqs):
        clusterList = []
        for cluster in self.clusterState:
            if self.clusterState[cluster] == 'stale':
                continue
            clusterCfg = self.clusterConfigDict[cluster]
            meetsReq = True
            for key in envReqs:
                keyFound = False
                for section in clusterCfg:
                    clusterEnvReqs = clusterCfg[section]
                    if key in clusterEnvReqs:
                        if clusterEnvReqs[key] == envReqs[key]:
                            keyFound = True
                            break
                if not keyFound:
                    meetsReq = False
                    break
            if meetsReq:
                clusterList.append(cluster)
        return clusterList
     
    def runSetup(self, cluster, testSet, setupTestList):
        testResult = True
        try:
            localTestExist = False
            dlog.info('Running Setup on cluster %s' % cluster)
            for test1 in setupTestList:
                testName = test1['NAME']
                dlog.info('+++++++++++++Setup Test Name: %s' % testName)
                localTest = False
                if 'LOCAL' in test1:
                    if test1['LOCAL'] == 'True':
                        localTest = True
                if localTest:
                    if self.localSetupDict[testSet]:
                        dlog.info('The Local Setup Test has already been executed! Skipping!')
                        continue
                    else:
                        localTestExist = True
                result = False
                response = self.runTestSerialWithTimeout(testName, test1, cluster)
                testResults = response['testResults']
                for testSet1 in testResults:
                    testResultSet = testResults[testSet1]
                    result = testResultSet[0][2]
                    
                if not result:
                    testResult = False
                    if localTestExist:
                        self.localSetupDict[testSet] = True
                        #Set all the clusters with the Setup failure as the Local setup Failed!
                        for cluster1 in self.clusterState:
                            self.setupTearDownStatesPerCluster[cluster1][testSet]['Failed'] = True
                    break
                           
        except Exception as e:
            traceback.print_exc()
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
        finally:
            if localTestExist:
                self.localSetupDict[testSet] = True    
            return testResult


    def runTearDown(self, cluster, testSet, tearDownTestList):
        try:
            testResult = True
            localTestExist = False
            
            dlog.info('Running TearDown on cluster %s' % cluster)
                
            for test1 in tearDownTestList:
                testName = test1['NAME']
                dlog.info('+++++++++++++TearDown Test Name: %s' % testName)
                localTest = False
                if 'LOCAL' in test1:
                    if test1['LOCAL'] == 'True':
                        localTest = True
                if localTest:
                    if self.localTearDownDict[testSet]:
                        dlog.info('The Local TearDown Test has already been executed! Skipping!')
                        continue
                    else:
                        localTestExist = True
                response = self.runTestSerialWithTimeout(testName, test1, cluster)
                dlog.info(response)
                testResults = response['testResults']
                for testSet1 in testResults:
                    testResultSet = testResults[testSet1]
                    testResult = testResultSet[0][2]
                    dlog.info('TearDown Result = %s' % testResult)
                        
        except Exception as e:
            traceback.print_exc()
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
        finally:
            if localTestExist:
                self.localTearDownDict[testSet] = True
            return testResult
    
    def getTestSetsForTearDown(self):
        testSetList = []
        #dlog.info(self.testSets)
        for testSet in self.testSets:
            tearDown = True
            tests = self.realTestsPerTestSet[testSet]
            for test in tests:
                if ( test['testSet'] == testSet ):
                    testId = test['testId']
                    status = self.testStatus[testId]
                    if (status == 'WAITING') or (status == 'RUNNING') or (status == 'Timeout' ):
                        tearDown = False
                        break
            if tearDown:
                if not self.tearDownStatus[testSet]:
                    testSetList.append(testSet)
        return testSetList
                    
    def checkHealthWithTimeOut(self, cluster, timeout=900):
        queueCH = multiprocessing.Queue()
        returnStatus = False
        checkHealthThread = multiprocessing.Process(target=self.checkHealth, args=(cluster, queueCH))
        checkHealthThread.daemon = False
        checkHealthThread.start()
        for i in range(timeout):
            time.sleep(1)
            if not checkHealthThread.is_alive():
                break
        if checkHealthThread.is_alive():
            dlog.info('CheckHealth has reached the Timeout!')
            dlog.info('Killing CheckHealth process!')
            checkHealthThread.terminate()
            return False
        time.sleep(1)
        if not queueCH.empty():
            returnStatus = queueCH.get()
            return returnStatus
        else:
            dlog.info('The CheckHealth Queue is Empty!')
            return returnStatus
        
    def checkHealth(self, cluster, queueCH):
        clusterConfig = cluster + '.cfg'
        dlog.info('Running CheckHealth on cluster %s' % cluster)
        testResult = False
        if not self.checkHealthTest:
            queueCH.put(True)
            return True
        try:
            darttest = Dart(configFile=clusterConfig, testFile=self.checkHealthDict,  dartRunner=True)
            testResults = darttest.getResults()
            self.printTestResults(testResults)
            for testSet in testResults:
                testResultSet = testResults[testSet]
                testResult = testResultSet[0][2]
        except Exception as e:
            traceback.print_exc()
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())  
        finally:
            queueCH.put(testResult)
        return testResult
    
    def getFreeClusterCnt(self):
        freeClusterCnt = 0
        for cluster in self.clusterState:
            if self.clusterState[cluster] == 'free':
                freeClusterCnt = freeClusterCnt + 1
        return freeClusterCnt
     
    def loadClusterConfigs(self):
        
        libPath = os.path.abspath(os.path.dirname(__file__))
        for cluster in self.clusters:
            configFile = cluster + '.cfg'
            configFileAbs = libPath + '/config/' + configFile
            tempConfigFile = os.path.join('/tmp', configFile)
            try:
                fileT = open(tempConfigFile, 'w')
                with open(configFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
            
                with open(tempConfigFile, 'r') as f:
                    cfgJson = json.load(f)
                    
                    if 'kubeCluster' in cfgJson:
                        self.kubemasters = cfgJson["kubeCluster"]["kubemaster"]
                        if "deployment" in cfgJson["cluster"]:
                            deployment = cfgJson["cluster"]["deployment"]
                            if deployment.lower() == 'docker' :
                                cfgJson = self.updateCfgJson(cfgJson)
                            if deployment.lower() == 'spark':
                                cfgJson = self.updateSparkCluster(cfgJson)
                    self.clusterConfigDict[cluster] = cfgJson
        
            except ValueError as e:
                dlog.info('The Json File may have syntax issues! Check the config file %s!' % configFile)
                dlog.info(e)
                dlog.info('Exiting Program!')
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                if self.fileTouched and os.path.isfile(self.absTouchFileName):
                    os.remove(self.absTouchFileName)
                sys.exit(2)
            except Exception as e:
                traceback.print_exc()
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                raise

    def kubeExecute(self, commandStr,cfgJson):

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
                raise
            kubemaster = kubemaster + '.' + domainName
        kubeMasterCon = SshConnect(kubemaster, username, password, privateKey)
        kubeMasterCon.connect()
        stdout, stderr, status = kubeMasterCon.execCommand(commandStr, timeout=30)
        dlog.info(stdout + stderr)
        kubeMasterCon.close()
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
                                        dlog.error("WARNING! WARNING! Please check the cluster config file for AWS IP/hostname Mapping!!")  
                            else:
                                nodeName = cfgJson["awsIpMapping"][nodeName]
                        else:
                            dlog.info(cfgJson)
                            dlog.info('The awsIpMapping is not found in the cluster Config File!')
                            dlog.error("WARNING! WARNING! Please check the cluster config file for AWS IP/hostname Mapping!!")    
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
        sparkManager =[]
        sparkthriftserver = []
        stdout = self.kubeExecute(commandStr, cfgJson)
        if (not stdout) or ('kubectl: command not found' in stdout):
            dlog.info("No Spark cluster installed on this cluster. Cannot update cfgjson for Spark")
            return cfgJson
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

    def pingCluster(self, cluster):
        clusterDict = self.clusterConfigDict[cluster]['cluster']
        queenCon = None
        if "deployment" in clusterDict:
            deployment = clusterDict['deployment']
            if deployment.lower() == 'docker' or deployment.lower() == 'spark':
                queenNodes = self.clusterConfigDict[cluster]['kubeCluster']['kubemaster']
                queenNode = queenNodes[0]
        else:
            if "queenNodes" in clusterDict:
                queenNodes = clusterDict['queenNodes']
            queenNode =  queenNodes[0]
        
        if '.' in queenNode:
            queenNodewithDomain = queenNode
        elif 'domain' in clusterDict:
            domainName = clusterDict['domain']
            queenNodewithDomain = queenNode + '.' + domainName
        else:
            dlog.info('QueenNode is not fully qualified in the cluster config file: %s.cfg' % cluster)
            return False
        if "username" in clusterDict:
            username = clusterDict['username']
        else:
            dlog.info('Username is required in the cluster config file: %s.cfg' % cluster)
        if "password" in clusterDict:
            password = clusterDict['password']
        else:
            password = None
        
        if "privateKey" in clusterDict:
            privateKey = clusterDict['privateKey']
        else:
            privateKey = None
        try:
            queenCon = SshConnect(queenNodewithDomain, username, password, privateKey)
            queenCon.connect()
            commandStr = 'lsb_release -a'
            stdout, stderr, status = queenCon.execCommand(commandStr, timeout=30)
            dlog.info('Ping on cluster %s Successful!' % cluster)
            #print(stdout)
            return True
        except Exception as e:
            dlog.info('The cluster is down. Unable to reach %s' % cluster)
            dlog.info (e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            return False
        finally:
            if queenCon:
                queenCon.close()
            
        
    def runTest(self, testName, test, cluster, queue, timeout):
        try:
            
            ##Check the pre-condition for the test 
            response = {'testName' : testName, 'test': test,'clusterName': cluster }
            testResults = {}
            startTime = time.time()
            startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
            if self.loadDatabase:
                try:
                    self.updateCluster(cluster, test)
                except Exception as e:
                    dlog.info('The Database Update Operation Failed!')
                    dlog.info(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    
                
                testProject = ""
                if 'projectName' in test:
                    testProject = test['projectName']
                branchName = ""
                if 'branchName' in test:
                    branchName = test['branchName']
                
                releaseName = ""
                if 'release' in test:
                    releaseName = test['release']
                runId = ""
                if 'runId' in test:
                    runId = test['runId']
                
                try:    
                    meta = None
                    if 'LOCAL' not in test:
                        meta = self.getRemainingMeta(cluster, branchName)
                    if meta:
                        self.updateTest(test, meta)
                except Exception as e:
                    dlog.info('The Database Update Operation Failed to update the Cluster Meta Data!')
                    dlog.info(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                    
                try:
                    
                    dlog.info('Updating the status to Running in the database: %s!' % testName)
                    columns = {'status': 'RUNNING', 'start_time': startTimeStr}
                    self.updateTest(test, columns)
                except Exception as e:
                    dlog.info('The Database Update Operation Failed!')
                    dlog.info(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())
                            
            clusterConfig = cluster + '.cfg'
            testDict = {}
            testList = []
            testList.append(test)
            testDict[test['testSet']] = testList
            if self.noTestLog:
                dlog.removeHandler(self.ch)
            darttest = Dart(configFile=clusterConfig, testFile=testDict, dartRunner=True)
            testResults = darttest.getResults()
                        
        except Exception as e:
            dlog.error(e)
            traceback.print_exc()
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            
        finally: 
            
            endTime = time.time()
            totalTime = int(endTime - startTime)
            response['totalTime'] =  totalTime
            response['testResults'] = testResults    
            queue.put(response)
            
            try:
                testResult = False
                testLogShortName = ''
                testLogFile = ''
                endTimeStr = None
            
                if testResults:
                    for testSet in testResults:
                        testResultSet = testResults[testSet]
                        totalTime = testResultSet[0][1]
                        testResult = testResultSet[0][2]
                        startTimeStr = testResultSet[0][3]
                        endTimeStr = testResultSet[0][4]
                        testLogFile = testResultSet[0][5]
                        testLogShortName = testResultSet[0][6]
                        
                        
                if testResult:
                    status = 'PASS'
                else:
                    status = 'FAIL'
               
                if self.loadDatabase:            
                    serverLogPath = "/root/DartLogs/" + testLogShortName
                
                    columns = {'status': status}
                
                    if os.path.isfile(testLogFile):
                        columns['log_location'] = serverLogPath
                        
                    if endTimeStr:
                        columns['end_time'] = endTimeStr
                    else:
                        endTime = time.time()
                        endTimeStr = datetime.datetime.fromtimestamp(endTime).strftime('%Y-%m-%d %H:%M:%S')
                        columns['end_time'] = endTimeStr
                          
                    columns['execution_time'] = DartUtility.intToTimeFormat(totalTime)
            
                    self.updateTest(test, columns)
                
                    if not testResult:
                        handler = DartDBConnect(DB_HOST, DB_NAME)
                        sql = "run_id=(select run_id from dartruninfo where branch='%s' " %branchName
                        sql = sql + "and release_name='%s' and " %testProject
                        sql = sql + "release='%s' and run_id<>'%s' " %(releaseName, runId)
                        sql = sql + "order by start_time desc limit 1) "
                        sql = sql + "and testcase='%s' order by start_time limit 1;" %testName
                        jiraInfo = handler.selectRows("darttest", "jira_number", sql)

                        if len(jiraInfo) != 0 and jiraInfo[0]['jira_number'] is not None:
                            jiraNumber = jiraInfo[0]['jira_number']
                            jiraColumns = {'jira_number': jiraNumber}
                            self.updateTest(test, jiraColumns)
                        
                    
            except Exception as e:
                dlog.info('The Database Update Operation Failed!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                
            try:        
                if self.loadDatabase:
                    #Upload the Dart Test Log to the DashBoard.
                    if testLogShortName != '' and os.path.isfile(testLogFile):
                        self.uploadLogFile(testLogFile, testLogShortName)   
                        
            except Exception as e:
                dlog.info('Unable to load the LogFile to the Server')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                
            try:
                if self.loadDatabase:
                    if 'reTryCnt' in test:
                        reTryCnt = test['reTryCnt']
                        columns['retry_count'] = reTryCnt
                    retryLogs = self.selectTestRetryLogs(test)
                    
                    retryLogsStr = ''
                    
                    if retryLogs:
                        retryLogsStr = retryLogs[0][0]
                        dlog.info('RETRY LOG STRING =====')
                        dlog.info(retryLogsStr)
                        if not retryLogsStr or retryLogsStr == 'None':
                            retryLogsStr = ''
                    
                    if retryLogsStr != '' :    
                        retryLogsStr = retryLogsStr + ','  + serverLogPath
                    else:
                        retryLogsStr =  serverLogPath 
                    columns['retry_logs'] = retryLogsStr
                    self.updateTest(test, columns)
                                    
            except Exception as e:
                dlog.info('The Database Update Operation Failed to upload the Retry Log Information!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())    
                

            
            
            try:   
                
                if self.loadDatabase:         
                    columns = {}
                    if 'LOCAL' not in test:
                        columns = self.getInfoFromCluster(cluster)
                        self.updateTest(test, columns)
                        
            except Exception as e:
                dlog.info('The Database Update Operation Failed to upload the Cluster Information!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())                
            
            
    
    def runTestSerialWithTimeout(self, testName, test, cluster):
 
        queueRT = multiprocessing.Queue()
        returnStatus = {}
        response = {}
        testResults = {}
        startTime = time.time()
        startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
        response['testResults'] = testResults
                 
        RTThread = multiprocessing.Process(target=self.runTestSerial, args=(testName, test, cluster, queueRT))
        RTThread.daemon = False
        RTThread.start()
        if 'TIMEOUT' in test:
            timeout = test['TIMEOUT']
        try:
            timeout = int(timeout)
        except Exception as e:
            timeout = self.defaultTimeout
            
        for i in range(timeout):
            time.sleep(1)
            if not RTThread.is_alive():
                break
        if RTThread.is_alive():
            dlog.info('Run Test Serial has reached the Timeout!')
            dlog.info('Killing RunTestSerial process!')
            RTThread.terminate()
        endTime = time.time()
        totalTime = int(endTime - startTime)
        response['totalTime'] =  totalTime
        
        time.sleep(1)
        if not queueRT.empty():
            returnStatus = queueRT.get()
            return returnStatus
        else:
            dlog.info('The Run Test Serial Queue is not Empty!')
            return response
        
    
    def runTestSerial(self, testName, test, cluster, queueRT):
        try:
            ##Check the pre-condition for the test
            response = {}
            testResults = {}
            startTime = time.time()
            startTimeStr = datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S')
            if self.loadDatabase:
                try:
                    testId = self.insertMeta(test, "RUNNING")
                    if testId == 0:
                        raise Exception("Database Insert operation fail")
                    test['id'] = testId
                    self.updateCluster(cluster, test)
                    
                    columns = {'start_time': startTimeStr}
                    self.updateTest(test, columns)
                    
                except Exception as e:
                    dlog.info('The Database Insert/Update Operation Failed!')
                    dlog.info(e)
                    dlog.error(str(sys.exc_info()))
                    dlog.error(traceback.format_exc())

                time.sleep(5)

            localSetup = False
            if 'LOCAL' in test:
                if test['LOCAL'] == 'True':
                    localSetup = True
            if localSetup:
                cluster = 'local'
            clusterConfig = cluster + '.cfg'
            testDict = {}
            testList = []
            testList.append(test)
            testDict[test['testSet']] = testList
            darttest = Dart(configFile=clusterConfig, testFile=testDict, dartRunner=True)
            testResults = darttest.getResults()
                        
        except Exception as e:
            traceback.print_exc()
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            response = {'testName' : testName, 'test' : test, 'totalTime' : -1, 'clusterName': cluster }   
        finally:
            ##Check the post condition for the test.
            ##Verify if the cluster is available. Set the state of the cluster.
            response['testResults'] = testResults
            
            endTime = time.time()
            totalTime = int(endTime - startTime)
            response['totalTime'] =  totalTime
            response['testResults'] = testResults    
            
            try:
                testResult = False
                testLogShortName = ''
                testLogFile = ''
                endTimeStr = None
            
                if testResults:
                    for testSet in testResults:
                        testResultSet = testResults[testSet]
                        totalTime = testResultSet[0][1]
                        testResult = testResultSet[0][2]
                        startTimeStr = testResultSet[0][3]
                        endTimeStr = testResultSet[0][4]
                        testLogFile = testResultSet[0][5]
                        testLogShortName = testResultSet[0][6]
                        
                        
                if testResult:
                    status = 'PASS'
                else:
                    status = 'FAIL'
               
                if self.loadDatabase:            
                    serverLogPath = "/root/DartLogs/" + testLogShortName
                
                    columns = {'status': status}
                
                    if os.path.isfile(testLogFile):
                        columns['log_location'] = serverLogPath

                    if endTimeStr:
                        columns['end_time'] = endTimeStr
                    else:
                        endTime = time.time()
                        endTimeStr = datetime.datetime.fromtimestamp(endTime).strftime('%Y-%m-%d %H:%M:%S')
                        columns['end_time'] = endTimeStr
                          
                    columns['execution_time'] = DartUtility.intToTimeFormat(totalTime)
                    self.updateTest(test, columns)
                    
            except Exception as e:
                dlog.info('The Database Update Operation Failed!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                
            try:                    
                    #Upload the Dart Test Log to the DashBoard.
                    if testLogShortName != '' and os.path.isfile(testLogFile):
                        self.uploadLogFile(testLogFile, testLogShortName)   
                        
            except Exception as e:
                
                dlog.info('Unable to load the LogFile to the Server')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())
                
            try:            
                    columns = {}
                    if 'LOCAL' not in test:
                        columns = self.getInfoFromCluster(cluster)
                        self.updateTest(test, columns)
                        
            except Exception as e:
                dlog.info('The Database Update Operation Failed to upload the Cluster Information!')
                dlog.info(e)
                dlog.error(str(sys.exc_info()))
                dlog.error(traceback.format_exc())                
            
            queueRT.put(response)
            return response


    def updateCluster(self, cluster, test):

        localTest = False
        if 'LOCAL' in test:
            if test['LOCAL'] == 'True':
                localTest = True
        if localTest:
            meta = self.getLocalMeta()
        else:
            meta = self.clusterConfigsForDb[cluster]
        
        handler = DartDBConnect(DB_HOST, DB_NAME)
        (msg, isSuccessful) = handler.updateRow("darttest", meta, "id=%s" % test['id'])
        if not isSuccessful:
            dlog.info("Updating fail for %s" % test['id'])

        dlog.info('Updated cluster: %s for test %s' % (cluster, test['NAME']))


    def updateTestStatus(self, test, status):
        #Because the Test id is generated by the database insert operation
        try:
            if 'id' not in test:
                return
            
            meta = {"status": status}
            handler = DartDBConnect(DB_HOST, DB_NAME)
            (msg, isSuccessful) = handler.updateRow("darttest", meta, "id=%s" % test['id'])
            if not isSuccessful:
                dlog.info("Update Failed for %s" % test['id'])

            dlog.info('Updated Status: %s on test %s' % (status, test['NAME']))
        except Exception as e:
            dlog.info('The Database Update Operation for SKIP operation!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())

    def updateTest(self, test, columns):
        #Because the Test id is generated by the database insert operation
        try:
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
            
    def selectTestStatus(self, test):
        #Because the Test id is generated by the database insert operation
        try:
            if 'id' not in test:
                return
            handler = DartDBConnect(DB_HOST, DB_NAME)
            columns = ['status']
            rows = handler.selectRowsUsingPG("darttest", columns, "id=%s" % test['id'])
            if not rows:
                dlog.info("Select Failed for %s" % test['id'])
            else:
                dlog.info('Select Status: %s test %s' % (rows[0], test['NAME']))
            dlog.info(rows)
            return rows
        except Exception as e:
            dlog.info('The Database Select operation FAILED!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            return []
    
    
    def selectTestRetryLogs(self, test):
        #Because the Test id is generated by the database insert operation
        try:
            if 'id' not in test:
                return
            handler = DartDBConnect(DB_HOST, DB_NAME)
            columns = ['retry_logs']
            rows = handler.selectRowsUsingPG("darttest", columns, "id=%s" % test['id'])
            if not rows:
                dlog.info("Select Failed for %s" % test['id'])
            else:
                dlog.info('Select Success: %s test %s' % (rows[0], test['NAME']))
            dlog.info(rows)
            return rows
        except Exception as e:
            dlog.info('The Database Select operation FAILED!')
            dlog.info(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())
            return []
        
            
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
    
    
            
    def insertMeta(self, test, status = "WAITING"):
        testMeta = self.getTestMetadata(test, status)
        testMeta['testset'] = test['testSet']

        # write testMeta to DB
        handler = DartDBConnect(DB_HOST, DB_NAME)
        res = handler.insertRow("darttest", testMeta)

        dlog.info('DB Insert Success: %s' % test['NAME'])
        if res[1]:
            return res[0]

        return 0


    def getClusterMeta(self, cfgJson):
        info = {}

        cluster = cfgJson['cluster']
        if 'name' in cluster:
            info['cluster_name'] = cluster['name']
        else:
            if '.' in cluster['queenNodes'][0]:
                dlog.info("You need to put the Cluster Name in config")
                sys.exit(1)

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

        info['platform_type'] = cluster['clusterType']

        username = cluster['username']
            
        info['release_name'] = self.projectName
        info['build_name'] = self.buildName
        info['tester'] = self.tester
        info['revision'] = self.revisionNumber
        info['build_number'] = self.buildNumber
        info['branch'] = self.branchName
        
        return info

    def getInfoFromCluster(self, cluster):
        info = {}
        try:
            kernelVersion, osVersion = self.getKernelAndOSVersion(cluster)
            info['kernel_version'] = kernelVersion
            info['os_version'] = osVersion
            
        except Exception as e:
            dlog.error("Can't get kernel or os information from cluster")

        try:
            info['revision'] = self.getRevision(cluster)
        except Exception as e:
            dlog.error("Unable to get the Revision from the cluster!")
            
        return info
    

    def getKernelAndOSVersion(self, cluster):
        dlog.info('Attempting to get the Kernel and os information from the Cluster')
        
        commandStr = 'lsb_release -a'
        stdout, stderr, status = self.runCommandOnQueen(cluster, commandStr)
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
                    stdout, stderr, status = self.runCommandOnQueen(cluster,cmd)
                    spNumber = stdout.split('=')[1].strip()
                    osVersion = osVersion + " SP " + spNumber

        commandStr = 'uname -r'
        stdout, stderr, status = self.runCommandOnQueen(cluster,commandStr)
        kernelVersion = stdout.strip()

        return kernelVersion, osVersion
    

    def getRevision(self, cluster):
        revision = self.revisionNumber
        ncli_cmd = "cat /home/beehive/bin/.build | grep 'BUILD_VERSION'"
        stdout, stderr, status = self.runCommandOnQueen(cluster, ncli_cmd)
        if status == 0:
            line = stdout.splitlines()[0]
            revision = line.split("-")[1]

        return revision
    
      
    def getLocalMeta(self):
        info = {}
        info['cluster_name'] = 'local'        
        info['release_name'] = self.projectName
        info['build_name'] = self.buildName
        info['tester'] = self.tester
        info['revision'] = self.revisionNumber
        info['build_number'] = self.buildNumber
        info['branch'] = self.branchName   
        return info

    def getTestMetadata(self, testInfo, status):
        testMeta = {}

        if 'LOCATION' in testInfo:
            testMeta['testcase_loc'] = testInfo['LOCATION']
        if 'creator' in testInfo:
            testMeta['creator'] = testInfo['CREATOR']

        if 'feature' in testInfo:
            testMeta['test_feature'] = testInfo['FEATURE']
        testMeta['priority'] = testInfo.get('PRIORITY', 3)

        if 'TYPE' in testInfo:
            testMeta['type'] = testInfo['TYPE']
        testMeta['run_id'] = testInfo['runId']
        testMeta['test_seq'] = testInfo['testId']

        testMeta['status'] = status

        if 'NAME' in testInfo:
            testMeta['testcase'] = testInfo['NAME']
        else:
            dlog.info("Test Name is required! Skipping the Test!")

        if 'OWNER' in testInfo:
            testMeta['owner'] = testInfo['OWNER']
        else:
            dlog.info("Test Owner is required! Skipping the Test!")

        if 'CATEGORY' in testInfo:
            testMeta['test_category'] = testInfo['CATEGORY']
        else:
            dlog.info("Test Category is required! Skipping the Test!")

        if 'COMPONENT' in testInfo:
            testMeta['test_component'] = testInfo['COMPONENT']
        else:
            dlog.info("Test Component is required! Skipping the Test!")

        if 'TIMEOUT' in testInfo:
            testMeta['timeout'] = testInfo['TIMEOUT']
        else:
            dlog.info("Test Timeout is required! Skipping the Test!")

        if 'NAME' not in testInfo or 'OWNER' not in testInfo or 'CATEGORY' not in testInfo \
            or 'COMPONENT' not in testInfo or 'TIMEOUT' not in testInfo:
            testMeta['status'] = "SKIP"

        return testMeta

    
    def getRemainingMeta(self, cluster, branchName):
        
        info = {}
        info['db_type'] = "Unknown"
        info['db_version'] = "Aster"
        info['build_info'] = ""

        try:
            info['build_info'] = self.getBuildInfo(cluster)
            if info['build_info'] is None:
                info['build_info'] = ""

            if branchName.lower() == "docker":
                info['db_type'] = "Docker"
                info['db_version'] = "Docker"
            else:
                info['db_type'] = "Hadoop"
                info['db_version'] = self.getHadoopVersion(cluster)
                if info['db_version'] == None:
                    dlog.info("The cluster is without Hadoop, change db_version to Aster")
                    info['db_type'] = "Classic"
                    info['db_version'] = "Aster"

            return info
        
        except Exception as e:
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc())

            return info


    def getBuildInfo(self, cluster):
        version = ""
        ncli_cmd = "cat /home/beehive/bin/.build | grep 'BUILD_VERSION'"
        stdout, stderr, status = self.runCommandOnQueen(cluster, ncli_cmd)
        if status == 0:
            line = stdout.splitlines()[0]
            version = line.split(" ")[1]
        return version
    
    
    def getHadoopVersion(self, cluster):
        hdversion = None
        hd_cmd = "hadoop version"
        stdout, stderr, status = self.runCommandOnQueen(cluster, hd_cmd)
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
    
    def runCommandOnQueen(self, cluster, cmd):
        stdout = None
        stderr = None
        status = 1
        cfgJson = self.clusterConfigDict[cluster]
        clusterCfg = cfgJson['cluster']
        try:
            queenConnect = None
            if "domain" in clusterCfg:
                domainName = clusterCfg['domain']
            if "queenNodes" in clusterCfg:
                queenNodes = clusterCfg['queenNodes']
            if "privateKey" in clusterCfg:
                privateKey = clusterCfg['privateKey']
            else:
                privateKey = None

            username = clusterCfg['username']
            password = clusterCfg['password']

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
        finally:
            if queenConnect:
                queenConnect.close()

        return stdout, stderr, status
    
    
    
    def printTestSet(self, testSetDict):
        for testset in testSetDict:
            for test in testSetDict[testset]:
                name = ''
                location = ''
                query = ''
                type = ''
                if 'NAME' in test:
                    name = test['NAME']
                if 'LOCATION' in test:
                    location = test['LOCATION']
                if 'QUERY' in test:
                    query = test['QUERY']
                if 'TYPE' in test:
                    type = test['TYPE']
                dlog.info('%s: %10s%10s%6s%15s'%(testset,name,location,type,query))
            
    def printSetupStates(self, setupDict):
        for cluster1 in setupDict:
            setupStates = setupDict[cluster1]
            for testset in setupStates:
                states = setupStates[testset]
                for key in states:
                    dlog.info('%s--%s: %s:%s'%(cluster1,testset,key,states[key]))


    def printTestResults(self, resultsDict):
        for testset in resultsDict:   
            for testresult in resultsDict[testset]:
                dlog.info('%15s%15s%10s%10s%20s%20s'%(testset, testresult[0], testresult[2], testresult[1],testresult[3], testresult[4]))
                
            
    def printFinalTestResults(self, finalTestResults):
        dlog.info('DartRunner Final Results!')
        dlog.info('%15s%15s%10s%10s%20s%20s'%('TESTSET', 'TESTNAME', 'STATUS', 'TOTALTIME','STARTTIME', 'ENDTIME'))
        for test in finalTestResults:
            testResult = test['testResults']
            self.printTestResults(testResult)
        self.dashBoardURL = 'http://dartdashboard.labs.teradata.com/report?run_id=%s'%self.runId
        dlog.info('Dart DashBoard URL: %s'%self.dashBoardURL)
    
    def verifyTestResults(self, finalTestResults, threshold):
        dlog.info('Checking if the pass rate is above the threshold %d!!' % threshold)
        #dlog.info('%15s%15s%10s%10s%20s%20s'%('TESTSET', 'TESTNAME', 'STATUS', 'TOTALTIME','STARTTIME', 'ENDTIME'))
        passCount = 0
        failCount = 0
        totalCount = 0
        for test in finalTestResults:
            testResultDict = test['testResults']
            #pprint(testResultDict)
            for testset in testResultDict:
                for testresult in testResultDict[testset]:
                    totalCount = totalCount + 1
                    status = testresult[2]
                    if status:
                        passCount = passCount + 1
                    else:
                        failCount = failCount + 1
        dlog.info('The number of tests Passed: %d'%passCount)
        dlog.info('The number of tests Failed: %d'%failCount)
        dlog.info('Current Threshold Value: %d'%threshold)
        if totalCount > 0:
            percentagePass = int((float(passCount)/totalCount)*100)
            dlog.info('Percentage Pass: %d'%percentagePass)
            if percentagePass > threshold:
                dlog.info('The rate of pass is greater than the threshold!')
                return True 
            else:
                dlog.info('The rate of pass is less than the threshold! The Stage will fail!!')
                return False               
        return True
            
    def getTestRunFiles(self, runFile):
        testRunFiles = []
        for (dirpath, dirnames, filenames) in walk(runFile):
            fileList = []
            for filename in filenames:
                filenameFull = os.path.join(dirpath, filename)
                fileList.append(filenameFull)
            testRunFiles.extend(fileList)
        testRunFilesOnly = []
        for testRunFile in testRunFiles:
            if os.stat(testRunFile).st_size != 0 and '.tst' in testRunFile:
                testRunFilesOnly.append(testRunFile)

        return testRunFilesOnly
    
       
if __name__ == "__main__":
    def printUsage():
        usage = '''
        Usage Example:
        DartRunner.py -c clusterList -t testRunFile
        DartRunner.py -h
        DartRunner.py -c clusterList -t testRunFile [-i installFile] [-k checkHealthFile] [-p projectName] [-b buildName] [-n ] [-u] [--tester username]
        Example:
        DartRunner.py -c "cdh253,cdh254,cdh255" -t ffr2nightly.tst -k checkHealthffr2.tst
        
        If the results are not required to be uploaded into the Web use -n option
        Example:
        DartRunner.py -c "cdh253,cdh254,cdh255" -t ffr2nightly.tst -n
        
        If the results should be uploaded into TestLink, use -u option
        Example:
        DartRunner.py -c "cdh253,cdh254,cdh255" -t ffr2nightly.tst -u
        
        Example:
        To Load the results into the DashBoard ( Public/Private )
        DartRunner.py -c "cdh253,cdh254" -t ffr2nightly.tst -l 'Public'
        
        '''
        print (usage)
        
    try:
        parser = argparse.ArgumentParser(description='DartRunner - Schedule a list of tests on multiple clusters')
        parser.add_argument('-c', '--clusterList',required=False, default=None, help='List of Clusters: Example "cdh251,cdh253"')
        parser.add_argument('-t', '--testRunFile',required=False, default=None, help='TestRunFile which contains the list of tests')
        parser.add_argument('-i', '--installFile',required=False, default=None, help='Install RunFile which contains the install test')
        parser.add_argument('-k', '--checkHealthFile',required=False, default=None, help='CheckHealth RunFile which contains the Check Health tests')
        parser.add_argument('--releaseName',required=False, default='',  help='Release Name')
        parser.add_argument('--keywords',required=False, default='',  help='Keywords')
        parser.add_argument('--comments',required=False, default='',  help='Comments')
        parser.add_argument('-p', '--projectName',required=False, default='Private', help='Project Name or Release Name')
        parser.add_argument('-b', '--buildName',required=False, default='Private',  help='Build Name')
        parser.add_argument('--buildNumber',required=False, default='',  help='Build Number')
        parser.add_argument('--branchName',required=False, default='',  help='Branch Name')  
        parser.add_argument('--revisionNumber',required=False, default='',  help='Revision Number')
        parser.add_argument('-u', '--uploadTestLink',required=False, default=False, action='store_true', help='Upload test results to TestLink')
        parser.add_argument('--tester',required=False, default=None, help='The User who is running the tests')
        parser.add_argument('--testPlan', required=False, default=None, help='The User who is running the tests')
        parser.add_argument('--timeoutScale',required=False, default=1, help='This value will increase the timeout value for the entire execution')
        parser.add_argument('--buildUrl', required=False, default=None, help='Use build url to get build number and revision number')
        parser.add_argument('--noDownload', required=False, default=False, help='Use noDownload if you do not like to download the rpms')
        parser.add_argument('--buildLoc', required=False, default=None, help='Use build Loc to upload into Queen')
        parser.add_argument('--runLabel', required=False, default='', help='Add the run label')
        parser.add_argument('--testTag', required=False, default=None, help='Use the test Tag option to discover tests and run tests selectively')
        parser.add_argument('--rerunFailedTests', required=False, default=None,  help='Rerun failed tests with a specific Run ID')
        parser.add_argument('--disableNotify', required=False, default=False, action='store_true', help='Disable sending email if test failure')
        parser.add_argument('-l', '--load',required=False, default='noLoad', help='Load the results to the DashBoard and Database for Reports. Public/Private')
        parser.add_argument('--retry',required=False, default=0, help='The number of times to retry/re-run a Failed or Aborted Test')
        parser.add_argument('--threshold',required=False, default=0, help='DartRunner will return as Failure if the passrate percentage is less the threshold!'),
        parser.add_argument('--noTestLog', required=False, default=None, action='store_true', help='Disable Test Logging on the Console'),
        parser.add_argument('--usage', required=False, default=None, action='store_true', help='Show usage of DartRunner')

        args = parser.parse_args()

        if args.usage:
            printUsage()
            sys.exit(2)

        if not args.clusterList:
            print "Cluster config file is required"
            printUsage()
            sys.exit(2)

        if not args.testRunFile:
            print "Test Run file is required"
            printUsage()
            sys.exit(2)

        metaDict = {'projectName' : args.projectName,
                    'buildName' : args.buildName,
                    'tester' : args.tester,
                    'uploadTL' : args.uploadTestLink,
                    'installTest' : args.installFile,
                    'checkHealthTest' : args.checkHealthFile,
                    'buildNumber' : args.buildNumber, 
                    'branchName' : args.branchName, 
                    'revisionNumber' : args.revisionNumber,
                    'timeScale' : args.timeoutScale, 
                    'testPlan': args.testPlan, 
                    'buildUrl': args.buildUrl,
                    'testTag' : args.testTag,
                    'runLabel': args.runLabel,
                    'buildLoc' : args.buildLoc,
                    'rerunFailedTests' : args.rerunFailedTests,
                    'disableNotify' : args.disableNotify,
                    'noDownload' : args.noDownload,
                    'load' : args.load,
                    'releaseName' : args.releaseName,
                    'keywords' : args.keywords,
                    'retry' : args.retry,
                    'threshold' : args.threshold,
                    'noTestLog' : args.noTestLog,
                    'comments' : args.comments
                    }
        dlog.info(metaDict)
        print(args.clusterList)
        print(args.testRunFile)
        loadDatabase = False
        if args.load == 'Public' or args.load == 'Private':
            loadDatabase = True
            

        dartRunner = DartRunner(metaDict, args.clusterList, args.testRunFile, loadDatabase = loadDatabase)
        dartRunner.main()
        
    except Exception as e:
        print(e)
        print(sys.exc_info())
        print(traceback.format_exc())
        printUsage()
        sys.exit(2)
        
