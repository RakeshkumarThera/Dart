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

from lib.TestBase import TestBase
from lib.Dlog import dlog
from pprint import pprint
class Cli(TestBase):
 
    def run(self):
        '''
        @summary This function will be called by Dart
        def installSqlMR(self, inputFile, fileAlias=None,  user="beehive", password = "beehive", database = None):
        
        '''
        
        if 'COMMAND' in self.testParams:
            command = self.testParams['COMMAND']
        else:
            dlog.error('COMMAND is not defined in the input file!')
            return False
        passStr = None
        if 'PASS' in self.testParams:
            passStr = self.testParams['PASS']
        failStr = None
        if 'FAIL' in self.testParams:
            failStr = self.testParams['FAIL']
           
        arguments = list()
        for arg in self.testParams.keys():
            if arg.startswith('ARG') and not arg.startswith('ARGMIX'):
                arguments.append(self.testParams[arg])
        argumentStr = ''
        for item in arguments:
            argumentStr = argumentStr + ' ' + item
        if 'ARGMIX' in self.testParams:
            argMixStr = self.testParams['ARGMIX']
            argMix = argMixStr.split(',')
            returnStatus = True
            returnStatusOut = True
            for arg1 in argMix:
                commandStr = 'source /home/beehive/config/asterenv.sh; ' + command + ' ' + argumentStr + ' ' + arg1
                stdout, stderr, status = self.queenExecCommand(commandStr, timeout=300)
                dlog.info(stdout + stderr)
                if status != 0:
                    dlog.error("Command Failed!")
                    returnStatus = False
                #Check for the Pass and Fail String if defined.
                if passStr != None:
                    passArry = passStr.split(',')
                    for item in passArry:
                        if not ((item in stdout) or (item in stderr)):
                            returnStatusOut = False
                if failStr != None:
                    failArry = failStr.split(',')
                    for item in failArry:
                        if ((item in stdout) or (item in stderr)):
                            returnStatusOut = False
            if not returnStatus:
                dlog.error('The test output did not meet the PASS or FAIL criteria!')
                return returnStatus
            if not returnStatusOut:
                dlog.error('The test output did not meet the PASS or FAIL criteria!')
                return returnStatusOut
            return returnStatus
        else:
            commandStr = 'source /home/beehive/config/asterenv.sh; ' + command + ' ' + argumentStr
            stdout, stderr, status = self.queenExecCommand(commandStr, timeout=300)
            dlog.info(stdout + stderr)
            if status != 0:
                dlog.error("Command Failed!")
                return False
            #Check for the Pass and Fail String if defined.
            returnStatus = True
            if passStr != None:
                passArry = passStr.split(',')
                for item in passArry:
                    if not ((item in stdout) or (item in stderr)):
                        returnStatus = False
            if failStr != None:
                failArry = failStr.split(',')
                for item in failArry:
                    if ((item in stdout) or (item in stderr)):
                        returnStatus = False
            if not returnStatus:
                dlog.error('The test output did not meet the PASS or FAIL criteria!')
                return returnStatus
                        
                        

        return True

