#
# Unpublished work.
# Copyright (c) 2011-2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2011-2017 by Teradata Corporation. All rights reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: rohit.khurd@teradata.com
# Secondary Owner:

import os
import re
import shutil
from collections import OrderedDict
from lib.Dlog import dlog
from lib.TestBase import TestBase
from testsrc.connector.spark.Spark import Spark

# KEY to replace in path for expected results of negative test cases
SYSTEM_TYPE_KEY = '%systype%'

# Default mode
DEFAULT_MODE = 'filessh'

#ACT DB constants
USER_BEEHIVE = 'beehive'
USER_BEEHIVE_PASSWD = 'beehive'

# Error key used for Negative tests
ERROR_KEY = 'ERROR:'

# MODEL DIRECTORIES used across AsterToSpark tests
# The reason these are listed here is to they can be deleted after
# execution of every test case. They need to be deleted since they cause
# permission issues, especially when the same test is run for livy
# and non-livy modes on the same cluster. The permission for these directories
# is different when create with livy (user=livy)
# as opposed to when created with ssh (user=runonspark)
MODEL_DIRECTORIES = [ '/tmp/kmeans1',
                      '/tmp/mlpcTest.model',
                      '/tmp/mlpcTest_PCA3.model',
                      '/tmp/LinearRegrModel1',
                      '/tmp/ALSModel1',
                      '/tmp/ALSModel2'
                    ]

