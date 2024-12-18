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

class SqlMR(TestBase):
 
    def run(self):
        '''
        @summary This function will be called by Dart
        def installSqlMR(self, inputFile, fileAlias=None,  user="beehive", password = "beehive", database = None):
        
        '''
        
        if 'COMMAND' in self.testParams:
            command = self.testParams['COMMAND']
        else:
            command = 'install'
        
        if 'FILE' in self.testParams:
            installFile = self.testParams['FILE']
        else:
            if command == 'install':
                dlog.error('SQLMR File is not defined in the input file!')
                return False
    
        
            
        fileAlias = None
        if 'FILEALIAS' in self.testParams:
            fileAlias = self.testParams['FILEALIAS']
        else:
            if command == 'remove':
                dlog.error('SQLMR fileAlias is not defined in the input file!')
                return False
                
        
        if 'USER' in self.testParams:
            user = self.testParams['USER']
        else:
            dlog.info('USER is not defined in the input file! Using the default beehive user')
            user = "beehive"
        if 'PASSWORD' in self.testParams:
            password = self.testParams['PASSWORD']
        else:
            dlog.info('PASSWORD is not defined in the input file! Using the default beehive user')
            password = "beehive"
        
        if 'DATABASE' in self.testParams:
            database = self.testParams['DATABASE']
        else:
            dlog.info('DATABASE is not defined in the input file! Using the default beehive user')
            database = None
        
        if command == 'remove':
            return self.removeSqlMR(fileAlias, user, password, database)
        elif command == 'install':
            return self.installSqlMR(installFile, fileAlias, user, password, database)
        else:
            dlog.error('SQLMR COMMAND is not defined in the input file!')
            return False


