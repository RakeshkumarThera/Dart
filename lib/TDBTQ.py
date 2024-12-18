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
import os

class TDBTQ(TestBase):
 
    def run(self):
        '''
        @summary This function will be called by Dart
        
        '''

        if 'QUERY' in self.testParams:
            queryFile = self.testParams['QUERY']
            queryFileAbs = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', queryFile)
            if os.path.isfile(queryFileAbs):
                dlog.info('Using the Query File %s' % queryFileAbs)
            else:          
                queryStr = queryFile
                queryFile = None
        else:
            dlog.error('QUERY is not defined in the input file!')
            return False
        
        validationQueryFile = None
        status = False
        
        if 'VALIDATIONQUERY' in self.testParams:
            validationQueryFile = self.testParams['VALIDATIONQUERY']
            validationQueryFileAbs = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', validationQueryFile)
            if os.path.isfile(validationQueryFileAbs):
                dlog.info('Using the Validation Query File %s' % validationQueryFileAbs)
            else:
                dlog.info('The Validation Query File does not exist %s' % validationQueryFileAbs)
                return False
            if 'VALIDATEON' in self.testParams:
                validateOn = self.testParams['VALIDATEON']
            else:
                validateOn = 'TD'
            
        if 'USER' in self.testParams:
            user = self.testParams['USER']
        else:
            dlog.info('USER is not defined in the input file! Using the default  testuser')
            user = "testuser"
        
        if 'DIFF' in self.testParams:
            if self.testParams['DIFF'] == "True":
                diff = True
            else:
                diff = False
            
        else:
            dlog.info('DIFF is not defined in the input file! Using the default as False')
            diff = False
              
        if 'PASSWORD' in self.testParams:
            password = self.testParams['PASSWORD']
        else:
            dlog.info('PASSWORD is not defined in the input file! Using the default testuser password')
            password = "testuser"
        
        if 'EXPECTEDOUT' in self.testParams:
            expectedOut = self.testParams['EXPECTEDOUT']
        elif not validationQueryFile:
            dlog.error('EXPECTEDOUT is not defined in the testrun File!')
            return False
        
        bteqParams = None
        if 'BTEQPARAMS' in self.testParams:
            bteqParams = self.testParams['BTEQPARAMS']
        
        diffParams = None
        if 'DIFFPARAMS' in self.testParams:
            diffParams = self.testParams['DIFFPARAMS']
            
        if 'DATABASE' in self.testParams:
            database = self.testParams['DATABASE']
        else:
            dlog.info('DATABASE is not defined in the input file! Using the default database')
            database = None

        if 'TDSETUPFILE' in self.testParams:
            setupDict = self.testParams['TDSETUPFILE']
            for TDSetupFile in setupDict:
                TDSetupFileAbs = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', TDSetupFile)
                if os.path.isfile(TDSetupFileAbs):
                    dlog.info('Using the Setup File %s' % TDSetupFileAbs)
                    status, out, contents = self.excSqlFileOnTD(inputFile=TDSetupFileAbs, user=user, password=password, database=database, \
                                                        bteqParams=bteqParams, diff=diff, diffParams=diffParams)
                    dlog.info(out)
                    dlog.info(contents)
                else:
                   dlog.error('Setup file given is not present.')
                   return False

           
        if validationQueryFile:
            status, stdout, contents, stdoutVal, contentsVal = self.excSqlFileWithValidationOnTD(inputFile=queryFile, validationFile=validationQueryFile, validateOn=validateOn, \
                                user=user, password=password, database=database, bteqParams=bteqParams,\
                                diffParams=diffParams)
            dlog.info(stdout)
            dlog.info(contents)
            dlog.info(stdoutVal)
            dlog.info(contentsVal)
            
        elif queryFile:
            status, out, contents = self.excSqlFileOnTD(inputFile=queryFile, user=user, password=password, database=database, \
                                                        expectedOut=expectedOut, bteqParams=bteqParams, diff=diff, diffParams=diffParams)
            
            if not status:
               dlog.info('Test Failed')
            dlog.info(out)
            dlog.info(contents)
        elif queryStr:
            status, out, contents = self.excSqlOnTD(inputSql=queryStr, user=user, password=password, database=database, \
                                                    expectedOut=expectedOut, bteqParams=bteqParams,diff=diff, diffParams=diffParams)
            dlog.info(out)
            dlog.info(contents)
       
        #return the status of the test after executing cleanup if provided in testset file. 
        if 'TDCLEANUPFILE' in self.testParams:
            TDCleanupFile = self.testParams['TDCLEANUPFILE']
            TDCleanupFileAbs = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', TDCleanupFile)
            if os.path.isfile(TDCleanupFileAbs):
                dlog.info('Using the Cleanup File %s' % TDCleanupFileAbs)
                status1, out, contents = self.excSqlFileOnTD(inputFile=TDCleanupFileAbs, user=user, password=password, database=database, \
                                                        bteqParams=bteqParams, diff=diff, diffParams=diffParams)
                dlog.info(out)
                dlog.info(contents)

                #if cleanup failed. Mark the test as failed.If clean is done correctly it will return status of previous execSql calls.
                if not status1:
                    dlog.info("Cleanup failed")
                    return False 
                
       	    else:
               dlog.error('Cleanup file given is not present.')
               return False
        
        return status

