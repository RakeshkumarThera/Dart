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
# DESCRIPTION: Class to setup and run TeradataAsterR tests

import re
import shutil
import os
import codecs
from collections import OrderedDict
from Sftp import Sftp
from SshConnect import SshConnect

from lib.TestBase import TestBase
from lib.Dlog import dlog
from testsrc.clients.common.clientConnection import clientConnection

localInputPath = os.path.join(os.getcwd(), "log/Ecosystem/tdplyr/input")
localOutputPath = os.path.join(os.getcwd(), "log/Ecosystem/tdplyr/output")

# Use the template input script to call individual R tests scripts
inputfileTemplate = "testsrc/EcoSystems/tdplyr/input_script.template"


class TeradataR(TestBase):

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
            if 'RclientLocation' in self.clientDict:
                self.R_CLIENT_LOC = self.clientDict['RclientLocation']
            if 'ClientPkgLocation' in self.clientDict:
                self.CLNT_PKG_LOCATION = self.clientDict['ClientPkgLocation']
            self.DRIVER_MANAGER = "unixODBC"
            if 'DriverManager' in self.clientDict:
                self.DRIVER_MANAGER = self.clientDict['DriverManager']

            #By default run is always remote.
            self.RunLocal = False
            if 'LocalClient' in self.clientDict:
                self.RunLocal = self.clientDict['LocalClient']


        self.conn = clientConnection()
        self.SftpConn = Sftp(self.ClientIP, self.ClientUsername, self.ClientPassword)


    def copyFilesToClient(self, source, target):
        self.SftpConn.connect()
        status = self.SftpConn.sftp.put(source, target)
        if status == 0 :
          dlog.info("Failed to copy %s on client" % source)
          return False
        dlog.info("Successfully copied %s on client" % source) 
        self.SftpConn.close()
        return True

    def runSQLFileonTD(self, filename, username, password, database):
        status, out, contents = self.excSqlFileOnTD(filename, username, password, database)
        dlog.info(out)
        dlog.info(contents)
        return status
           
    #execute R scripts on clients and get status
    def execTeradataRBatch(self,
                           testName,
                           database,
                           dsn,
                           username,
                           password,
                           inputRScript
                           ):


        ClientrPath = self.R_CLIENT_LOC
        
        InputLoc = os.path.dirname(inputRScript)
        
        remoteInputLoc = "testdir"
        remoteOutputLoc = "testdir/output"

        if not os.path.exists(localInputPath):
            os.makedirs(localInputPath)

        if not os.path.exists(localOutputPath):
            os.makedirs(localOutputPath)
        
        inputfilename = inputRScript.split("/")[-1]
        
        TempFile = os.path.join(localInputPath, "temp." + os.path.basename(inputRScript))
        tempInputRScript = os.path.join(localInputPath, os.path.basename(inputRScript))

        #create the input script for local runs
        if self.RunLocal == 'True':
           inputScriptPath = os.path.join(localInputPath , os.path.basename(inputRScript))
           dlog.info("For local client run input script location is  {}".format(inputScriptPath))

        else:
            inputScriptPath = os.path.join(remoteInputLoc, inputfilename)
            dlog.info("For remote client run input script location is  {}".format(inputScriptPath))

        TempScript = os.path.basename(TempFile)

        fp1 = codecs.open(inputfileTemplate, "r", "utf-8")
        fp2 = codecs.open(TempFile, "w", "utf-8")

        #create input test file using template and replace the test .R script path.
        for line in fp1:
            fp2.write(line.replace("REPLACE_FILEPATH", inputScriptPath))
        fp1.close()
        fp2.close()

        fp1 = codecs.open(inputRScript, "r", "utf-8")
        fp2 = codecs.open(tempInputRScript, "w", "utf-8")

        #Change the DSN from the temporary created input script with the one specified in local.cfg
        for line in fp1:
            fp2.write(line.replace("REPLACE_DSN", self.DSN))
        fp1.close()
        fp2.close()

        generatedROutputFile =  inputfilename + ".generated"
        if os.path.exists(os.path.join(localOutputPath,generatedROutputFile)):
            os.remove(os.path.join(localOutputPath,generatedROutputFile))

        R_Client_Script = ClientrPath + "/R CMD BATCH --no-save {} {}".format("{}/{}".format(remoteInputLoc,TempScript),
                                                    "{}/{}".format(remoteOutputLoc,generatedROutputFile))

        if not self.RunLocal:
            # Run R script on Client
            dlog.info("The Connection to client is Initiated")
            self.clientsConnect = SshConnect(self.ClientIP, self.ClientUsername, self.ClientPassword)
            self.clientsConnect.connect()
            dlog.info("The Connection to client has been established")

            clcmd = "mkdir -p testdir/output"
            stdout, stderr, status =  self.clientsConnect.execCommand(clcmd, timeout=180)

            # Copy input test_file API script to Client
            dlog.info("Copy test_file API script on Client")
            self.copyFilesToClient(TempFile, os.path.join(remoteInputLoc,TempScript))

            # Copy input R script to Client
            dlog.info("Copy input R script on Client")
            self.copyFilesToClient(tempInputRScript, os.path.join(remoteInputLoc,inputfilename))
        
            dlog.info("Executing command {} on {} Client".format(R_Client_Script,self.clientDict["ClientOS"].upper()))
            stdout, stderr, status =  self.clientsConnect.execCommand(R_Client_Script, timeout=3600)
        
            if status != 0:
                dlog.error("Failed to run R command %s: " % R_Client_Script)
                dlog.error(stdout + stderr)

            status = self.conn.getFile(self.ClientIP, self.ClientUsername, self.ClientPassword, remoteOutputLoc, localOutputPath)

        #if the run is local, just execute R locally.
        else:

            R_Client_Script = ClientrPath + "/R CMD BATCH --no-save {} {}/{}".format(TempFile,localOutputPath,generatedROutputFile)
            dlog.info("Executing local command {} ".format(R_Client_Script))
            status, stdout, stderr = self.execCmdLocal(R_Client_Script)
            if status != 0:
                dlog.error("Failed to run R command %s: " % R_Client_Script)
                dlog.error(stdout + stderr)

        if not os.path.exists(os.path.join(localOutputPath,generatedROutputFile)):
            dlog.error("File doesn't exist: %s" % os.path.join(localOutputPath,generatedROutputFile))
            return False
            
        with open(os.path.join(localOutputPath,generatedROutputFile)) as f1:
            filecontents = f1.read()
            contents = filecontents.splitlines()
            status = True
            for line in contents:
               if line.find('Failed:') > -1:
                  if int(line.split(':')[1]) > 0:
                     status = False
                     dlog.info("Number of test failures are non zero. Mark the test as failed")

               if line.find('Execution halted') > -1:
                   status = False
                   dlog.info("Tests execution haulted. Mark the test as failed.")

               if line.find("Too many failures") > -1:
                   status = False
                   dlog.info("Tests execution haulted. Mark the test as failed.")

               if not status:
                   dlog.info("Test failed. Contents of generated output file are - \n")
                   dlog.info(filecontents + "\n")
                   dlog.info("Generated Output file location : {}".format(os.path.join(localOutputPath, generatedROutputFile)))
                   return False

            else:
               print ("Test Passed!!")
               return True
  

    def run(self):
        """
        Run R Tests
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
            database= "alice"
                        
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
                          status  = self.runSQLFileonTD(cleanupFile, username, password, database)
                else:
                    dlog.info(cleanupSqlFiles)
                    status  = self.runSQLFileonTD(cleanupSqlFiles, username, password, database)

            #setup up files can be a single file as string or a list of multiple files
            setupFiles = self.testParams['TESTSETUP']
            if type(setupFiles) is list:
                for setupFile in setupFiles:          
                    status  = self.runSQLFileonTD(setupFile, username, password, database)
                    if not status:
                        dlog.error('Setup failed.')
                        return False 
            else:
                status  = self.runSQLFileonTD(setupFiles, username, password, database)
                if not status:
                    dlog.error('Setup failed.')
                    return False       

        #if the TYPE is TeradataR, execute the scripts using R console
        if self.testParams['TYPE']=="TeradataR":   
            if 'INPUTRSCRIPT' in self.testParams:
                inputRScript = self.testParams['INPUTRSCRIPT']
                if "clients" in self.cfgJson:
                    status =  self.execTeradataRBatch(self.testParams["NAME"], database,
                                                          self.DSN, self.ClientUsername, self.ClientPassword,
                                                          inputRScript)
                    if not status:
                       dlog.error("Test failed")

        #Run cleanup only when current test is not of type SETUP=True
        if 'CLEANUPSETUP' in self.testParams and not commonSetup:
            dlog.info("Perform cleanup of the test")
            cleanupSqlFiles = self.testParams['CLEANUPSETUP']

            if type(cleanupSqlFiles) is list:
                for cleanupFile in cleanupSqlFiles:
                    status2  = self.runSQLFileonTD(cleanupFile, username, password, database)
            else:
                dlog.info(cleanupSqlFiles)
                status2  = self.runSQLFileonTD(cleanupSqlFiles, username, password, database)

            if not status2:
                dlog.error('Cleanup did not executed properly.')
                return False

        return status
