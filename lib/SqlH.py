#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: anuj.mittal@teradata.com
# Secondary Owner: vaibhav.mahajan@teradata.com

import inspect
import os
import re
import sys
import shutil
import fileinput
import tempfile
from lib.Dlog import dlog
from lib.TestBase import TestBase
from testsrc.connector.sqlh.Hadoop import Hadoop

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

# SQL_MR DEFAULT 
DEFAULT_SQL_MR_PORT = 9083
DEFAULT_USER = "hive"

#ACT DB constants
USER_BEEHIVE = 'beehive'
USER_BEEHIVE_PASSWD = 'beehive'
#ACT
ACT_CMD = '/home/beehive/clients/act -U %s -w %s -f %s > %s'

#Unix Commands
DIFF_CMD = '/usr/bin/diff %s %s'
MD5SUM_CMD = '/usr/bin/md5sum %s'


class SqlH(TestBase):
    
    def __init__(self, cfgJson, testParams=None):
        TestBase.__init__(self, cfgJson, testParams)
        self.sourceCmd = "source /home/beehive/config/asterenv.sh; "
        self.hadoop = Hadoop(cfgJson["hadoopCluster"])
        self.cfgJson = cfgJson

    def run(self):
        queryFile = None
        if 'QUERY' in self.testParams:
            queryFile = self.testParams['QUERY']
        else:
            dlog.error('QUERY File is not defined in the input file!')
            return False

        expectedOutFile = None
        if 'EXPECTEDOUT' in self.testParams:
            expectedOutFile = self.testParams['EXPECTEDOUT']
        else:
            dlog.error('EXPECTEDOUT File is not defined in the input file!')
            return False

        user = None
        if 'USER' in self.testParams:
            user = self.testParams['USER']
        else:
            dlog.info('USER is not defined in the input file! Using the default beehive user')
            user = USER_BEEHIVE

        password = None
        if 'PASSWORD' in self.testParams:
            password = self.testParams['PASSWORD']
        else:
            dlog.info('PASSWORD is not defined in the input file! Using the default beehive password')
            password = USER_BEEHIVE_PASSWD
        
        actParams = None
        if 'ACTPARAMS' in self.testParams:
            actParams = self.testParams['ACTPARAMS']
        
        database = None
        if 'DATABASE' in self.testParams:
            database = self.testParams['DATABASE']
        else:
            dlog.info('DATABASE is not defined in the input file! Using the default database')

        #"ASTER_SETUP_CLEAN_UP" used in run_on_hive testcases
        asterSetup =  self.testParams.get('ASTER_SETUP_CLEAN_UP')
        if asterSetup and not self.asterSetupCleanUp():
            return False

        hcatSqlFile = self.testParams.get('HIVE_QUERY')
        if hcatSqlFile and not self.runHiveQuery(hcatSqlFile):
            return False

        hcatSetup = self.testParams.get('HCAT_SETUP')
        tables = None
        if hcatSetup:
            tables = self.createHcatSetup(hcatSetup)
            if not tables:
                dlog.info("Falied to create hadoop setup")
                return False
	currentDir = os.path.abspath(os.path.dirname(__file__))
        tempQueryFile = os.path.join(currentDir, os.path.basename(queryFile) + "_generated") 
        self.updateSqlhQueryParams(queryFile, tempQueryFile)
        
        #get the type of testcase, this is specially for lzo testcases
        #Reason : 
        #  a) lzo testcases requires compare and md5sum both to verify the data
        #  b) due to huge amount of data we can't directly generate data on queen_node
        #     node, so we will use /asterfs mount point
        #'TC_TYPE' == 'LZO' then call 'execSqlFileCompareOutputAndmd5Sum'
        tcType = self.testParams.get('TC_TYPE')
        if tcType:
            dst_dir = self.cfgJson['sqlhConfigs']['queen_lzo_out']
            if not self.execSqlFileCompareOutputAndmd5Sum(tempQueryFile, \
                                expectedOutFile, dst_dir, user, password):
                return False
        
        else:
            if not self.excSqlFileAndCompareOutput(tempQueryFile, expectedOutFile, \
                                               user, password, database, actParams):
                return False



        # Clear tables created during creatHCatSetup
        if hcatSetup and not self.hadoop.clearHadoopSetup(tables):
            dlog.error("Failed to clear setup")
            return False

        return True
        
    def execSqlFileCompareOutputAndmd5Sum(self, queryFile, expectedOutFile, dst_dir,\
                username='beehive', password='beehive', database='default'):
        """
        This method used to execute lzo testcases
        perform following steps
            a) copy the 'sql' file from local node to queen node
            b) execute the sql file stores it result
            c) compare the result of sql file with expectedOutFile, and
               their checksum
        """

        src = dst = queryFile
        #copy queryFile to queen node
        dlog.info('copying queryFile:%s from local node to queen node at %s\
        ' %(src, dst))
        self.queenPut(src, dst)
        dlog.info('successfully copied the query file on queen node at %s' \
        %(dst))
        #get 'queryFile' file name, without extension
        (fname, exten) = os.path.splitext(os.path.basename(queryFile))
        file_res_out = os.path.join(dst_dir, fname + '.expResult.generated')
        cmd = ACT_CMD %(username, password, dst, file_res_out)
        dlog.info('executing cmd:\'%s\' on queen node' %cmd)
        (output, errmsg, status) = self.queenExecCommand(cmd, timeout=3600)
        if status:
            dlog.error('failed to execute queryFile:%s on queen node' \
            % queryFile)
            return False
        else:
            dlog.info('successfully executed queryFile:%s on queen node' \
            % queryFile)
        #get diff status
        diff_status = self.get_diff_status(expectedOutFile, file_res_out )
        #get md5sum status
        md5_status = self.get_md5sum_status(expectedOutFile, file_res_out )

        if md5_status and diff_status:
            return True
        else:
            return False
         
        
    def get_diff_status(self, uncompressFile, compressedFile):
        """
        This method will take two files as input 
        
        Returns: True , if both has no diff otherwise False
        """
        
        dlog.info('comparing diff of compressed file: %s & uncompressed file %s' \
                 %(uncompressFile, compressedFile))
        cmd = DIFF_CMD %(uncompressFile, compressedFile)
        dlog.info('executing cmd:\'%s\' on queen node' %cmd)
        (output, errmsg, status) = self.queenExecCommand(cmd, timeout=1800)
                                                        
        if status:
            dlog.error('file has diff %s %s' %(uncompressFile, \
                                                compressedFile))
            return False
        else:
            return True  
            
    def get_md5sum_status(self, f1, f2):
        """
        This method will take two files as input 
        
        Returns: True , if both have same md5sum otherwise False
        """
        cmd = MD5SUM_CMD % f1
        dlog.info('executing md5sum cmd:\'%s\' on queen node ' %cmd)
        (md5_f1, errmsg, status) = self.queenExecCommand(cmd, timeout=1800)
        md5_f1 = md5_f1.strip()
        tmp_val = re.split('\s+', md5_f1)
        md5_f1 = tmp_val[0].strip()
        dlog.info('md5sum of file \'%s\' :: %s' %(f1, md5_f1))
        cmd = MD5SUM_CMD % f2
        dlog.info('executing md5sum cmd:\'%s\' on queen node ' %cmd)
        (md5_f2, errmsg, status) = self.queenExecCommand(cmd, timeout=1800)
        md5_f2 = md5_f2.strip()
        tmp_val = None
        tmp_val = re.split('\s+', md5_f2)
        md5_f2 = tmp_val[0].strip()
        dlog.info('md5sum of file \'%s\' :: %s' %(f2, md5_f2))
        md5_f2 = md5_f2.strip()
        
        if md5_f1 == md5_f2:
            return True
        else:
            dlog.error('md5sum is different for file %s  %s' %(f1, f2))
            return False
        
    def asterSetupCleanUp(self):
        """
        In this method, dropping all the database except 'default'
        """
    
        cmd = "show databases\\\" | grep -i runOnHive_DB | xargs -I {} hive -e \\\"DROP DATABASE IF EXISTS {} CASCADE"
        if self.hadoop.execHCatCommand(cmd):
            dlog.error('Failed to execute %s cmd on hadoop node' % cmd)
            return False
        else:
            dlog.info('Successfully executed %s cmd on hadoop node' % cmd)

        return True
        
    def updateSqlhQueryParams(self, queryFile, dst):
        """
        In this method we make the copy of 'queryFile' and update the values of following variables
        -> server('%(queen_node)s') 
        -> port('%(port)s')
        -> tablename('%(target_table_name)s')
        -> username('%(sqlh_username)s'))
        AND
        adding the additional parameter i.e. password('%(sqlh_password)s')),  if securityType == "kerberos" 
        """
        
        dlog.info('making copy of %s file i.e. "%s"' % (os.path.basename(queryFile), os.path.basename(dst)))
        try:
            shutil.copy(queryFile, dst)
        except IOerror, e:
            dlog.error('unable to copy %s file at "%s"' %(os.path.basename(queryFile), os.path.basename(dst)))
            return False

        securityType = self.cfgJson['sqlhConfigs']['securityType']
        if (securityType == 'kerberos' and not self.cfgJson['sqlhConfigs'].has_key('serverProxyConfig')) \
                   or securityType == "ldap_hs2":
            dlog.info('adding "password" parameter in %s sql file' %(os.path.basename(dst)))
            # creating two files (*_generated & *_generated.bak) using these files \
            # to adding parameter 'password' and replacing hadoopCluster config values
            for line in fileinput.input([dst, dst], inplace=True, mode='rU', backup='.bak'):
                if re.search(".?username\('\%\(sqlh_username\)s'\),", line):
                    line = re.sub(".?username\('\%\(sqlh_username\)s'\),", " username('%(sqlh_username)s'), password('%(sqlh_password)s'),", line)
                else:
                    line = re.sub(r".?username\('\%\(sqlh_username\)s'", " username('%(sqlh_username)s') password('%(sqlh_password)s'", line)
                print line.rstrip('\n')

            fileinput.close()
        else:
            shutil.copy(dst, dst+'.bak')

        #get aster db cluster config info
        clusterInfo = self.hadoopClusterConfig()

        fh = open(dst, "w")
        fh.write(((open(dst+'.bak', "r").read()) % clusterInfo))
        fh.close()
             
    def runHiveQuery(self, hcatSqlFile=None, dirPath=None, user=DEFAULT_USER):
        """
        In this method, executing query on hadoop masternode
        """

        if self.hadoop.execHCatFile(hcatSqlFile, dirPath, user):
            dlog.error('Failed to execute %s sql file on hadoop node' % os.path.basename(hcatSqlFile))
            return False
        else:
            dlog.info('Successfully executed %s sql file on hadoop node' % os.path.basename(hcatSqlFile))

        return True

    def hadoopClusterConfig(self):
        """
        This method will return the hadoop cluster info dictionary
        """
        
        config_info = {}
        config_info['hcatalog_server'] = self.cfgJson['hadoopCluster']['namenodes'][0]
        config_info['port'] = DEFAULT_SQL_MR_PORT

        if self.cfgJson['sqlhConfigs'].has_key('serverProxyConfig') and \
               self.cfgJson['sqlhConfigs']['serverProxyConfig']:
            proxyPrincipal = self.cfgJson['sqlhConfigs']['serverProxyConfig']['proxyPrincipal']
            if not proxyPrincipal:
                dlog.error("proxyPrincipal not defined for proxy user")
            
            config_info['sqlh_username'] = "%s@%s" % (self.cfgJson['sqlhConfigs']['sqlhUsername'], proxyPrincipal)
        else:
            config_info['sqlh_username'] = self.cfgJson['sqlhConfigs']['sqlhUsername']

        if "sqlhPassword" in self.cfgJson["sqlhConfigs"]:
            config_info['sqlh_password'] = self.cfgJson['sqlhConfigs']['sqlhPassword']
            
        return config_info

    def createHcatSetup(self, dataPath):
        user = self.cfgJson['sqlhConfigs']['sqlhUsername']
        permissions = "%s:%s" % (user, user)
        dataPath = os.path.join(dataPath, "data")
       
        tableList = self.hadoop.createHadoopSetup(user, permissions, dataPath)
        if not tableList:
            return False

        dlog.info("Hadoop setup created successfully")

        return tableList

