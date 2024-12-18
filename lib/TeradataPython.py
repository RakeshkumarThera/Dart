# -*- coding: utf-8 -*-
#coding:utf-8
#
# Unpublished work.
# Copyright (c) 2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: Abhinav.Sahu@teradata.com
# Secondary Owner: Trupti.Purohit@teradata.com
#
# DESCRIPTION: Class to run teradataml tests
#
# Sample local.cfg (must be present under config dir) contents:
# {
# "clients": {
#      "ClientIP" : "153.64.29.84",
#      "ClientUsername" : "Administrator",
#      "ClientPassword" : "TCAMPass123",
#      "PyTestLocation" : "/cygdrive/c/ProgramData/Anaconda3/Scripts",
#      "ClientOS" : "windows64",
#      "ODBCDSN" : "TeradataDSN",
#      "TD_USER": "alice",
#      "TD_PASS": "alice"
#   }
# }
#


import re
import shutil
import os
import codecs
import subprocess
from collections import OrderedDict
from Sftp import Sftp
from SshConnect import SshConnect

from lib.TestBase import TestBase
from lib.Dlog import dlog
from testsrc.clients.common.clientConnection import clientConnection

localInputPath = os.path.join(os.getcwd(), "log/Ecosystem/TeradataPython/input")
localOutputPath = os.path.join(os.getcwd(), "log/Ecosystem/TeradataPython/output")

# Use the below config template input script to keep your target TD
configfileTemplate = "testsrc/EcoSystems/TeradataPython/td_config.cfg"
testconfig = "testsrc/EcoSystems/TeradataPython/testconfigure.py"


