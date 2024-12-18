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

class SqlRun(TestBase):
 
    def run(self):
        '''
        @summary This function will be called by Dart
        '''
        if 'QUERY' in self.testParams:
            queryFile = self.testParams['QUERY']
        else:
            dlog.error('QUERY File is not defined in the input file!')
            return False
        if 'EXPECTEDOUT' in self.testParams:
            expectedOutFile = self.testParams['EXPECTEDOUT']
        else:
            dlog.error('EXPECTEDOUT File is not defined in the input file!')
            return False
        if 'USER' in self.testParams:
            user = self.testParams['USER']
        else:
            dlog.info('USER is not defined in the input file! Using the default beehive user')
            user = "beehive"
        if 'PASSWORD' in self.testParams:
            password = self.testParams['PASSWORD']
        else:
            dlog.info('PASSWORD is not defined in the input file! Using the default beehive password')
            password = "beehive"
        
        actParams = None
        if 'ACTPARAMS' in self.testParams:
            actParams = self.testParams['ACTPARAMS']
        
        if 'DATABASE' in self.testParams:
            database = self.testParams['DATABASE']

        elif self.defaultDb != None:
            database = self.defaultDb
        else:
            dlog.info('DATABASE is not defined in the input file! Using the default database')
            database = None

        diffParams = None
        if 'DIFFPARAMS' in self.testParams:
            diffParams = self.testParams['DIFFPARAMS']
        
        
        return self.excSqlFileAndCompareOutput(queryFile, expectedOutFile, user, password, database, \
                                               actParams, diffParams)