class AsterToSpark(TestBase):
    def __init__(self, cfgJson, testParams=None):
        TestBase.__init__(self, cfgJson, testParams)
        self.sourceCmd = "source /home/beehive/config/asterenv.sh"
 
        self.spark = Spark(cfgJson["sparkCluster"])

        self.system = ""
        if self.spark.getSparkMaster().lower() == "yarn":
            self.system = self.system + \
                           self.spark.getHadoopDistribution().lower()

            # commented the lines below to be able to run Negative tests 
            # without requiring to regenrate expected files for the various
            # versions that we may plan to support
            # A basic segration of HDP and CDH results should hopefully suffice
            # We also have not tested standalone version of spark, so commenting
            # out relavant lines since we dont have the relevant files as well

            # self.system = self.system + \
                          # self.spark.getHadoopVersion().replace(".","")
            if self.spark.isColocated():
                self.system = self.system + 'colocated'
            else:
                self.system = self.system + 'remote'
        #else:
        #    self.system = self.system + \
        #                   self.spark.getSparkVersion().replace(".","")
        #    self.system = self.system + 'standalone'

        self.sparkNamenode = self.spark.getSparkNamenode()

        self.sparkHasLivy = self.spark.hasLivy()

        self.cfgJson = cfgJson
        self.valid_modes = {"filessh"   : {"suffix" : "_site.json-file-SSh",
                                           "prefix" : "AsterSpark_"},
                            "filenossh" : {"suffix" : "_site.json-file-noSSh",
                                           "prefix" : "AsterSpark_"},
                            "socketssh" : {"suffix" : "_site.json-socket-SSh",
                                           "prefix" : "AsterSpark_"},
                            "socketnossh" : {"suffix" : "_site.json-socket-noSSh",
                                             "prefix" : "AsterSpark_"},
                            "filelivy" : {"suffix" : "_site.json-file-livy",
                                          "prefix" : "AsterSpark_"},
                            "socketlivy" : {"suffix" : "_site.json-socket-livy",
                                            "prefix" : "AsterSpark_"}
                           }

        self.ignorePatterns = OrderedDict()

        # spark-submit failed socket
        self.ignorePatterns['(\s*SQL-MR function RUNONSPARK failed: '
                            'com.asterdata.ncluster.sqlmr.ClientVisibleException: '
                            'The command (/[a-zA-Z0-9\-\.]+)(/)?([a-zA-Z0-9\-\.]+\/)*spark-submit '
                            'failed with error Code: 1)\s.*$'] = "\\1"

        # lines from stacktrace
        self.ignorePatterns['^\s*(java|javax|scala|sun|org)(\.[a-zA-z0-9]+)+.*$'] = ''
        self.ignorePatterns['\s+at\s+(java|javax|scala|sun|org)(\.[$a-zA-z0-9<>]+)+'
                            '(\([$a-zA-Z0-9<>\.]+( )?[$a-zA-Z0-9<>\.]*(:[0-9]+)?(\))?)?(\s|$)'] = "\\7"

        # paths containing hostnames
        self.ignorePatterns['/home/beehive/config/spark/[a-zA-Z0-9\.\-]*/'] = '/home/beehive/config/spark/x/'

        # aster-spark-extension.jar and spark-assembly jar and other place where CDH and HDP may occurr
        self.ignorePatterns['aster-spark-extension-spark[0-9\.]*jar'] = 'aster-spark-extension-spark.jar'
        self.ignorePatterns['spark-assembly-[0-9\.\-]*(cdh)*[0-9\.\-]*'
                            '(hadoop)*[0-9\.\-]*(cdh*)[0-9\.\-]*jar'] = 'spark-assembly.jar'
        self.ignorePatterns['cdh[a-zA-Z0-9\.\-]*/'] = 'x/'

        # temporary paths
        self.ignorePatterns['spark[a-zA-Z0-9\-]*/'] = 'spark/'
        self.ignorePatterns['__spark_conf__[a-zA-Z0-9]*\.zip'] = '__spark_conf__.zip'

        # timestamps
        self.ignorePatterns['[0-9]{2}/[0-9]{2}/[0-9]{2}'
                            '[0-9]{2}:[0-9]{2}:[0-9]{2} '] = 'xx/xx/xx xx:xx:xx '

        # spark-yarn application id
        self.ignorePatterns['application(_[0-9]+)+'] =  'application_x'

        # HDFS/HTTP path/URL, Job tracking URLs containing hostname, port
        self.ignorePatterns['(hdfs|http)://((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*'
                            '[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*'
                            '[A-Za-z0-9])|([0-9]{1,3}\.[0-9]{1,3}\.'
                            '[0-9]{1,3}\.[0-9]{1,3})):[0-9]{1,5}'] = 'hxxx://x.x.x.x:x'

        # hostname with TID
        self.ignorePatterns['TID[ \t\n\r\f\v]*[0-9]+[, \t\n\r\f\v]*'
                            '((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
                            '([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])'
                            '|([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}))[ \t\n\r\f\v]*\)'] = 'TID x x.x.x.x)'

        # hostname/ip:port
        self.ignorePatterns['[ \t\n\r\f\v]*(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
                            '([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])'
                            '/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}'] = ' x.x.x.x/x:x'
        
        # ip
        self.ignorePatterns['[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'] = 'x.x.x.x'

        # :port
        self.ignorePatterns[':[0-9]{1,5}'] = ':x'

        # start time in long
        self.ignorePatterns['[ \t\n\r\f\v]*start time: [0-9]*'] = ' start time: x'

        # replace all other digits (linenumbers, etc.)
        self.ignorePatterns['[0-9]+'] = 'x'

    
    def run(self):

        queryFile = None
        if 'QUERY' in self.testParams:
            queryFile = self.testParams['QUERY']
        else:
            dlog.error('QUERY File is not defined in the input file!')
            return False

        category = "positive"
        if 'CATEGORY' in self.testParams:
            category = self.testParams['CATEGORY'].lower()

        expectedOutFile = None
        if 'EXPECTEDOUT' in self.testParams:
            # Basically the path to all negative test cases will be based on the
            # system type,distribution, and version
            # To keep the tst file generic, we dynamically generate this part of
            # the path for the negative tests based on the values in the cfg file
            # The subPath generated is something like 'hdp242remote'
            # So for negative test, path in tst file can be:
            #   testsrc/connector/spark/AsterToSpark/expectedResults/negative/%systype%/filessh/analytics/als.queryResults
            # which after replacement will becaome
            #   testsrc/connector/spark/AsterToSpark/expectedResults/negative/hdp242remote/filessh/analytics/als.queryResults
            if category == 'negative':
                if self.testParams['EXPECTEDOUT'].find(SYSTEM_TYPE_KEY) != -1:
                    expectedOutFile = self.testParams['EXPECTEDOUT'].replace(
                                           SYSTEM_TYPE_KEY,
                                           self.system)

                    dlog.info("EXPECTEDOUT after substitution: %s" %(expectedOutFile))
            else:
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

        mode = None
        if 'MODE' in self.testParams:
            mode = self.testParams['MODE']
            if mode not in self.valid_modes:
                dlog.warning("Invalid MODE: %s. Using default mode '%s'" %(mode, DEFAULT_MODE))
                mode = DEFAULT_MODE
            if self.isLivyMode(mode) and (not self.sparkHasLivy):
                dlog.error("!!! Cannot test mode '%s'; spark cluster does not have Livy." %(mode))
                return False
        else:
            dlog.warning("MODE is not defined in the input file! Using default mode '%s'" %(DEFAULT_MODE))
            mode = DEFAULT_MODE

        self.updateDefaultSparkClusterID(mode)

        retVal = False
        if category == 'negative':
            # Local method to mask the error messages based on regexs before comparison, locally
            retVal = self.excSqlFileAndCompareOutputNegative(queryFile, expectedOutFile, \
                                               user, password, database, actParams)
        else:
            retVal = self.excSqlFileAndCompareOutput(queryFile, expectedOutFile, \
                                               user, password, database, actParams)

        # Remove all model built locations so that they can be recreated,
        # for instance by a different user like 'livy'
        # The conditional check here may change as we learn the requirements with standalone spark
        if self.spark.getSparkMaster().lower() == "yarn":
            self.spark.execHDFSRmr(" ".join(MODEL_DIRECTORIES))

        return retVal



    def isLivyMode(self, mode):
        '''Check if mode is livy mode'''
        if mode.find('livy') == -1:
            return False
        else:
            return True


    def updateDefaultSparkClusterID(self, mode):
        '''
        Update the default spark cluster ID to use the mode provided
        This assumes that the setup was done using the the AsterToSparkSetup.py,
        which creates the 4 sparkIDs in the standard format for the test:
           SparkTest-file-SSh (the configureAster script has the format of <AsterSpark_<spark_namenode>_site.json-file-SSh>)
        '''
        
        if mode is None:
            return

        prefix = self.valid_modes[mode]['prefix']
        suffix = self.valid_modes[mode]['suffix']
        clusterID = prefix + self.sparkNamenode + suffix
        dlog.info('Setting default SPARK CLUSTER ID to "%s"' % (clusterID))
        
        commandStr = "%s; ncli spark addsparkconfigname --default=%s" % (self.sourceCmd, clusterID)
        dlog.info('Executing command on queen: %s' % (commandStr))
        stdout, stderr, status = self.queenExecCommand(commandStr, timeout=300)
        if status != 0:
            dlog.error('Command completed on queen with Status: %s; Out: %s; Err: %s'
                      % (status, stdout, stderr))
        else:
            dlog.info('Command completed on queen with Status: %s; Out: %s; Err: %s' 
                     % (status, stdout, stderr))


    def excSqlFileAndCompareOutputNegative(self, inputFile, expectedOutputFile,
                                   user="beehive", password = "beehive",
                                   database = None, actParams=None, diffParams=None):
        '''
        Copy the input file to the queen.
        Execute input sql file on the cluster, and copy the result to the Dart machine/workstation.
        Mask random strings in the error messages in both, the local copy of the generatedOutputFile,
        and a copy of the expectedOutputFile, and delete the local copies of the files.
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        '''

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""

        if diffParams == None:
            diffParams = ""

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')

        localFile = inputFile
        baseFile = os.path.basename(inputFile)
        remoteInputFile = os.path.join("/tmp/", baseFile)
        self.queenPut(localFile, remoteInputFile)

        localExpectedOutputFile = '/tmp/' + os.path.basename(expectedOutputFile)
        shutil.copy2(expectedOutputFile, localExpectedOutputFile)

        remoteOutFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + \
                           ".generated")
        dlog.info("Generated output file on queen node: %s" % remoteOutFile)

        cmd = "%s; /home/beehive/clients/act -U %s -w %s %s %s -f %s > %s 2>&1" \
                %(self.sourceCmd, user, password, databaseStr, actParams, remoteInputFile, remoteOutFile)
        stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
        stdout = stdout + stderr
        if status != 0 and stdout != None:
            dlog.error("ACT failed\n %s" % stdout)
            return False

        localGeneratedOutput = '/tmp/' + os.path.basename(remoteOutFile)
        self.queenGet(remoteOutFile, localGeneratedOutput)
        
        # mask the system/time specific error messages in the copy
        # of the expectedOutputFile and generatedOutputFile before comparison 
        self.morphOutputFile(localGeneratedOutput)
        self.morphOutputFile(localExpectedOutputFile)

        # run a local diff on the local mophed copies
        diffCmd = "diff %s %s %s " %(diffParams, localExpectedOutputFile, localGeneratedOutput)
        status, stdout, stderr = self.execCmdLocal(diffCmd)
        stdout = stdout + stderr

        # remove the local copies of the files post comparison
        os.remove(localGeneratedOutput)
        os.remove(localExpectedOutputFile)

        if status != 0 and stdout != None:
            dlog.error("Diff in output\n %s" % stdout)
            return False
        else:
            return True


    def morphOutputFile(self, fileToUpdate):
        updatedFile = fileToUpdate + '.updated'

        try:
            # Search for patterns and replace expected result
            fp1 = open(fileToUpdate, "r")
            fp2 = open(updatedFile, "w")

            for line in fp1:
                if len(line.rstrip('\n')) == 0:
                    fp2.write(line)
                    continue

                line = line.rstrip('\n')
                prefix = ''
                if re.match('^act:', line):
                    tmp = line.split(ERROR_KEY)
                    prefix = tmp[0]
                    line = tmp[1]

                # replace random and uncertain values in result file
                for ignorePattern, replaceSymbol in OrderedDict(self.ignorePatterns).items():
                    if len(line) == 0:
                        break
                    p = re.compile(ignorePattern, re.I)
                    line = p.sub(replaceSymbol, line)

                if len(prefix) > 0:
                    line = prefix + ERROR_KEY + line
                if len(line) > 0:
                    fp2.write(line + '\n')

            fp1.close()
            fp2.close()
        except IOError, err:
            print str(err)

        # move the updated file to replace the original local copy of the file
        os.rename(updatedFile, fileToUpdate)
