#
# Unpublished work.
# Copyright (c) 2011-2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: Cluster Class to establish SSH connection to the system

from multiprocessing.pool import ThreadPool

from SshConnect import SshConnect
from Sftp import Sftp

class Cluster(object):

    def __init__(self, cfgJson):
        self.clusterDict = cfgJson['cluster']
        self.domainName = None
        self.queenNodes = None
        self.workerNodes = None
        self.loaderNodes = None
        self.hdfs_namenodes = None
        self.privateKey = None
        self.remoteNode = None
        self.sparkMaster = None
        self.sparkWorkers = None
        self.sparkManager = None
        self.sparkthriftserver = None

        if "domain" in self.clusterDict:
            self.domainName = self.clusterDict['domain']
        if "remoteNode" in self.clusterDict:
            self.remoteNode = self.clusterDict['remoteNode']
        if "queenNodes" in self.clusterDict:
            self.queenNodes = self.clusterDict['queenNodes']
        if "workerNodes" in self.clusterDict:
            self.workerNodes = self.clusterDict['workerNodes']
        if "loaderNodes" in self.clusterDict:
            self.loaderNodes = self.clusterDict['loaderNodes']
        if "hdfs_namenodes" in self.clusterDict:
            self.hdfs_namenodes = self.clusterDict['hdfs_namenodes']
        if "privateKey" in self.clusterDict:
            self.privateKey = self.clusterDict['privateKey']
    
        if "sparkMaster" in self.clusterDict:
            self.sparkMaster = self.clusterDict['sparkMaster']
        if "sparkWorkers" in self.clusterDict:
            self.sparkWorkers = self.clusterDict['sparkWorkers']
        if "sparkManager" in self.clusterDict:
            self.sparkManager = self.clusterDict['sparkManager']
        if "sparkthriftserver" in self.clusterDict:
            self.sparkthriftserver = self.clusterDict['sparkthriftserver']

        self.tdMasterNode = None
        self.tdQgmLink = None
        if 'tdCluster' in cfgJson:
            self.tdCluster = cfgJson['tdCluster']
            if "tdMasterNode" in self.tdCluster:
                self.tdMasterNode = self.tdCluster['tdMasterNode']
            if "tdUserName" in self.tdCluster:
                self.tdUserName = self.tdCluster['tdUserName']
            else:
                self.tdUserName = "root"
            if "tdPassword" in self.tdCluster:
                self.tdPassword = self.tdCluster['tdPassword']
            else:
                self.tdPassword = None
            if "tdPrivateKey" in self.tdCluster:
                self.tdPrivateKey = self.tdCluster['tdPrivateKey']
            else:
                self.tdPrivateKey = None
            
            if "qgmLink" in self.tdCluster:
                self.tdQgmLink = self.tdCluster['qgmLink']
            else:
                self.tdQgmLink = None
                
                 
        self.username = self.clusterDict['username']
        self.password = self.clusterDict['password']

        self.queenNames = list()
        self.queenCons = list()
        self.queenSftpCons = list()
        self.loaderSftpCons = list()
        self.workerSftpCons = list()
      
        if self.queenNodes:
            for queenNode in self.queenNodes:
                if '.' in queenNode:
                    queenNodewithDomain = queenNode
                else:
                    queenNodewithDomain = queenNode + '.' + self.domainName
                self.queenNames.append(queenNodewithDomain)
                queenCon = SshConnect(queenNodewithDomain, self.username, self.password, self.privateKey)
                self.queenCons.append(queenCon)

                queenSftpCon = Sftp(queenNodewithDomain, self.username, self.password, self.privateKey)
                self.queenSftpCons.append(queenSftpCon)

        if self.tdMasterNode:
            self.tdMasterNodeCon = SshConnect(self.tdMasterNode, self.tdUserName, self.tdPassword, self.tdPrivateKey)
            self.tdMasterNodeSftpCon = Sftp(self.tdMasterNode, self.tdUserName, self.tdPassword,self.tdPrivateKey )
        
        if self.remoteNode:
            self.remoteNodeCon = SshConnect(self.remoteNode, self.username, self.password, self.privateKey)
            self.remoteNodeSftpCon = Sftp(self.remoteNode, self.username, self.password, self.PrivateKey)
        
        self.workerCons = list()
        self.workerNames = list()
        if self.workerNodes:
            for workerNode in self.workerNodes:
                if '.' in workerNode:
                    workerNodewithDomain = workerNode
                else:
                    workerNodewithDomain = workerNode + '.' + self.domainName
                self.workerNames.append(workerNodewithDomain)
                workerCon = SshConnect(workerNodewithDomain, self.username, self.password, self.privateKey)
                self.workerCons.append(workerCon)

                workerSftpCon = Sftp(workerNodewithDomain, self.username, self.password, self.privateKey)
                self.workerSftpCons.append(workerSftpCon)

        self.loaderCons = list()
        self.loaderNames = list()
        if self.loaderNodes != None:
            for loaderNode in self.loaderNodes:
                if '.' in loaderNode:
                    loaderNodewithDomain = loaderNode
                else:
                    loaderNodewithDomain = loaderNode + '.' + self.domainName
                self.loaderNames.append(loaderNodewithDomain)
                loaderCon = SshConnect(loaderNodewithDomain, self.username, self.password,self.privateKey)
                self.loaderCons.append(loaderCon)

                loaderSftpCon = Sftp(loaderNodewithDomain, self.username, self.password, self.privateKey)
                self.loaderSftpCons.append(loaderSftpCon)

        self.namenodeCons = list()
        self.namenodeNames = list()
        if self.hdfs_namenodes != None:
            for nameNode in self.hdfs_namenodes:
                if '.' in nameNode:
                    nameNodewithDomain = nameNode
                else:
                    nameNodewithDomain = nameNode + '.' + self.domainName
                self.namenodeNames.append(nameNodewithDomain)
                namenodeCon = SshConnect(nameNodewithDomain, self.username, self.password,self.privateKey)
                self.namenodeCons.append(namenodeCon)

    def queenExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the Queen Node
        '''
        queenCon = self.queenCons[node]
        queenCon.connect()
        ret = queenCon.execCommand(commandStr, timeout=timeout)
        queenCon.close()

        return ret

    def remoteExecCommand(self, commandStr, timeout=60):
        '''
        Execute a command on a Remote Node
        '''
        self.remoteNodeCon.connect()
        ret = self.remoteNodeCon.execCommand(commandStr, timeout=timeout)
        self.remoteNodeCon.close()

        return ret

    def tdMasterExecCommand(self, commandStr, timeout=60):
        '''
        Execute a command on the Teradata Master Node
        '''
        self.tdMasterNodeCon.connect()
        ret = self.tdMasterNodeCon.execCommand(commandStr, timeout=timeout)
        self.tdMasterNodeCon.close()

        return ret
    
    def queenPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the Queen location
        '''
        queenSftpCon = self.queenSftpCons[node]
        queenSftpCon.connect()

        queenSftpCon.sftp.put(localFile, remoteFile)

    def queenGet(self, remoteFile, localFile,node=0, timeout=300):
        '''
        Sftp a remote file from the Queen to the local location
        '''
        queenSftpCon = self.queenSftpCons[node]
        queenSftpCon.connect()
        queenSftpCon.sftp.get(remoteFile, localFile)

    def remotePut(self, localFile, remoteFile, timeout=300):
        '''
        Sftp a localFile to the Remote node location
        '''
        self.remoteNodeSftpCon.connect()

        self.remoteNodeSftpCon.sftp.put(localFile, remoteFile)

    def remoteGet(self, remoteFile, localFile, timeout=300):
        '''
        Sftp a remote file from the Remote node to the local location
        '''
        self.remoteNodeSftpCon.connect()
        self.remoteNodeSftpCon.sftp.get(remoteFile, localFile)

    def workerPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the Queen location
        '''
        workerSftpCon = self.workerSftpCons[node]
        workerSftpCon.connect()

        workerSftpCon.sftp.put(localFile, remoteFile)

    def workerGet(self, remoteFile, localFile,node=0, timeout=300):
        '''
        Sftp a remote file from the Queen to the local location
        '''
        workerSftpCon = self.workerSftpCons[node]
        workerSftpCon.connect()
        workerSftpCon.sftp.get(remoteFile, localFile)

    def loaderPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the Queen location
        '''
        loaderSftpCon = self.loaderSftpCons[node]
        loaderSftpCon.connect()

        loaderSftpCon.sftp.put(localFile, remoteFile)

    def loaderGet(self, remoteFile, localFile,node=0, timeout=300):
        '''
        Sftp a remote file from the Queen to the local location
        '''
        loaderSftpCon = self.loaderSftpCons[node]
        loaderSftpCon.connect()
        loaderSftpCon.sftp.get(remoteFile, localFile)

    def tdMasterPut(self, localFile, remoteFile, timeout=300):
        '''
        Sftp a localFile to the TD Master location
        '''
        
        self.tdMasterNodeSftpCon.connect()

        self.tdMasterNodeSftpCon.sftp.put(localFile, remoteFile)

    def tdMasterGet(self, remoteFile, localFile, timeout=300):
        '''
        Sftp a remote file from the TDMasterNode to the local location
        '''
        self.tdMasterNodeSftpCon.connect()
        self.tdMasterNodeSftpCon.sftp.get(remoteFile, localFile)
    
    def workerExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the Worker Node
        '''
        workerCon = self.workerCons[node]
        workerCon.connect()
        ret = workerCon.execCommand(commandStr, timeout=timeout)
        workerCon.close()

        return ret

    def loaderExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the loader Node
        '''
        loaderCon = self.loaderCons[node]
        loaderCon.connect()
        return loaderCon.execCommand(commandStr, timeout=timeout)

    def openQueenInteract(self,node=0, timeout=60, buffer_size=1024, display=False):
        '''
        Open an interactive session on the Queen Node
        '''
        queenCon = self.queenCons[node]
        queenCon.connect()
        return queenCon.interact(display=display, timeout=timeout, buffer_size=buffer_size)

    def openQueenContainerInteract(self, queendbDockerContainerId, node=0, timeout=60, display=False):
        '''
        Open an interactive session to the queendb docker container on the Queen Node
        '''
        queenCon = self.queenCons[node]
        queenCon.connect()
        # Docker, open session to queendb docker container
        prompt = ']#'
        commandStr = "docker exec -it %s /bin/bash" % queendbDockerContainerId
        queenInteract = queenCon.interact(display=display, timeout=timeout)
        queenInteract.send(commandStr)
        index, out = queenInteract.expect(prompt, timeout=timeout)
        return queenInteract

    def openWorkerInteract(self,node=0, timeout=60, display=False):
        '''
        Open an interactive session on the worker Node
        '''
        workerCon = self.workerCons[node]
        workerCon.connect()
        return workerCon.interact(display=display, timeout=timeout)

    def openLoaderInteract(self,node=0, timeout=60, display=False):
        '''
        Open an interactive session on the loader Node
        '''
        loaderCon = self.loaderCons[node]
        loaderCon.connect()
        return loaderCon.interact(display=display, timeout=timeout)


    def openTDMasterInteract(self, timeout=60, display=False):
        '''
        Open an interactive session on the Teradata Master Node
        '''
        
        self.tdMasterNodeCon.connect()
        return self.tdMasterNodeCon.interact(display=display, timeout=timeout)

    def openRemoteInteract(self, timeout=60, display=False):
        '''
        Open an interactive session on the Remote Node
        '''

        self.remoteNodeCon.connect()
        return self.remoteNodeCon.interact(display=display, timeout=timeout) 
    
    def namenodeExecCommand(self, commandStr, node=0, timeout=60):
        '''
        Execute a command on the HDFS nameNode
        '''
        namenodeCon = self.namenodeCons[node]
        namenodeCon.connect()
        return namenodeCon.execCommand(commandStr, timeout=timeout)

    def queenExecCommandBackground(self, commandStr, node=0):
        '''
        Execute a non-blocking command on the Queen Node
        '''
        queenCon = self.queenCons[node]
        queenCon.connect()
        queenCon.execCommandBackground(commandStr)

    def execCommandOnNode(self, connection, command, timeout, node):
        '''
        This function is called in parallel by execCmdOnMultipleNodesInParallel()
        '''
        connection.connect()
        output, error, status = connection.execCommand(command,timeout)
        connection.close()
        return ( node, output, error, status )

    def execCmdOnMultipleNodesInParallel(self, command, nodes, timeout=60 ):
        '''
        Execute command on list of nodes in parallel and return a dictionary
        of nodeResults:
        nodeResults = {'node0': (output, error, result),
                       'node1': (output, error, result),
                       ...
                      }
        '''
        nodesPool = ThreadPool(100)
        nodesPoolWaitList = []
        nodeResults = dict()
        if not command:
            raise Exception ('Must provide a command for execCommand!')
        for i,node in enumerate(nodes):
            if '.' in node:
                nodewithDomain = node
            else:
                nodewithDomain = node + '.' + self.domainName
            connection = SshConnect(nodewithDomain, self.username, self.password, self.privateKey)
            nodesPoolWaitList.append(nodesPool.apply_async(self.execCommandOnNode,
                                        [connection, command, timeout, node]))
        for result in nodesPoolWaitList:
            node, output, error, status = result.get()
            nodeResults[node] = [output, error, status]

        return nodeResults
