#
# Unpublished work.
# Copyright (c) 2016-2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: TestBase Class to establish SSH connection to the system
import random
import base64
import json
import os
import subprocess
import re
import datetime
import time
import tempfile
import signal
import codecs

from os import stat
from Cluster import Cluster
from Dlog import dlog


class PTETestBase(object):
    def __init__(self, cfgJson, testParams={}):
        if 'logTimestamp' in testParams:
            self.logTimestamp = testParams['logTimestamp']
        if 'timeScale' in testParams:
            self.timeScale = int(testParams['timeScale'])
        else:
            self.timeScale = 1

        dlog.debug('TestBase Called!')

        if not testParams:
            testParams = {}
        self.testParams = testParams
        dlog.info('          Using the following Test Parameters:')
        dlog.info('-' * 50)
        for key in self.testParams:
            dlog.info('          %s : %s ' % (key, self.testParams[key]))
        dlog.info('-' * 50)

        self.localTest = False
        if 'LOCAL' in testParams:
            if testParams['LOCAL'] == 'True':
                self.localTest = True

        self.cfgJson = cfgJson
        self.actLoc = None
        self.psqlLoc = None
        self.buildLoc = None
        self.nClusterLoaderLoc = None
        self.kubeInstance = None
        self.defaultDb = None
        self.clusterType = None
        self.tunnel = None

        if "common" in self.cfgJson:
            commonDict = cfgJson['common']
            if "buildLoc" in commonDict:
                self.buildLoc = commonDict['buildLoc']
            if "actLoc" in commonDict:
                self.actLoc = commonDict['actLoc']
            if "psqlLoc" in commonDict:
                self.psqlLoc = commonDict['psqlLoc']
            if "nClusterLoaderLoc" in commonDict:
                self.nClusterLoaderLoc = commonDict['nClusterLoaderLoc']
            if "defaultDb" in commonDict:
                self.defaultDb = commonDict['defaultDb']

        if not self.localTest:
            self.clusterDict = cfgJson['cluster']
            self.cluster = Cluster(self.cfgJson)
            self.username = self.clusterDict['username']
            self.password = self.clusterDict['password']
            self.domainName = None
            self.queenNodes = None
            self.queenIps = None
            self.remoteIp = None
            self.workerNodes = None
            self.workerIps = None
            self.loaderNodes = None
            self.loaderIps = None
            self.hdfs_namenodes = None
            self.yarnQueueName = "default"
            self.deployment = None
            self.privateKey = None
            self.tdPrivateKey = None

            if "domain" in self.clusterDict:
                self.domainName = self.clusterDict['domain']
            if "queenNodes" in self.clusterDict:
                self.queenNodes = self.clusterDict['queenNodes']
            if "workerNodes" in self.clusterDict:
                self.workerNodes = self.clusterDict['workerNodes']
            if "queenIps" in self.clusterDict:
                self.queenIps = self.clusterDict['queenIps']
            if "remoteIp" in self.clusterDict:
                self.remoteIp = self.clusterDict['remoteIp']
            if "workerIps" in self.clusterDict:
                self.workerIps = self.clusterDict['workerIps']
            
            
            if "queue" in self.clusterDict:
                self.yarnQueueName = self.clusterDict['queue']

            if "deployment" in self.clusterDict:
                self.deployment = self.clusterDict['deployment']

            if "privateKey" in self.clusterDict:
                self.privateKey = self.clusterDict['privateKey']

            if "tdCluster" in self.cfgJson:
                self.tdClusterDict = cfgJson['tdCluster']
                if "tdPrivateKey" in self.tdClusterDict:
                    self.tdPrivateKey = self.tdClusterDict['tdPrivateKey']

            if "clusterType" in self.clusterDict:
                self.clusterType = self.clusterDict['clusterType']

            self.queenNames = self.cluster.queenNames
            self.workerNames = self.cluster.workerNames
            

    def queenExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the Queen Node
        '''
        timeoutValue = timeout * self.timeScale
        dlog.info('Running Command: %s' % commandStr)

        return self.cluster.queenExecCommand(commandStr, node=node, timeout=timeoutValue)

    def remoteExecCommand(self, commandStr, timeout=60):
        '''
        Execute a command on a Remote node
        '''
        timeoutValue = timeout * self.timeScale
        dlog.info('Running Command on Remote Node: %s' % commandStr)
        return self.cluster.remoteExecCommand(commandStr, timeout=timeoutValue)

    def tdMasterExecCommand(self, commandStr, timeout=60):
        '''
        Execute a command on the Teradata Master
        '''
        timeoutValue = timeout * self.timeScale
        dlog.info('Running Command on TD: %s' % commandStr)

        return self.cluster.tdMasterExecCommand(commandStr, timeout=timeoutValue)
    
    def queenPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the Queen location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.queenPut(localFile, remoteFile, node=node, timeout=timeoutValue)

    def queenGet(self, remoteFile, localFile, node=0, timeout=300):
        '''
        Sftp a remote file from the Queen to the local location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.queenGet(remoteFile, localFile, node=node, timeout=timeoutValue)

    def workerPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the Worker location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.workerPut(localFile, remoteFile, node=node, timeout=timeoutValue)

    def workerGet(self, remoteFile, localFile, node=0, timeout=300):
        '''
        Sftp a remote file from the Worker to the local location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.workerGet(remoteFile, localFile, node=node, timeout=timeoutValue)


    def tdMasterPut(self, localFile, remoteFile, timeout=300):
        '''
        Sftp a localFile to the Queen location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.tdMasterPut(localFile, remoteFile, timeout=timeoutValue)
    
    def tdMasterGet(self, remoteFile, localFile, timeout=300):
        '''
        Sftp a remote file from the Loader to the local location
        '''
        timeoutValue = timeout*self.timeScale
        return self.cluster.tdMasterGet(remoteFile, localFile, timeout=timeoutValue)

    def remotePut(self, localFile, remoteFile, timeout=300):
        '''
        Sftp a localFile to the Remote Node location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.remotePut(localFile, remoteFile, timeout=timeoutValue)
    
    def remoteGet(self, remoteFile, localFile, timeout=300):
        '''
        Sftp a remote file from the Remote node to the local location
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.remoteGet(remoteFile, localFile, timeout=timeoutValue)
    
    
    def openQueenInteract(self, node=0, timeout=60, display=False):
        '''
        Get an interactive shell for queen Node
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.openQueenInteract(node=node, timeout=timeoutValue, display=display)

    def openQueenContainerInteract(self, node=0, timeout=60, display=False):
        '''
        Get an interactive shell for queendb container on queen Node
        '''
        timeoutValue = timeout * self.timeScale
        containerId = self.getContainerIdFromQueen(node, type='queendb')
        return self.cluster.openQueenContainerInteract(containerId, node=node, timeout=timeoutValue, display=display)

    def workerExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the Worker Node
        '''
        timeoutValue = timeout * self.timeScale
        dlog.info('Running Command: %s' % commandStr)
        return self.cluster.workerExecCommand(commandStr, node=node, timeout=timeoutValue)

    def loaderExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the loader Node
        '''
        dlog.info('Running Command: %s' % commandStr)
        timeoutValue = timeout * self.timeScale
        return self.cluster.loaderExecCommand(commandStr, node=node, timeout=timeoutValue)

    def execCmdOnNodesInParallel(self, commandStr, nodes, timeout=60):
        '''
        Execute a command on given nodes in parallel
        '''
        timeoutValue = timeout * self.timeScale
        dlog.info('Running Command in Parallel : %s' % commandStr)
        return self.cluster.execCmdOnMultipleNodesInParallel(commandStr, nodes, timeout=timeoutValue)

    def execCmdOnWorkersInParallel(self, commandStr, timeout=60):
        '''
        Execute a command on given nodes in parallel
        '''
        dlog.info('Running On Workers in Parallel Command: %s' % commandStr)
        timeoutValue = timeout * self.timeScale
        return self.cluster.execCmdOnMultipleNodesInParallel(commandStr, self.workerNodes, timeout=timeoutValue)

    def execCmdOnAllNodesInParallel(self, commandStr, timeout=60):
        '''
        Execute a command on given nodes in parallel
        '''
        dlog.info('Running On ALL Nodes in Parallel Command: %s' % commandStr)
        timeoutValue = timeout * self.timeScale
        nodes = self.queenNodes + self.workerNodes
        if self.loaderNodes != None:
            nodes += self.loaderNodes
        return self.cluster.execCmdOnMultipleNodesInParallel(commandStr, nodes, timeout=timeoutValue)
    def openWorkerInteract(self, node=0, timeout=60, display=False):
        '''
        Get an interactive shell for queen Node
        '''
        timeoutValue = timeout * self.timeScale
        return self.cluster.openWorkerInteract(node=node, timeout=timeoutValue, display=display)

    def execCmdLocal(self, cmd):
        '''
        Run command locally on the DartRunner machine/workstation
        '''
        # TODO: Add timeout to command
        dlog.info("Executing local command: %s" % cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )
            
        stdout, stderr = proc.communicate()
        status = proc.poll()
        
        if status != 0:
            dlog.error("Failed to execute command %s" % cmd)
        return status, stdout, stderr

    def installSqlMR(self, inputFile, fileAlias=None, user="beehive", password="beehive", database=None,
                     actParams=None):
        '''
        Copy the SqlMR jar file and install it on the cluster using act
        '''

        databaseStr = ''
        if database == None:
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if fileAlias == None:
            fileAlias = ''

        if actParams is None:
            actParams = ''
        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                else:
                    actParams = actParams + ' -p 30002 '
                

        # if local act location is set, use local act to install SQLMR function
        # to avoid copying file to Queen node
        if self.actLoc:
            installcmd = '\'\\install ' + inputFile + ' ' + fileAlias + '\''
            commandStr = "%s -h %s -U %s -w %s %s %s -c %s  " \
                         % (self.actLoc, queenNode, user, password, databaseStr, actParams, installcmd)
            status, stdout, stderr = self.execCmdLocal(commandStr)
            
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)
            remoteCommandStr = '\'\\install ' + remoteInputFile + ' ' + fileAlias + '\''
            commandStr = "/home/beehive/clients/act -U %s -w %s %s -c %s " \
                         % (user, password, databaseStr, remoteCommandStr)
            stdout, stderr, status = self.queenExecCommand(commandStr, timeout=900)

        dlog.info(stdout + stderr)
        if status != 0:
            return False
        else:
            return True

    def removeSqlMR(self, fileAlias, user="beehive", password="beehive", database=None, actParams=None):
        '''
        Copy the SqlMR jar file and install it on the cluster using act
        '''
        removeCommandStr = '\'\\remove ' + fileAlias + '\''
        databaseStr = ''
        if database == None:
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams is None:
            actParams = ''
            
        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                else:
                    actParams = actParams + ' -p 30002 '
                
        # if local act location is set, use local act to remove SQLMR function
        if self.actLoc:
            commandStr = "%s -h %s -U %s -w %s %s %s -c %s  " \
                         % (self.actLoc, queenNode, user, password, databaseStr, actParams, removeCommandStr)
            status, stdout, stderr = self.execCmdLocal(commandStr) 

        else:
            commandStr = "/home/beehive/clients/act -U %s -w %s %s %s -c %s " \
                         % (user, password, databaseStr, actParams, removeCommandStr)
            stdout, stderr, status = self.queenExecCommand(commandStr, timeout=900)

        dlog.info(stdout + stderr)
        if status != 0:
            return False
        else:
            return True

    def removeLineOnLocal(self, file, pattern, timeout=300):
        f = open(file, "r")
        newF = open(file + ".tmp", "w")

        while True:
            line = f.readline()
            if not line:
                break

            line = re.sub(pattern, '', line)

            newF.write(line)

        f.close()
        newF.close()

        p = subprocess.Popen("mv %s %s" % (file + ".tmp", file), shell=True,
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE )
            
        out, err = p.communicate()
        status = p.poll()
        if status != 0:
            dlog.error("Remove error line fail" % file)
            return False

        return True

    def removeLineOnQueen(self, file, pattern):
        cmd = "perl -pi -e %s %s" % (pattern, file)

        stdout, stderr, status = self.queenExecCommand(cmd, timeout=300)
        stdout = stdout + stderr

        if status != 0 and stdout != None:
            dlog.error("Remove error line fail\n %s" % stdout)
            return False
        else:
            return True

    def excSqlFileAndCompareOutput(self, inputFile, expectedOutputFile,
                                   user="beehive", password = "beehive",
                                   database = None, actParams=None, diffParams=None, timeout=1200):
        '''
        Copy the input file and expected output file on the queen.
        Execute input sql file on the cluster and compare output with
        expectedOutputFile.
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
            diffParams = "-u"
        else:
            diffParams = "-u " + diffParams

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')
        
        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                    
                else:
                    actParams = actParams + ' -p 30002 '

        if self.actLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            cmd = "cp %s %s" % (os.path.abspath(inputFile), localFile)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE )
            
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                return False
            
            randomNum = str(random.random())
            outputFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + \
                               "{}.generated".format(randomNum))
            
            cmd = self.actLoc + " -U %s -w %s %s %s -f %s -h %s> %s 2>&1" \
                  % (user, password, databaseStr, actParams, localFile, queenNode, outputFile)
            dlog.info('act command Used: %s' %cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )
            
            
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 and stdout.strip() != "":
                dlog.error("act command Failed! \n %s" % stdout)
                return False

            diffCmd = "diff %s %s %s " % (diffParams, expectedOutputFile, outputFile)
            dlog.info('diff command Used: %s' % diffCmd)
            p = subprocess.Popen(diffCmd, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )
            
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 and stdout.strip() != "":
                return False
            else:
                # Removing generated output file
                rmCmd= "rm -r {}".format(outputFile)
                p = subprocess.Popen(rmCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                rmout = p.communicate()
                p.poll()
                dlog.info("Removed generated out file successfully {}".format(rmout))
                return True 
            
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            localFile = expectedOutputFile
            baseFile = os.path.basename(expectedOutputFile)
            remoteExpectedOutputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteExpectedOutputFile)

            remoteOutFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + \
                                         ".generated")
            dlog.info("Generated output file on queen node: %s" % remoteOutFile)

            cmd = "/home/beehive/clients/act -U %s -w %s %s %s -f %s > %s 2>&1" \
                  % (user, password, databaseStr, actParams, remoteInputFile, remoteOutFile)
            dlog.info('act command: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=3600)
            stdout = stdout + stderr
            dlog.info(stdout)
            # if status != 0 and stdout != None:
            if status != 0 and stdout.strip() != "":
                dlog.error("The act command Failed!\n %s" % stdout)
                return False

            diffCmd = "diff %s %s %s " % (diffParams, remoteExpectedOutputFile, remoteOutFile)
            dlog.info('diff command Used: %s' % diffCmd)
            stdout, stderr, status = self.queenExecCommand(diffCmd, timeout=300)
            stdout = stdout + stderr
            dlog.info(stdout)

            if status != 0 and stdout != None:
                dlog.error("Diff in output\n %s" % stdout)
                return False
            else:
                return True

    def excSqlFile(self, inputFile, user="beehive", password = "beehive",
                   database = None, actParams=None, timeout=1200):
        '''
        Copy the input file and 
        execute input sql file on the cluster. Return the output of the sql file!
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        '''
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""
        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')
        
        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                    
                else:
                    actParams = actParams + ' -p 30002 '

        if self.actLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            cmd = "cp %s %s" % (os.path.abspath(inputFile), localFile)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE )
            
            out, err = p.communicate()
            status = p.poll()
            
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                stdout = out + err
                return (status, stdout)

            cmd = self.actLoc + " -U %s -w %s %s %s -f %s -h %s" \
                                % (user, password, databaseStr, actParams, localFile, queenNode)
            dlog.info('act command Used: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )

            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 or 'ERROR' in stdout:
                status = 1
            return (status, stdout)
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            cmd = "/home/beehive/clients/act -U %s -w %s %s %s -f %s " \
                  % (user, password, databaseStr, actParams, remoteInputFile)
            dlog.info('act command Used: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
            stdout = stdout + stderr
            # dlog.info(stdout)
            return (status, stdout)

    
    def excSql(self, inputSql, user="beehive", password = "beehive",
                   database = None, actParams=None, timeout=1200):
        '''
        Execute Sql String on the cluster using act. Return the output of the sql!
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        '''
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'   
                else:
                    actParams = actParams + ' -p 30002 '
        if self.actLoc:
            
            cmd = self.actLoc + " -U %s -w %s %s %s -c \"%s\" -h %s" \
                                % (user, password, databaseStr, actParams, inputSql, queenNode)
            dlog.info('act command Used: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )
            
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            return (status, stdout)
        else:
            cmd = "/home/beehive/clients/act -U %s -w %s %s %s -c \"%s\" " \
                  % (user, password, databaseStr, actParams, inputSql)
            dlog.info('Act Command Used: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)

            stdout = stdout + stderr
            dlog.info(stdout)
            return (status, stdout)


    def excSqlAsFile(self, inputSql, user="beehive", password = "beehive",
                   database = None, actParams=None, timeout=1200):
        '''
        Copy the input file and 
        execute input sql file on the cluster. Return the output of the sql file!
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        '''
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""
        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                    
                else:
                    actParams = actParams + ' -p 30002 '

        localFile = "/tmp/excSqlAsFile.sql"
        with open(localFile, "w") as file1:
            file1.write(inputSql)

        if self.actLoc:

            cmd = self.actLoc + " -U %s -w %s %s %s -f %s -h %s" \
                                % (user, password, databaseStr, actParams, localFile, queenNode)
            dlog.info('act command Used: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )
                
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 or 'ERROR' in stdout:
                status = 1
            return (status, stdout)
        else:
            baseFile = os.path.basename(localFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            cmd = "/home/beehive/clients/act -U %s -w %s %s %s -f %s " \
                  % (user, password, databaseStr, actParams, remoteInputFile)
            dlog.info('act command Used: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
            stdout = stdout + stderr
            dlog.info(stdout)
            return (status, stdout)

    def excSqlFileBackground(self, inputFile,
                             user="beehive", password="beehive",
                             database=None, actParams=None):
        """
        Copy the input file on the queen.
        Execute input sql file on the cluster, no validation
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        This will run the sql in the background and
        will return the name of the remote output file.
        """
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                    
                else:
                    actParams = actParams + ' -p 30002 '

        if self.actLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            cmd = "cp %s %s" % (os.path.abspath(inputFile), localFile)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE ) 
            
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                return False

            outFile = os.path.join("/tmp/", os.path.basename(inputFile) + \
                                   ".generated")
            cmd = "nohup " + self.actLoc + " -U %s -w %s %s %s -f %s -h %s> %s 2>&1 &" \
                                           % (user, password, databaseStr, actParams, localFile, queenNode,
                                              outFile)
            dlog.info('act command Used: %s' % cmd)
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return outFile
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            remoteOutFile = os.path.join("/tmp/", os.path.basename(inputFile) + \
                                         ".generated")
            cmd = "nohup /home/beehive/clients/act -U %s -w %s %s %s -f %s > %s 2>&1 &" \
                  % (user, password, databaseStr, actParams, remoteInputFile, remoteOutFile)
            dlog.info('act command Used: %s' % cmd)
            self.cluster.queenExecCommandBackground(cmd)
            return remoteOutFile

    def excSqlBackground(self, inputSql, user="beehive", password="beehive",
                         database=None, actParams=None):

        '''
        Execute Sql String on the cluster using act in the background. Do not wait for the output
        By default, user beehive will be used. Additional act params string
        can be passed using the actParams argument.
        Returns a filename which has the output of the sql statement
        '''

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if actParams == None:
            actParams = ""

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the actParams!')

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS' and self.actLoc:
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'  
                else:
                    actParams = actParams + ' -p 30002 '

        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
        outFile = os.path.join("/tmp", "bgfile_%s.generated" % timeStamp)
        if self.actLoc:
            cmd = "nohup " + self.actLoc + " -U %s -w %s %s %s -c \"%s\" -h %s> %s 2>&1 &" \
                                           % (user, password, databaseStr, actParams, inputSql, queenNode,
                                              outFile)
            dlog.info('act command Used: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


        else:
            cmd = "nohup /home/beehive/clients/act -U %s -w %s %s %s -c \"%s\" > %s 2>&1 &" \
                  % (user, password, databaseStr, actParams, inputSql, outFile)
            dlog.info('act command Used: %s' % cmd)
            self.cluster.queenExecCommandBackground(cmd)

        return outFile

    def excSqlFileOnTD(self, inputFile, user="tdqg", password="tdqg",
                   database=None, expectedOut=None, bteqParams=None, diff=False, diffParams=None, encoding=None):
        '''
        Copy the input file and 
        execute input sql file on the Teradata cluster. Return the output of the sql file!
        By default, user tdqg will be used. Additional bteq params string
        can be passed using the bteqParams argument.
        '''

        if self.cluster.tdQgmLink:
            tdQgmLink = self.cluster.tdQgmLink
        
        if diffParams is None:
            diffParams = ''
                
        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')

        localFileAbs = os.path.abspath(inputFile)
        
        baseFile = os.path.basename(inputFile)
        updatedLocalFile = os.path.join("/tmp/", baseFile)
        outFile = '%s_generated_%s'%(updatedLocalFile, timeStamp)
        updatedLocalFile = '%s_%s'%(updatedLocalFile, timeStamp)
        
        if encoding is None:
            outF = open(updatedLocalFile, "w")
        else:
            outF = codecs.open(updatedLocalFile, "w", encoding)
        
        outF.write('.logon %s,%s; \n'% (user, password))
        if not database:
            outF.write('DATABASE %s; \n' % (database))
        #outF.write('.SET SIDETITLES ON \n')
        #outF.write('.SET FOLDLINE ON \n')
        outF.write('.SET width 2000 \n')
        outF.write('.export report file=%s \n' % outFile)

        if encoding is None:
            with open(localFileAbs, "r") as lines:
                for line in lines:
                    line = re.sub(r'\$QGMLINK', tdQgmLink, line)
                    outF.write(line)
        else:
            with codecs.open(localFileAbs, "r", encoding) as lines:
                for line in lines:
                    line = re.sub(r'\$QGMLINK', tdQgmLink, line)
                    outF.write(line)        
        outF.write('\n')
        outF.write('.QUIT ;\n')
        outF.close()
                
        
        remoteInputFile = updatedLocalFile
        self.tdMasterPut(updatedLocalFile, remoteInputFile)

        if encoding is None:
            cmd = "bteq < %s " % (remoteInputFile)
        else:
            cmd = "bteq -c %s < %s " % (encoding.replace("-",""),remoteInputFile)

        dlog.info('bteq command Used: %s' % cmd)
        stdout, stderr, status = self.tdMasterExecCommand(cmd, timeout=900)
        if status != 0 and stdout != None:
            return (False,stdout, stderr)
        dlog.info("query execution successful! Verifying output...")
        stdout = stdout + stderr
        contents = ''
        try:
            self.tdMasterGet(outFile, outFile, timeout=900)
            if encoding is None:
                with open(outFile) as f:
                    contents = f.read()
            else:
                with codecs.open(outFile, encoding) as f:
                    contents = f.read()
                
        except Exception as e:
            dlog.error(e)
            dlog.error('Unable to get the outFile contents! Maybe bteq could not log the output in a file.')
            
        # dlog.info(stdout)
        
        if expectedOut is None:
            return (True, stdout, contents)
        
        else:
            
            expectedOutFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', expectedOut)
            if os.path.isfile(expectedOutFile):
                if os.path.isfile(outFile):
                    dlog.info('Expected Out is given as a file. Comparing the output with the generated!')
                    if diff:
                    
                        diffCmd = "diff %s %s %s " % (diffParams, expectedOutFile, outFile)
                        dlog.info('diff command Used: %s' % diffCmd)
                        p = subprocess.Popen(diffCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = p.communicate()
                        status1 = p.poll()
                        stdout1 = out + err
                        dlog.info(stdout1)
                        if status1 != 0 and stdout1.strip() != "":
                            dlog.error("Diff in output\n %s" % stdout1)
                            dlog.error("Generated output is %s" % contents)
                            return (False, stdout, contents)
                        else:
                            return (True, stdout,contents)
                    else:
                        if encoding is None:                       
                            with open(expectedOutFile, 'r') as f1:
                                expectOut = f1.read()
                        else:
                            with codecs.open(expectedOutFile, 'r', encoding) as f1:
                                expectOut = f1.read()
                        if contents in expectOut or expectOut in contents:
                            return (True, stdout,contents)
                        else:
                            return (False, stdout, contents)
                            
                else:
                    return (False, stdout, contents)
                    
            else:
                
                for item in expectedOut.split(',') :
                    if not ((item in contents) or (item in stdout)):
                        return (False, stdout, contents)
                return (True, stdout,contents)    
    
    
    def excSqlOnTD(self, inputSql, user="tdqg", password="tdqg",
                   database=None, expectedOut=None, bteqParams=None, diff=False, diffParams=None, encoding=None):
        '''
        Copy the inoputSql into an input sql file and 
        execute input sql file on the Teradata cluster. Return the output of the sql!
        By default, user tdqg will be used. Additional bteq params string
        can be passed using the bteqParams argument.
        '''

        if self.cluster.tdQgmLink:
            tdQgmLink = self.cluster.tdQgmLink
            
        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')

        
        baseFile = 'inputSql.sql'
        updatedLocalFile = os.path.join("/tmp/", baseFile)
        outFile = '%s_generated_%s'%(updatedLocalFile, timeStamp)
        updatedLocalFile = '%s_%s'%(updatedLocalFile, timeStamp)
        
        outF = open(updatedLocalFile, "w")
        
        outF.write('.logon %s,%s; \n'% (user, password))
        if not database:
            outF.write('DATABASE %s; \n' % (database))
        #outF.write('.SET SIDETITLES ON \n')
        #outF.write('.SET FOLDLINE ON \n')
        outF.write('.SET width 2000 \n')
        outF.write('.export report file=%s \n' % outFile)
        
        
        line = re.sub(r'\$QGMLINK', tdQgmLink, inputSql)
        outF.write(line)
        outF.write('\n')
        outF.write('.QUIT ;\n')
        outF.close()
                
        
        remoteInputFile = updatedLocalFile
        self.tdMasterPut(updatedLocalFile, remoteInputFile)

        if encoding is None:
            cmd = "bteq < %s " % (remoteInputFile)
        else:
            cmd = "bteq -c %s < %s " % (encoding.replace("-",""),remoteInputFile)

        dlog.info('bteq command Used: %s' % cmd)
        stdout, stderr, status = self.tdMasterExecCommand(cmd, timeout=900)
        if status != 0 and stdout != None:
            return (False,stdout, stderr)
        dlog.info("query execution successful! Verifying output...")
        stdout = stdout + stderr
        contents = ''
        try:
            self.tdMasterGet(outFile, outFile, timeout=900)
            with open(outFile) as f:
                contents = f.read()
                
        except Exception as e:
            dlog.error(e)
            dlog.error('Unable to get the outFile contents! Maybe bteq could not log the output in a file.')
            
        # dlog.info(stdout)
        
        if expectedOut is None:
            return (True, stdout, contents)
        
        else:
            
            expectedOutFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', expectedOut)
            if os.path.isfile(expectedOutFile):
                if os.path.isfile(outFile):
                    dlog.info('Expected Out is given as a file. Comparing the output with the generated!')
                    if diff:
                    
                        diffCmd = "diff %s %s %s " % (diffParams, expectedOutFile, outFile)
                        dlog.info('diff command Used: %s' % diffCmd)
                        p = subprocess.Popen(diffCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = p.communicate()
                        status1 = p.poll()
                        stdout1 = out + err
                        dlog.info(stdout1)
                        if status1 != 0 and stdout1.strip() != "":
                            dlog.error("Diff in output\n %s" % stdout1)
                            dlog.error("Generated output is %s" % contents)
                            return (False, stdout, contents)
                        else:
                            return (True, stdout,contents)
                    else:
                        with open(expectedOutFile, 'r') as f1:
                            expectOut = f1.read()
                        if contents in expectOut or expectOut in contents:
                            return (True, stdout,contents)
                        else:
                            return (False, stdout, contents)
                            
                else:
                    return (False, stdout, contents)
                    
            else:
                
                for item in expectedOut.split(',') :
                    if not ((item in contents) or (item in stdout)):
                        return (False, stdout, contents)         
                return (True, stdout,contents)
    
            
 
    def excSqlFileWithValidationOnTD(self, inputFile, validationFile, validateOn="TD", user="tdqg", password="tdqg",
                   database=None, bteqParams=None, diffParams=None):
        '''
        Copy the input file and 
        execute input sql file on the Teradata cluster. Run the validation sql on either TD or ASTER!
        Compare both the output files.
        '''

        if self.cluster.tdQgmLink:
            tdQgmLink = self.cluster.tdQgmLink
            
        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')

        localFileAbs = os.path.abspath(inputFile)
        
        baseFile = os.path.basename(inputFile)
        updatedLocalFile = os.path.join("/tmp/", baseFile)
        outFile = '%s_generated_%s'%(updatedLocalFile, timeStamp)
        updatedLocalFile = '%s_%s'%(updatedLocalFile, timeStamp)
        
        outF = open(updatedLocalFile, "w")
        
        outF.write('.logon %s,%s; \n'% (user, password))
        if not database:
            outF.write('DATABASE %s; \n' % (database))
        #outF.write('.SET SIDETITLES ON \n')
        #outF.write('.SET FOLDLINE ON \n')
        outF.write('.SET width 2000 \n')
        outF.write('.export report file=%s \n' % outFile)
        
        with open(localFileAbs, "r") as lines:
            for line in lines:
                line = re.sub(r'\$QGMLINK', tdQgmLink, line)
                outF.write(line)
        outF.write('\n')
        outF.write('.QUIT ;\n')
        outF.close()
                
        
        remoteInputFile = updatedLocalFile
        self.tdMasterPut(updatedLocalFile, remoteInputFile)

        cmd = "bteq < %s " % (remoteInputFile)
        dlog.info('bteq command Used: %s' % cmd)
        stdout, stderr, status = self.tdMasterExecCommand(cmd, timeout=900)
	if status != 0 and stdout != None:
            return (False,stdout, stderr)
        dlog.info("query execution successful! Verifying output...")
        stdout = stdout + stderr
        contents = ''
        try:
            self.tdMasterGet(outFile, outFile, timeout=900)
            with open(outFile) as f:
                contents = f.read()
                
        except Exception as e:
            dlog.error(e)
            dlog.error('Unable to get the outFile contents! Maybe bteq could not log the output in a file.')
            
        # dlog.info(stdout)
        
        localFileAbsVal = os.path.abspath(validationFile)
        
        baseFileVal = os.path.basename(validationFile)
        updatedLocalFileVal = os.path.join("/tmp/", baseFileVal)
        outFileVal = '%s_generated_%s'%(updatedLocalFileVal, timeStamp)
        updatedLocalFileVal = '%s_%s'%(updatedLocalFileVal, timeStamp)
        
        outF = open(updatedLocalFileVal, "w")
        
        outF.write('.logon %s,%s; \n'% (user, password))
        if not database:
            outF.write('DATABASE %s; \n' % (database))
        #outF.write('.SET SIDETITLES ON \n')
        #outF.write('.SET FOLDLINE ON \n')
        outF.write('.SET width 2000 \n')
        outF.write('.export report file=%s \n' % outFileVal)
        
        with open(localFileAbsVal, "r") as lines:
            for line in lines:
                line = re.sub(r'\$QGMLINK', tdQgmLink, line)
                outF.write(line)
        outF.write('\n')
        outF.write('.QUIT ;\n')
        outF.close()
                
        
        remoteInputFileVal = updatedLocalFileVal
        self.tdMasterPut(updatedLocalFileVal, remoteInputFileVal)

        cmd = "bteq < %s " % (remoteInputFileVal)
        dlog.info('bteq command Used: %s' % cmd)
        stdoutVal, stderrVal, status = self.tdMasterExecCommand(cmd, timeout=900)
        stdoutVal = stdoutVal + stderrVal
        contentsVal = ''
        try:
            self.tdMasterGet(outFileVal, outFileVal, timeout=900)
            with open(outFileVal) as f:
                contentsVal = f.read()
                
        except Exception as e:
            dlog.error(e)
            dlog.error('Unable to get the outFile contents! Maybe bteq could not log the output in a file.')
            
        # dlog.info(stdout)
        contentsValLines = contentsVal.split('\n')
        contentsLines = contents.split('\n')
        
        for line in contentsLines:
            if 'C_ID' in line or 'c_id' in line or 'C_int' in line \
                            or 'c_int' in line or '-----' in line:
                continue
                
            found = False
            array1 = line.split()
            for lineVal in contentsValLines: 
                array2 = lineVal.split()
                for item in array1:
                    if item not in array2:
                        break
                dlog.info('Found row:')
                dlog.info(line)
                found = True
                break
            if not found:
                dlog.info('The below row is not found')
                dlog.info(line)
                return (False, stdout, contents, stdoutVal, contentsVal)
        
        dlog.info('All the rows are found in the validation output!!')    
        return (True, stdout, contents, stdoutVal, contentsVal)
    

    def loadDataFile(self, inputFile,tablename,user="beehive",
                        password = "beehive", database="beehive",
                        loaderParams=None):
        '''
        Load data into the table based on given parameters.
        '''
        if not os.path.exists(inputFile):
            return False

        if loaderParams == None:
            loaderParams = ""

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS':
                    loaderParams = loaderParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'      
                else:
                    loaderParams = loaderParams + ' -p 30002 '

        if self.nClusterLoaderLoc:
            cmd = self.nClusterLoaderLoc + ' -h %s -U %s -w %s -d %s  %s \'%s\' %s' \
                                           % (queenNode, user, password, database, loaderParams, tablename,
                                              inputFile)
            status, stdout, stderr = self.execCmdLocal(cmd)
            if status != 0:
                dlog.error(stdout + stderr)
                return False
            return True
        else:
            dlog.error("nClusterLoaderLoc option is not set in cluster config file. Please set it to use load data")
            return False


    def runTDFastload(self, confFile, datFile, user="tdqg", password = "tdqg", database="tdqg"):
        '''
        Load data into TD cluster by command fasdload
        '''
        confFile = os.path.abspath(confFile)
        datFile = os.path.abspath(datFile)
        if not os.path.exists(confFile) or not os.path.exists(datFile):
            dlog.error("error with file path")
            return (False, None)

        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')

        conFileBaseFile = os.path.basename(confFile)
        confFileRemoteInputFile = os.path.join("/tmp/", conFileBaseFile)
        confFileRemoteInputFile = '%s_%s' % (confFileRemoteInputFile, timeStamp)

        self.tdMasterPut(confFile, confFileRemoteInputFile)

        datFileBaseFile = os.path.basename(datFile)
        datFileRemoteInputFile = os.path.join("/tmp/", datFileBaseFile)
        datFileRemoteInputFile = '%s_%s' % (datFileRemoteInputFile, timeStamp)

        self.tdMasterPut(datFile, datFileRemoteInputFile)

        cmd = "fastload < %s " % (datFileRemoteInputFile)
        dlog.info('fastload command Used: %s' % cmd)
        stdout, stderr, status = self.tdMasterExecCommand(cmd, timeout=900)
        stdout = stdout + stderr
        dlog.info("runTDFastload status = %s" %status)
        dlog.info("stdout = %s" %stdout)
        if status == 0:
            return (True, stdout)
        else:
            return (False, stdout)


    def getActShellOnQueen(self, user, password, database='beehive', actParams=''):
        ''' 
        Return an act shell on queen
        '''
        actShellOnQueen = ActShellOnQueen(self, user, password, database, actParams)
        if actShellOnQueen.openShellOK():
            return actShellOnQueen
        else:
            return None

    def getActShellOnQueendbContainer(self, user, password, database='beehive', actParams=''):
        ''' 
        Return an act shell on queen
        '''
        actShellOnQueen = ActShellOnQueen(self, user, password, database, actParams)
        if actShellOnQueen.openShellOKforQueendbContainer():
            return actShellOnQueen
        else:
            return None

    '''The following five methods(excSqlOnPostgres, excSqlFileOnPostgres, excSqlBackgroundOnPostgres, 
    excSqlFileBackgroundOnPostgres, excSqlFileOnPostgreAndCompareOutput) are used to execute the queries using Postgres. 
    '''

    def excSqlOnPostgres(self, inputPsql, database, user, password=None, targetDb="queenDb",
                         psqlParams=None, dbCmdPrint=False):
        '''
        Execute PostgreSql String on the cluster Return the output of the sql!
        '''
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ""

        if ' -d ' in psqlParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the psqlParams!')

        pstgrecmd = 'ps -ef | grep postgres'
        tmp_tuple = self.queenExecCommand(pstgrecmd)
        port = getPortno(tmp_tuple, targetDb)

        if password:
            tempPgpassFile = tempfile.NamedTemporaryFile(prefix='ExcnCompareOp.Pgpass')
            tempPgpassFile.write('*:*:*:%s:%s' % (user, password))
            tempPgpassFile.flush()
            pgPassFile = tempPgpassFile.name
            exp_remote_file = 'pgPassFile'
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using generated Postgres password file: %s' % pgPassFile)
        else:
            pgPassFile = getPgPassFile()
            exp_remote_file = 'pgPassFile'
            if len(pgPassFile) == 2:
                pgPassFile = pgPassFile[0]
                self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using Postgres password file %s' % pgPassFile)

        if self.psqlLoc:
            cmd = self.psqlLoc + " -p %s -U %s %s %s -c \"%s\" -h %s" \
                                 % (port, user, psqlParams, databaseStr, inputPsql, self.queenNames[0])
            dlog.info('Postgresql command Used: %s' % cmd)

            command = 'PGPASSFILE=pgPassFile %s' % (cmd)

            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if dbCmdPrint:
                cmd = "%s -a" % cmd

            return (status, stdout)
        else:
            cmd = "/home/beehive/sqlstore/bin/psql -p %s -U %s %s %s -c \"%s\" " \
                  % (port, user, psqlParams, databaseStr, inputPsql)
            if targetDb == 'queenDb':
                dlog.info('Postgresql Command Used: %s' % cmd)
                stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
                stdout = stdout + stderr
                dlog.info(stdout)
            else:
                command = 'PGPASSFILE=pgPassFile %s' % (cmd)
                dlog.info('Postgresql Command Used: %s' % command)
                stdout, stderr, status = self.queenExecCommand(command, timeout=900)
                stdout = stdout + stderr
                dlog.info(stdout)

            if dbCmdPrint:
                cmd = "%s -a" % cmd
            return (status, stdout)

    def excSqlFileOnPostgres(self, inputFile, database, user, password=None, targetDb="queenDb",
                             psqlParams=None):
        '''
        Copy the input file and
        execute input postgresql file on the cluster.
        '''
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ""
        if ' -d ' in psqlParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the psqlParams!')

        pstgrecmd = 'ps -ef | grep postgres'
        tmp_tuple = self.queenExecCommand(pstgrecmd)
        port = getPortno(tmp_tuple, targetDb)
        if password:
            tempPgpassFile = tempfile.NamedTemporaryFile(prefix='ExcnCompareOp.Pgpass')
            tempPgpassFile.write('*:*:*:%s:%s' % (user, password))
            tempPgpassFile.flush()
            pgPassFile = tempPgpassFile.name
            exp_remote_file = 'pgPassFile'
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using generated Postgres password file: %s' % pgPassFile)
        else:
            pgPassFile = getPgPassFile()
            exp_remote_file = 'pgPassFile'
            if len(pgPassFile) == 2:
                pgPassFile = pgPassFile[0]
                self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using Postgres password file %s' % pgPassFile)

        if self.psqlLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            p = subprocess.Popen("cp %s %s" % (os.path.abspath(inputFile), localFile), shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                stdout = out + err
                return (status, stdout)

            cmd = self.psqlLoc + " -p %s -U %s %s %s -f %s -h %s" \
                                 % (port, user, psqlParams, databaseStr, localFile, self.queenNames[0])
            dlog.info('postgre command Used: %s' % cmd)

            command = 'PGPASSFILE=pgPassFile %s' % (cmd)

            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 or 'ERROR' in stdout:
                status = 1

            return (status, stdout)
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)
            cmd = "/home/beehive/sqlstore/bin/psql -p %s -U %s %s %s -f %s " \
                  % (port, user, psqlParams, databaseStr, remoteInputFile)
            if targetDb == 'amvDb':
                cmd = 'PGPASSFILE=pgPassFile %s' % (cmd)
            dlog.info('postgre command Used: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
            stdout = stdout + stderr
            dlog.info(stdout)

            return (status, stdout)

    def excSqlBackgroundOnPostgres(self, inputSql, database, user, password=None, targetDb="queenDb",
                                   psqlParams=None, dbCmdPrint=False):

        '''
        Execute postgre Sql String on the cluster using psql. Do not wait for the output
        Returns a filename which has the output of the sql statement
        '''

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ""

        if ' -d ' in psqlParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the psqlParams!')

        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
        outFile = os.path.join("/tmp", "bgfile_%s.generated" % timeStamp)

        pstgrecmd = 'ps -ef | grep postgres'
        tmp_tuple = self.queenExecCommand(pstgrecmd)
        port = getPortno(tmp_tuple, targetDb)
        if password:
            tempPgpassFile = tempfile.NamedTemporaryFile(prefix='ExcnCompareOp.Pgpass')
            tempPgpassFile.write('*:*:*:%s:%s' % (user, password))
            tempPgpassFile.flush()
            pgPassFile = tempPgpassFile.name
            exp_remote_file = 'pgPassFile'
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using generated Postgres password file: %s' % pgPassFile)
        else:
            pgPassFile = getPgPassFile()
            exp_remote_file = 'pgPassFile'
            if len(pgPassFile) == 2:
                pgPassFile = pgPassFile[0]
                self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using Postgres password file %s' % pgPassFile)

        if self.psqlLoc:
            cmd = "nohup " + self.psqlLoc + " -p %s -U %s %s %s -c \"%s\" -h %s> %s 2>&1 &" \
                                            % (port, user, databaseStr, psqlParams, inputSql,
                                               self.queenNames[0], outFile)
            dlog.info('postgre command Used: %s' % cmd)
            command = 'PGPASSFILE=pgPassFile %s' % (cmd)
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if dbCmdPrint:
                cmd = "%s -a" % cmd

        else:
            cmd = "nohup /home/beehive/sqlstore/bin/psql -p %s -U %s %s %s -c \"%s\" > %s 2>&1 &" \
                  % (port, user, databaseStr, psqlParams, inputSql, outFile)
            if targetDb == 'amvDb':
                cmd = 'PGPASSFILE=pgPassFile %s' % (cmd)

            dlog.info('postgre command Used: %s' % cmd)
            self.cluster.queenExecCommandBackground(cmd)
            if dbCmdPrint:
                cmd = "%s -a" % cmd

        return outFile

    def excSqlFileBackgroundOnPostgres(self, inputFile,
                                       database, user, password=None, targetDb="queenDb", psqlParams=None):
        """
        Copy the input file on the queen.
        Execute input postgre sql file on the cluster.
        This will run the sql in the background and
        will return the name of the remote output file.
        """
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ""

        if ' -d ' in psqlParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the psqlParams!')

        pstgrecmd = 'ps -ef | grep postgres'
        tmp_tuple = self.queenExecCommand(pstgrecmd)
        port = getPortno(tmp_tuple, targetDb)

        if password:
            tempPgpassFile = tempfile.NamedTemporaryFile(prefix='ExcnCompareOp.Pgpass')
            tempPgpassFile.write('*:*:*:%s:%s' % (user, password))
            tempPgpassFile.flush()
            pgPassFile = tempPgpassFile.name
            exp_remote_file = 'pgPassFile'
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using generated Postgres password file: %s' % pgPassFile)
        else:
            pgPassFile = getPgPassFile()
            exp_remote_file = 'pgPassFile'
            os.chmod(pgPassFile, 0600)
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using Postgres password file %s' % pgPassFile)

        if self.psqlLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            p = subprocess.Popen("cp %s %s" % (os.path.abspath(inputFile), localFile), shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                return False
            outFile = os.path.join("/tmp/", os.path.basename(inputFile) + \
                                   ".generated")
            cmd = "nohup " + self.psqlLoc + " -p %s -U %s %s %s -f %s -h %s> %s 2>&1 &" \
                                            % (port, user, databaseStr, psqlParams, localFile, outFile,
                                               self.queenNames[0])
            dlog.info('postgre command Used: %s' % cmd)
            command = 'PGPASSFILE=pgPassFile %s' % (cmd)
            subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return outFile
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            remoteOutFile = os.path.join("/tmp/", os.path.basename(inputFile) + \
                                         ".generated")
            cmd = "nohup /home/beehive/sqlstore/bin/psql -p %s -U %s %s %s -f %s > %s 2>&1 &" \
                  % (port, user, databaseStr, psqlParams, remoteInputFile, remoteOutFile)
            if targetDb == 'amvDb':
                cmd = 'PGPASSFILE=pgPassFile %s' % (cmd)
            dlog.info('postgre command Used: %s' % cmd)
            self.cluster.queenExecCommandBackground(cmd)
            return remoteOutFile

    def excSqlFileOnPostgreAndCompareOutput(self, inputFile, expectedOutputFile, database,
                                            user, password=None, targetDb="queenDb", psqlParams=None, diffParams=None,
                                            dbCmdPrint=False):
        '''
        Copy the input file and expected output file on the queen.
        Execute input postgre sql file on the cluster and compare output with
        expectedOutputFile.
        '''

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ""

        if diffParams == None:
                diffParams = "-u"
        else:
            diffParams = "-u " + diffParams

        if ' -d ' in psqlParams:
            databaseStr = ''
            dlog.info('Ignoring the database String as -d option is specified in the psqlParams!')
        pstgrecmd = 'ps -ef | grep postgres'
        tmp_tuple = self.queenExecCommand(pstgrecmd)
        port = getPortno(tmp_tuple, targetDb)
        if password:
            tempPgpassFile = tempfile.NamedTemporaryFile(prefix='ExcnCompareOp.Pgpass')
            tempPgpassFile.write('*:*:*:%s:%s' % (user, password))
            tempPgpassFile.flush()
            pgPassFile = tempPgpassFile.name
            exp_remote_file = 'pgPassFile'
            self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using generated Postgres password file: %s' % pgPassFile)
        else:
            pgPassFile = getPgPassFile()
            exp_remote_file = 'pgPassFile'
            if len(pgPassFile) == 2:
                pgPassFile = pgPassFile[0]
                self.queenPut(pgPassFile, exp_remote_file)
            change_perm = 'chmod 600 pgPassFile'
            self.queenExecCommand(change_perm)
            dlog.info('Using Postgres password file %s' % pgPassFile)

        if self.psqlLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            p = subprocess.Popen("cp %s %s" % (os.path.abspath(inputFile), localFile), shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                return False

            outputFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + \
                                      ".generated")
            cmd = self.psqlLoc + " -p %s -U %s %s %s -f %s -h %s> %s 2>&1" \
                                 % (port, user, databaseStr, psqlParams, localFile, self.queenNames[0],
                                    outputFile)
            dlog.info("In If Execution block")
            dlog.info('postgre command Used: %s' % cmd)
            command = 'PGPASSFILE=pgPassFile %s' % (cmd)
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if status != 0 and stdout.strip() != "":
                dlog.error("postgre command Failed! \n %s" % stdout)
                return False

            diffCmd = "diff %s %s %s " % (diffParams, expectedOutputFile, outputFile)
            dlog.info('diff command Used: %s' % diffCmd)
            p = subprocess.Popen(diffCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            if dbCmdPrint:
                cmd = "%s -a" % cmd
            if status != 0 and stdout.strip() != "":
                dlog.error("Diff in output\n %s" % stdout)
                return False
            else:
                return True
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            localFile = expectedOutputFile
            baseFile = os.path.basename(expectedOutputFile)
            remoteExpectedOutputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteExpectedOutputFile)

            remoteOutFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + \
                                         ".generated")
            dlog.info("Generated output file on queen node: %s" % remoteOutFile)

            cmd = "/home/beehive/sqlstore/bin/psql -p %s -U %s %s %s -f %s > %s 2>&1" \
                  % (port, user, databaseStr, psqlParams, remoteInputFile, remoteOutFile)
            if targetDb == 'amvDb':
                cmd = 'PGPASSFILE=pgPassFile %s' % (cmd)
            dlog.info('postgre command: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
            stdout = stdout + stderr
            dlog.info(stdout)
            if status != 0 and stdout != None:
                dlog.error("The postgre command Failed!\n %s" % stdout)
                return False

            diffCmd = "diff %s %s %s " % (diffParams, remoteExpectedOutputFile, remoteOutFile)
            dlog.info('diff command Used: %s' % diffCmd)
            stdout, stderr, status = self.queenExecCommand(diffCmd, timeout=300)
            stdout = stdout + stderr
            dlog.info(stdout)
            if dbCmdPrint:
                cmd = "%s -a" % cmd
            if status != 0 and stdout != None:
                dlog.error("Diff in output\n %s" % stdout)
                return False
            else:
                return True

    def excSqlFileAndCompareDiffUsingRegex(self, inputFile, expectedOutputFile,
                                           dbname, regex=None,
                                           user="db_superuser",
                                           password="db_superuser",
                                           diffParams=None, actParams=None,
                                           sort=False):
        """
        This will execute the SQL file and compare the generated output with e
        xpected output using regex and sort
        - if sort is true and regex not given then will sort both out files at  
            a time and compare 
        - if sort is true and regex is given then will sort files individually 
            and then compare files using regex
        - if sort is false and regex is given then will compare files using regex
        - if sort is false and regex not given then will do simple file comparison
        """
        if dbname == None or dbname == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + dbname

        if actParams == None:
            actParams = ""

        queenNode = self.queenNames[0]
        if self.deployment:
            if self.deployment.lower() == 'docker':
                if self.clusterType and self.clusterType == 'AWS':
                    actParams = actParams + ' -p ' + str(self.localPort) + ' '
                    queenNode = 'localhost'
                    
                else:
                    actParams = actParams + ' -p 30002 '

        if diffParams == None:
            diffParams = "-u"
        else:
            diffParams = "-u " + diffParams

        if ' -d ' in actParams:
            databaseStr = ''
            dlog.info(
                'Ignoring the database String as -d option is specified '
                'in the actParams!')
        testName = os.path.basename(inputFile).split(".")[0]
        tmpFile1 = os.path.join("/tmp/", "tmp_{}1.queryResults".format(testName))
        tmpFile2 = os.path.join("/tmp/", "tmp_{}2.queryResults".format(testName))

        if self.actLoc:
            localFile = "/tmp/" + os.path.basename(inputFile)
            p = subprocess.Popen(
                "cp %s %s" % (os.path.abspath(inputFile), localFile),
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            if status != 0:
                dlog.error("Copy %s to /tmp fail" % inputFile)
                return False

            outputFile = os.path.join("/tmp/",
                                      os.path.basename(expectedOutputFile) + \
                                      ".generated")
            cmd = self.actLoc + " -U %s -w %s %s %s -f %s -h %s 2>&1 | tee %s" \
                                % (user, password, databaseStr, actParams,
                                   localFile, queenNode, outputFile)
            dlog.info('act command Used: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info("status is : %s" % status)
            if status != 0:
                dlog.error("act command returned non zero status %s \n console output is %s" % (status, stdout))
            if sort == True:
                if regex:
                    cmd = "sort %s > %s" % (expectedOutputFile, tmpFile1)
                    dlog.info("Sort expected out file %s" % cmd)
                    p = subprocess.Popen(cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    status = p.poll()

                    cmd = "sort %s > %s" % (outputFile, tmpFile2)
                    dlog.info("Sort actual out file %s" % cmd)
                    p = subprocess.Popen(cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    status = p.poll()
                    diffCmd = "diff %s %s %s %s " % (
                        diffParams, regex, tmpFile1, tmpFile2)
                else:
                    cmd = "sort %s > %s" % (expectedOutputFile, tmpFile1)
                    dlog.info("Sort expected out file %s" % cmd)
                    p = subprocess.Popen(cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    status = p.poll()

                    cmd = "sort %s > %s" % (outputFile, tmpFile2)
                    dlog.info("Sort actual out file %s" % cmd)
                    p = subprocess.Popen(cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    status = p.poll()
                    diffCmd = "diff {} {}".format(
                        tmpFile1, tmpFile2)
            else:
                if regex == None:
                    regex = ""
                diffCmd = "diff %s %s %s %s " % (
                    diffParams, regex, expectedOutputFile, outputFile)
            dlog.info('diff command Used: %s' % diffCmd)
            p = subprocess.Popen(diffCmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            status = p.poll()
            stdout = out + err
            dlog.info(stdout)
            # removing temp files created
            rmCmd = 'rm -r {} {}'.format(tmpFile1, tmpFile2)
            p = subprocess.Popen(rmCmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.communicate()
            p.poll()
            if status != 0 and stdout.strip() != "":
                dlog.error("Diff in output\n %s" % stdout)
                return False
            else:
                return True
        else:
            localFile = inputFile
            baseFile = os.path.basename(inputFile)
            remoteInputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteInputFile)

            localFile = expectedOutputFile
            baseFile = os.path.basename(expectedOutputFile)
            remoteExpectedOutputFile = os.path.join("/tmp/", baseFile)
            self.queenPut(localFile, remoteExpectedOutputFile)

            remoteOutFile = os.path.join("/tmp/",
                                         os.path.basename(expectedOutputFile) + \
                                         ".generated")
            dlog.info("Generated output file on queen node: %s" % remoteOutFile)

            # cmd = "/home/beehive/clients/act -U %s -w %s %s %s -f %s > %s 2>&1" \
            #      % (user, password, databaseStr, actParams, remoteInputFile,
            #         remoteOutFile)
            cmd = "/home/beehive/clients/act -U %s -w %s %s %s -f %s 2>&1 | tee %s" \
                  % (user, password, databaseStr, actParams, remoteInputFile,
                     remoteOutFile)
            dlog.info('act command: %s' % cmd)
            stdout, stderr, status = self.queenExecCommand(cmd, timeout=900)
            stdout = stdout + stderr
            dlog.info("status %s " % (status))
            if status != 0:
                dlog.error("act command returned non zero status: %s output is: \n %s" % (status, stdout))
            if sort == True:
                if regex:
                    cmd = "sort %s > %s" % (remoteExpectedOutputFile, tmpFile1)
                    dlog.info("Sort expected out file %s" % cmd)
                    stdout, stderr, status = self.queenExecCommand(cmd)
                    cmd = "sort %s > %s" % (remoteOutFile, tmpFile2)
                    dlog.info("Sort actual out file %s" % cmd)
                    stdout, stderr, status = self.queenExecCommand(cmd)
                    diffCmd = "diff %s %s %s %s " % (
                        diffParams, regex, tmpFile1, tmpFile2)
                else:
                    cmd = "sort %s > %s" % (remoteExpectedOutputFile, tmpFile1)
                    dlog.info("Sort expected out file %s" % cmd)
                    stdout, stderr, status = self.queenExecCommand(cmd)
                    cmd = "sort %s > %s" % (remoteOutFile, tmpFile2)
                    dlog.info("Sort actual out file %s" % cmd)
                    stdout, stderr, status = self.queenExecCommand(cmd)
                    diffCmd = "diff {} {}".format(
                        tmpFile1, tmpFile2)
            else:
                if regex == None:
                    regex = ""
                diffCmd = "diff %s %s %s %s " % (
                    diffParams, regex, remoteExpectedOutputFile, remoteOutFile)

            dlog.info('diff command Used: %s' % diffCmd)
            stdout, stderr, status = self.queenExecCommand(diffCmd, timeout=300)
            stdout = stdout + stderr
            dlog.info(stdout)
            # removing temp files created
            rmCmd = 'rm -r {} {}'.format(tmpFile1, tmpFile2)
            self.queenExecCommand(rmCmd, timeout=300)

            if status != 0 and stdout != None:
                dlog.error("Diff in output\n %s" % stdout)
                return False
            else:
                return True

    def excNcliCommand(self, ncliCommandStr, node=0, timeout=120, display=False, cmdShPromt="beehive@"):
        '''
        Use this method to execute ncli command in astershell
        of a kubernetes cluster
        '''
        timeoutValue = timeout * self.timeScale

        # Get the queen pod IP
        queenPodIp = self.kubeInstance.getQueenPodIp()
        # Execute ncli command on astershell
        commandStr = 'ssh-keygen -f \"/root/.ssh/known_hosts\" -R %s' % queenPodIp
        stdout, stderr, status = self.queenExecCommand(commandStr, node, timeout)
        dlog.info(stdout + stderr)

        #Increase buffersize to adjust any errors
        self.kubemasterInteract = self.kubeInstance.openKubeMasterInteract(node=node, timeout=timeoutValue, buffer_size=25000, display=display)
        # Flush the output to start with a clean plate
        self.kubemasterInteract.flush()
        commandStr = ''
        shPrompt = '(]| )# |$'
        self.kubemasterInteract.send(commandStr)
        index, out = self.kubemasterInteract.expect(shPrompt, timeout=60)
        dlog.info(out)
        dlog.info(index)
        passwordPrompt = "beehive@%s's password:" % queenPodIp
        commandStr = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no beehive@%s' % queenPodIp
        dlog.info("Connect to astershell using cmd %s " % commandStr)
        self.kubemasterInteract.send(commandStr)
        index, out = self.kubemasterInteract.expect(passwordPrompt, timeout=200)
        dlog.info(out)
        dlog.info(index)
        if not index == 0:
            dlog.info('Unable to connect using ssh!')
            return False

        # send password
        passwd = base64.b64decode('YXN0ZXI0ZGF0YQ==')
        self.kubemasterInteract.send(passwd)
        index, out = self.kubemasterInteract.expect(shPrompt, timeout=timeout)
        dlog.info(out)
        if not index == 0:
            dlog.info('Unable to connect using ssh to astershell!')
            return False

        # send the ncli command and return result
        dlog.info("Sending command '%s' " % ncliCommandStr)
        self.kubemasterInteract.send(ncliCommandStr)
        index, out = self.kubemasterInteract.expect(cmdShPromt, timeout=timeout)
        dlog.info(out)
        status = True
        if not index == 0:
            dlog.info('Unable to run the ncli command on astershell!')
            status = False
        # remove first line and last line if json format, else first line
        if 'json' in ncliCommandStr:
            out = out.split('\n')[1:][:-1]
        else:
            out = out.split('\n')[1:][:-1]
        out = ''.join(out)
        return out, status

    def getContainerIdFromQueen(self,node=0, type='queendb', timeout=60):

        timeoutValue = timeout * self.timeScale
        cmdstr = 'docker ps | grep %s' % type
        stdout, stderr, status = self.queenExecCommand(cmdstr, node=node, timeout=timeoutValue )
        containerId = stdout.splitlines()[0].split()[0]
        return containerId

    def getContainerIdFromWorker(self, node=0, type='runner', timeout=60):

        timeoutValue = timeout * self.timeScale
        workerName = 'worker%d_cloud' % (int(node) + 1)
        cmdstr = 'docker ps | grep %s | grep %s' % (workerName, type)
        stdout, stderr, status = self.workerExecCommand(cmdstr, node=node, timeout=timeoutValue)
        stdout = stdout + stderr
        dlog.info(stdout)
        containerId = stdout.splitlines()[0].split()[0]
        return containerId

    def queenContainerExecCommand(self, commandStr, container='queendb', node=0,  timeout=60, user=None):
        """
        Execute a command on queenDb container
        """
        timeoutValue = timeout * self.timeScale
        containerId = self.getContainerIdFromQueen(node, container, timeoutValue)
        dlog.info("Executing after connecting to a container..")
        if user is None:
            cmdstr = 'docker exec -i %s /bin/bash -c "%s" ' % (containerId, commandStr)
        else:
            cmdstr = 'docker exec -i -u %s %s /bin/bash -c "%s" ' % (user, containerId, commandStr)
        stdout, stderr, status = self.queenExecCommand(cmdstr, node=node, timeout=timeout)

        return stdout, stderr, status

    def workerContainerExecCommand(self, commandStr, container='runner', node=0, timeout=60, user=None):
        """
        Execute a command on runner container
        """
        timeoutValue = timeout * self.timeScale
        containerId = self.getContainerIdFromWorker(node, container)
        dlog.info("Executing after connecting to a container..")
        if user is None:
            cmdstr = 'docker exec -i %s /bin/bash -c "%s" ' % (containerId, commandStr)
        else:
            cmdstr = 'docker exec -i -u %s %s /bin/bash -c "%s" ' % (user, containerId, commandStr)
        stdout, stderr, status = self.workerExecCommand(cmdstr, node=node, timeout=timeoutValue)

        return stdout, stderr, status

    def excPostgreSqlOnQueenDbContainer(self, inputPsql, user, password=None,
                                        database=None, portNo=8000, psqlParams=None, container='queendb'):
        """
        Execute postgre sql command on queendb container for 
        a kubernetes cluster and return: stdout, stderr, status 
        """

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ''

        psqlPath = "export PGPASSWORD='%s';/home/beehive/sqlstore/bin/psql " %(password)
        cmdStr = psqlPath + "-U %s %s -p %s %s -c \'%s \' " \
                               % (user, databaseStr, portNo, psqlParams, inputPsql )
	
        return self.queenContainerExecCommand(cmdStr,container)

    def copyToContainer(self, containerId, from_location, to_location, node=0, timeout=60):
        """
        Copy a file from the localhost to inside a running container
        """
        cp_cmd = "docker cp %s %s:%s" % (from_location, containerId, to_location)
        stdout, stderr, status = self.queenExecCommand(cp_cmd, node, timeout)
        dlog.info(stdout + stderr)
        if status != 0:
            return False
        return True

    def copyFromContainer(self, containerId, from_location, to_location, node=0, timeout=60):
        """
        Copy a file from inside a running container to  the localhost
        """
        cp_cmd = "docker cp  %s:%s %s" % (containerId, from_location, to_location)
        dlog.info(cp_cmd)
        stdout, stderr, status = self.queenExecCommand(cp_cmd, node, timeout)
        dlog.info(stdout + stderr)
        if status != 0:
            return False
        return True

    def excPostgreSqlFileOnQueenDbContainer(self, inputFile, database, user,
                                            password=None, portNo=8000, psqlParams=None):
        """
        Execute postgre sql file on queendb container for
        a kubernetes cluster and return: stdout, stderr, status 
        """

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ''

        # Get the queendb container Id
        queendbId = self.getContainerIdFromQueen(node=0, type='queendb', timeout=60)

        remoteInputFile = os.path.join("/tmp/", os.path.basename(inputFile))
        self.queenPut(inputFile, remoteInputFile)

        # copy sql file to queendb container
        self.copyToContainer(queendbId, remoteInputFile, remoteInputFile)

        psqlPath = '/home/beehive/sqlstore/bin/psql'
        cmdStr = "docker exec -i %s %s -U %s -w %s %s -p %s %s -f %s" % \
            (queendbId, psqlPath, user, password, databaseStr, portNo, psqlParams, remoteInputFile)

        return self.queenExecCommand(cmdStr)

    def excPostgreSqlFileOnQueenDbContainerAndCompareOutput(self, inputFile,
                expectedOutputFile, database, user, password=None, portNo=8000, psqlParams=None, diffParams=None):
        """
        Execute postgre sql file on queendb container for
         a kubernetes cluster and compare with expectedOutput 
         file and return: True OR False
        """

        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ''

        if diffParams == None:
            diffParams = ' -u '

        # Get the queendb container Id
        queendbId = self.getContainerIdFromQueen(node=0, type='queendb', timeout=60)

        remoteInputFile = os.path.join("/tmp/", os.path.basename(inputFile))
        self.queenPut(inputFile, remoteInputFile)

        generatedOutputFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + ".generated")

        remoteOutputFile = os.path.join("/tmp", os.path.basename(expectedOutputFile))
        self.queenPut(expectedOutputFile, remoteOutputFile)

        # copy sql file to queendb container
        self.copyToContainer(queendbId, remoteInputFile, remoteInputFile)

        psqlPath = '/home/beehive/sqlstore/bin/psql'
        cmdStr = "docker exec -i %s %s -U %s -w %s %s -p %s %s -f %s> %s 2>&1" % \
                 (queendbId, psqlPath, user, password, databaseStr, portNo, psqlParams, remoteInputFile, generatedOutputFile)
        stdout, stderr, status = self.queenExecCommand(cmdStr, timeout=900)
        stdout = stdout + stderr
        if status !=0 and 'ERROR' in stderr:
            dlog.info("The postgre command failed!\n %s" % stdout)
            return False

        diffCmd = "diff %s %s %s" % (diffParams, remoteOutputFile, generatedOutputFile)
        stdout, stderr, status = self.queenExecCommand(diffCmd, timeout=300)
        stdout = stdout + stderr
        if status != 0 and stdout != None:
            dlog.error("Diff in output:\n %s" % stdout)
            return False

        return True

    def excPostgreSqlFileOnQueenDbContainerAndCompareDiffUsingRegex(self, inputFile,expectedOutputFile, database,
                 user, password=None, portNo=8000, psqlParams=None, diffParams=None,regex=None, sort=False):
        """
        Execute postgre sql file on queendb container for
         a kubernetes cluster and compare with expectedOutput using regex and sort
         file and return: True OR False
        - if sort is true and regex not given then will sort both out files at
            a time and compare
        - if sort is true and regex is given then will sort files individually
            and then compare files using regex
        - if sort is false and regex is given then will compare files using regex
        - if sort is false and regex not given then will do simple file comparison
        """
        if database == None or database == '':
            databaseStr = ''
        else:
            databaseStr = ' -d ' + database

        if psqlParams == None:
            psqlParams = ''

        if diffParams == None:
            diffParams = ' -u '
        else:
            diffParams = "-u " + diffParams

        testName = os.path.basename(inputFile).split(".")[0]
        tmpFile1 = os.path.join("/tmp/", "tmp_{}1.queryResults".format(testName))
        tmpFile2 = os.path.join("/tmp/", "tmp_{}2.queryResults".format(testName))

        # Get the queendb container Id
        queendbId = self.getContainerIdFromQueen(node=0, type='queendb', timeout=60)

        remoteInputFile = os.path.join("/tmp/", os.path.basename(inputFile))
        self.queenPut(inputFile, remoteInputFile)

        generatedOutputFile = os.path.join("/tmp/", os.path.basename(expectedOutputFile) + ".generated")

        remoteExpectedOutputFile = os.path.join("/tmp", os.path.basename(expectedOutputFile))
        self.queenPut(expectedOutputFile, remoteExpectedOutputFile)

        # copy sql file to queendb container
        self.copyToContainer(queendbId, remoteInputFile, remoteInputFile)

        psqlPath = '/home/beehive/sqlstore/bin/psql'
        cmdStr = "docker exec -i %s %s -U %s -w %s %s -p %s %s -f %s> %s 2>&1" % \
                 (queendbId, psqlPath, user, password, databaseStr, portNo, psqlParams, remoteInputFile, generatedOutputFile)
        stdout, stderr, status = self.queenExecCommand(cmdStr, timeout=900)
        stdout = stdout + stderr
        if status !=0 and 'ERROR' in stderr:
            dlog.info("The postgres command failed!\n %s" % stdout)
            return False
		
        dlog.info("Generated output file on queen node: %s" % generatedOutputFile)
        if sort == True:
            if regex:
                cmd = "sort %s > %s" % (remoteExpectedOutputFile, tmpFile1)
                dlog.info("Sort expected out file %s" % cmd)
                stdout, stderr, status = self.queenExecCommand(cmd)
                cmd = "sort %s > %s" % (generatedOutputFile, tmpFile2)
                dlog.info("Sort actual out file %s" % cmd)
                stdout, stderr, status = self.queenExecCommand(cmd)
                diffCmd = "diff %s %s %s %s " % (
                    diffParams, regex, tmpFile1, tmpFile2)
            else:
                cmd = "sort %s > %s" % (remoteExpectedOutputFile, tmpFile1)
                dlog.info("Sort expected out file %s" % cmd)
                stdout, stderr, status = self.queenExecCommand(cmd)
                cmd = "sort %s > %s" % (generatedOutputFile, tmpFile2)
                dlog.info("Sort actual out file %s" % cmd)
                stdout, stderr, status = self.queenExecCommand(cmd)
                diffCmd = "diff {} {}".format(
                    tmpFile1, tmpFile2)
        else:
            if regex == None:
                regex = ""
            diffCmd = "diff %s %s %s %s " % (
                diffParams, regex, remoteExpectedOutputFile, generatedOutputFile)

        dlog.info('diff command Used: %s' % diffCmd)
        stdout, stderr, status = self.queenExecCommand(diffCmd, timeout=300)
        stdout = stdout + stderr
        dlog.info(stdout)
		
        # removing temp files 
        rmCmd = 'rm -r {} {}'.format(tmpFile1, tmpFile2)
        self.queenExecCommand(rmCmd, timeout=300)

        if status != 0 and stdout != None:
            dlog.error("Diff in output\n %s" % stdout)
            return False
        else:
            return True


def getPgPassFile():
    """
    Find the appropriate pgpass file to use for authentication.

    Use the PGPASSFILE environment variable if it is set.

    Otherwise use the default location of the pgpass file as specified by
    the PG_PASSFILE variable.

    If the pgpass file does not exist, throw an exception.
    """

    pgPassFile = os.getenv("PGPASSFILE", None)

    PG_PASSFILE = "/home/beehive/bin/utils/init/pgpass"
    if pgPassFile:
        # PGPASSFILE is defined in environment, use it instead of default.
        dlog.info("Using Postgres password file %s (from environment)" % pgPassFile)
        os.chmod(pgPassFile, 0600)
        if not os.path.exists(pgPassFile) or not os.access(pgPassFile, os.R_OK):
            # No pgpass file -> throw exception
            msg = "pgpass file %s not found or not readable" % pgPassFile
            dlog.error(msg)
            raise IOError

        return (pgPassFile, 1)
    else:
        # use default pgpass file
        pgPassFile = PG_PASSFILE
        dlog.info("Using default Postgres password file %s" % pgPassFile)
        return pgPassFile

def getPortno(tmp_tuple, targetDb):
    tmp_string = tmp_tuple[0]
    temp_values = tmp_string.split('\n')
    for val in temp_values:
        if '/home/beehive/toolchain/x86_64-unknown-linux-gnu/' in val:
            if 'queenDb' in val and targetDb == 'queenDb':
                port = re.findall(r'-p (\w+)', val)[0]
                return port
            elif 'amvDb' in val and targetDb == 'amvDb':
                port = re.findall(r'-p (\w+)', val)[0]
                return port