class TeradataPython(TestBase):

    def __init__(self, cfgJson, testParams=None):
        TestBase.__init__(self, cfgJson, testParams)
        if "clients" in self.cfgJson:
            self.clientDict = cfgJson['clients']
            if "ClientIP" in self.clientDict:
                self.ClientIP = self.clientDict['ClientIP']
            if "ClientUsername" in self.clientDict:
                self.ClientUsername = self.clientDict['ClientUsername']
            if "ClientPassword" in self.clientDict:
                self.ClientPassword = self.clientDict['ClientPassword']
            if "ODBCDSN" in self.clientDict:
                self.DSN = self.clientDict['ODBCDSN']
            self.PyTest = self.cfgJson['clients']['PyTestLocation']
            self.OS_NAME = self.cfgJson['clients']['ClientOS']
            self.TD_USER = self.cfgJson['clients']['TD_USER']
            self.TD_PASS = self.cfgJson['clients']['TD_PASS']
            
            self.TDPID = self.cfgJson['tdCluster']['tdMasterNode']
            #By default run is always remote.
            self.RunLocal = False
            if 'LocalClient' in self.clientDict:
                self.RunLocal = self.clientDict['LocalClient']


        self.conn = clientConnection()
        self.SftpConn = Sftp(self.ClientIP, self.ClientUsername, self.ClientPassword)
        self.clientsConnect = SshConnect(self.ClientIP, self.ClientUsername, self.ClientPassword)


    def copyFilesToClient(self, source, target):
        self.SftpConn.connect()
        status = self.SftpConn.sftp.put(source, target)
        if status == 0 :
          dlog.info("Failed to copy {} on client - {}".format(source, target))
          return False
        dlog.info("Successfully copied {} on client - {}".format(source, target)) 
        self.SftpConn.close()
        return True
     
    def changeTDPID(self):
        out_file = open('tmp/td_config', "w")
        sed_cmd = '/host/ c\"host": "{}",'.format(self.TDPID)
        status = subprocess.call(['sed', sed_cmd, configfileTemplate], stdout=out_file)
        if status!=0:
            dlog.error('Replace failed.')
            return False
        dlog.info("Replaced td host in {} to {}".format(configfileTemplate, self.TDPID))
    
    #Execute Python test scripts and get status
    def execTeradataPythonBatch(self,
                                testName,
                                database,
                                dsn,
                                username,
                                password,
                                inputPyScript
                                ):


        InputLoc = os.path.dirname(inputPyScript)
        
        remoteInputLoc = "testPydir"
        remoteOutputLoc = "testPydir/output"

        if not os.path.exists(localInputPath):
            os.makedirs(localInputPath)

        if not os.path.exists(localOutputPath):
            os.makedirs(localOutputPath)
        
        configfilename = configfileTemplate.split("/")[-1]
        testconfigname = testconfig.split("/")[-1]
        inputfilename = inputPyScript.split("/")[-1]

        #create the input script for local runs
        if self.RunLocal == 'True':
           inputScriptPath = os.path.join(localInputPath , os.path.basename(inputPyScript))
           dlog.info("For local client run input script location is {}".format(inputScriptPath))

        else:
            inputScriptPath = os.path.join(remoteInputLoc, inputfilename)
            dlog.info("For remote client run input script location is {}".format(inputScriptPath))

        generatedPyOutputFile =  inputfilename + ".generated"
        if os.path.exists(os.path.join(localOutputPath,generatedPyOutputFile)):
            os.remove(os.path.join(localOutputPath,generatedPyOutputFile))

        Py_Client_Script = self.PyTest + "/pytest {} > {}".format(inputScriptPath, os.path.join(remoteOutputLoc,generatedPyOutputFile))

        # Run Pytest scripts on Client (remote)
        if not self.RunLocal:
            dlog.info("The Connection to client is Initiated")
            self.clientsConnect = SshConnect(self.ClientIP, self.ClientUsername, self.ClientPassword)
            self.clientsConnect.connect()
            dlog.info("The Connection to client has been established")

            clcmd = "mkdir -p testPydir/output"
            stdout, stderr, status =  self.clientsConnect.execCommand(clcmd, timeout=180)
            if status != 0:
                dlog.error("Failed to create testPydir on client")
                return False

            # Copy config files to Client
            dlog.info("Copy TD_CONFIG on Client")
            self.copyFilesToClient('tmp/td_config', os.path.join(remoteInputLoc,configfilename))
            dlog.info("Copy Test_CONFIG on Client")
            self.copyFilesToClient(testconfig, os.path.join(remoteInputLoc,testconfigname))

            # Copy input Py script to Client
            dlog.info("Copy input Py test script on Client")
            self.copyFilesToClient(inputPyScript, os.path.join(remoteInputLoc,inputfilename))
        
            dlog.info("Executing command {} on {} Client".format(Py_Client_Script, self.clientDict["ClientOS"].upper()))
            stdout, stderr, status =  self.clientsConnect.execCommand(Py_Client_Script, timeout=3600)
        
            if status != 0:
                dlog.error("Failed to run Py command %s: " % Py_Client_Script)
                dlog.error(stdout + stderr)
                return False
            status = self.conn.getFile(self.ClientIP, self.ClientUsername, self.ClientPassword, remoteOutputLoc, localOutputPath)

        #if the run is local, just execute Pytest locally.
        else:
            Py_Client_Script = "pytest {} > {}".format(inputScriptPath, os.path.join(localOutputPath,generatedPyOutputFile))
            dlog.info("Executing local command {} ".format(Py_Client_Script))
            status, stdout, stderr = self.execCmdLocal(Py_Client_Script)
            if status != 0:
                dlog.error("Failed to run Py command %s: " % Py_Client_Script)
                dlog.error(stdout + stderr)
                return False

        if not os.path.exists(os.path.join(localOutputPath,generatedPyOutputFile)):
            dlog.error("File doesn't exist: %s" % os.path.join(localOutputPath,generatedPyOutputFile))
            return False
            
        with open(os.path.join(localOutputPath,generatedPyOutputFile)) as f1:
            contents = f1.read().splitlines()
            dlog.info(contents)
            status = True
            for line in contents:
               if line.find('failed:') > -1:
                   status = False
                   dlog.info("Number of test failures are non zero. Mark the test as failed")
               if not status:
                   print contents
                   dlog.info("Test failed. For more details refer {}".format(os.path.join(localOutputPath, generatedPyOutputFile)))
                   return False

            else:
               print ("Test Passed!!")
               return True
  
    
    def run(self):
        """
        Run Python Tests
        """
        status = True
        commonSetup = False
        
        if 'USER' in self.testParams:
            username = self.testParams['USER']
        else:
            dlog.info('USER is not defined in the input file! Using the default user')
            username = "alice"
        if 'PASSWORD' in self.testParams:
            password = self.testParams['PASSWORD']
        else:
            dlog.info('PASSWORD is not defined in the input file! Using the default password')
            password = "alice"           
        if 'DATABASE' in self.testParams:
            database = self.testParams['DATABASE']
        else:
            dlog.info('DATABASE is not defined in the input file! Using the default database')
            database = "alice"
        
        #Below function will change TD host in td_config.cfg file taking value from <cluster>.cfg                
        self.changeTDPID()
        
        if 'TESTSETUP' in self.testParams:

            if 'SETUP' in self.testParams:
                if self.testParams['SETUP'] == 'True':
                   commonSetup = True
                   dlog.info("Local setup is TRUE")

            #This is cleanup just to make sure no existing tables affect the current run.
            #If the database is clean this call will return error, we wll ignore the return
            #status of this call here.
            if 'CLEANUPSETUP' in self.testParams:
                cleanupSqlFiles = self.testParams['CLEANUPSETUP']

                #clean up files can be a single file as string or a list of multiple files
                if type(cleanupSqlFiles) is list:
                    for cleanupFile in cleanupSqlFiles:
                          dlog.info(cleanupFile)
                          status  = self.excSqlFileOnTD(cleanupFile, username, password, database)
                else:
                    dlog.info(cleanupSqlFiles)
                    status  = self.excSqlFileOnTD(cleanupSqlFiles, username, password, database)

            #setup up files can be a single file as string or a list of multiple files
            setupFiles = self.testParams['TESTSETUP']
            if type(setupFiles) is list:
                for setupFile in setupFiles:          
                    status  = self.excSqlFileOnTD(setupFile, username, password, database)
                    if not status:
                        dlog.error('Setup failed.')
                        return False 
            else:
                status  = self.excSqlFileOnTD(setupFiles, username, password, database)
                if not status:
                    dlog.error('Setup failed.')
                    return False       

        #Execute the test scripts using Pytest    
        if 'INPUTPYSCRIPT' in self.testParams:
            inputPyScript = self.testParams['INPUTPYSCRIPT']
            if "clients" in self.cfgJson:
                status =  self.execTeradataPythonBatch(self.testParams["NAME"], database,
                                                      self.DSN, self.ClientUsername, self.ClientPassword,
                                                      inputPyScript)
                if not status:
                   dlog.error("Test failed")

        #Run cleanup only when current test is not of type SETUP=True
        if 'CLEANUPSETUP' in self.testParams and not commonSetup:
            dlog.info("Perform cleanup of the test")
            cleanupSqlFiles = self.testParams['CLEANUPSETUP']

            if type(cleanupSqlFiles) is list:
                for cleanupFile in cleanupSqlFiles:
                    status2  = self.excSqlFileOnTD(cleanupFile, username, password, database)
            else:
                dlog.info(cleanupSqlFiles)
                status2  = self.excSqlFileOnTD(cleanupSqlFiles, username, password, database)

            if not status2:
                dlog.error('Cleanup did not executed properly.')
                return False
                
        return status
