#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner: alen.cheng@teradata.com
#
# Description: Dart Runner runs a list of tests on a list of Clusters in parallel
import argparse
import json
import os
import sys
import traceback

# This code is not required if PYTHONPATH is set as an ENV variable
libPath = os.path.abspath(os.path.dirname(__file__)) + '/lib'
sys.path.insert(0, libPath)
libPath = os.path.abspath(os.path.dirname(__file__)) + '/testsrc'
sys.path.insert(0, libPath)

from SshConnect import SshConnect

class GetHealthyClusters(object):
    
    def __init__(self, clusterList):
        """
        @summary: Get Healthy Clusters from a list of available clusters
        """  
        #Read the cluster Config Files
        self.clusterConfigDict = {}
        # Get the ClusterList
        self.clusterList = clusterList
        clustersStr = self.clusterList.split(',')
        self.clusters = []
        for clusterName in clustersStr:
            self.clusters.append(clusterName.strip())
            
        self.loadClusterConfigs()
        #Refresh the list of clusters.
        self.clusters = []
        for clusterName in self.clusterConfigDict:
            self.clusters.append(clusterName)
        
    def returnList(self):
        
        #Initialize Cluster States      
        self.clusterState = {}
        listStr = ''
        for cluster in self.clusters:
            if self.checkCluster(cluster):
                self.clusterState[cluster] = 'free'
            else:
                self.clusterState[cluster] = 'stale'
        
        for cluster in self.clusters:
            if self.clusterState[cluster] == 'free':
                
                listStr=listStr+cluster.strip()+','
                print(cluster),
        listStr = listStr[:-1]
        print(listStr)
        with open("/tmp/returnList", "w") as file1:
            file1.write("%s" % listStr)
                
                
        
    
    def loadClusterConfigs(self):
        
        libPath = os.path.abspath(os.path.dirname(__file__))
        for cluster in self.clusters:
            configFile = cluster + '.cfg'
            configFileAbs = libPath + '/config/' + configFile
            tempConfigFile = os.path.join('/tmp', configFile)
            try:
                fileT = open(tempConfigFile, 'w')
                with open(configFileAbs, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()
            
                with open(tempConfigFile, 'r') as f:
                    cfgJson = json.load(f)
                    self.clusterConfigDict[cluster] = cfgJson
        
            except ValueError as e:
                print('The Json File may have syntax issues! Check the config file %s!' % configFile)
                print(e)
            except Exception as e:
                print('Check the Config File!!')
                print(e)

    def kubeExecute(self,commandStr,cluster):
    
        cfgJson = self.clusterConfigDict[cluster]
        if "privateKey" in cfgJson["cluster"]:
            privateKey = cfgJson['cluster']['privateKey']

        else:
            privateKey = None
        username = cfgJson["kubeCluster"]["username"]
        password = cfgJson["kubeCluster"]["password"]
        domainName = cfgJson["kubeCluster"]['domain']
        kubemasters = cfgJson["kubeCluster"]['kubemaster']
        kubemaster = kubemasters[0]
        if '.' not in kubemaster:
            if domainName is None:
                print("Cannot proceed without domainName")
                raise
            kubemaster = kubemaster + '.' + domainName
        kubeMasterCon = SshConnect(kubemaster, username, password, privateKey)
        kubeMasterCon.connect()
        stdout, stderr, status = kubeMasterCon.execCommand(commandStr, timeout=30)
        print(stdout + stderr)
        kubeMasterCon.close()
        return stdout + stderr


    def checkCluster(self, cluster):
        clusterDict = self.clusterConfigDict[cluster]['cluster']
        queenCon = None
        queenNode = None
        if "deployment" in clusterDict:
            deployment = clusterDict['deployment']
            if deployment.lower() == 'docker' or deployment.lower() == 'spark':
                queenNodes = self.clusterConfigDict[cluster]['kubeCluster']['kubemaster']
                queenNode = queenNodes[0]
        else:
            if "queenNodes" in clusterDict:
                queenNodes = clusterDict['queenNodes']
                queenNode =  queenNodes[0]
        
        if '.' in queenNode:
            queenNodewithDomain = queenNode
        elif 'domain' in clusterDict:
            domainName = clusterDict['domain']
            queenNodewithDomain = queenNode + '.' + domainName
        else:
            print('QueenNode is not fully qualified in the cluster config file: %s.cfg' % cluster)
            return False
        if "username" in clusterDict:
            username = clusterDict['username']
        else:
            print('Username is required in the cluster config file: %s.cfg' % cluster)
        if "password" in clusterDict:
            password = clusterDict['password']
        else:
            password = None
        
        if "privateKey" in clusterDict:
            privateKey = clusterDict['privateKey']
        else:
            privateKey = None
        try:
            queenCon = SshConnect(queenNodewithDomain, username, password, privateKey)
            queenCon.connect()
            commandStr = 'lsb_release -a'
            stdout, stderr, status = queenCon.execCommand(commandStr, timeout=30)
            print('Ping on cluster %s Successful!' % cluster)
            print(stdout,stderr, status)
            print('Checking if kubernetes is Up!!')
            commandStr = 'kubectl get nodes'
            out = self.kubeExecute(commandStr, cluster)
            lines = out.split('\n')
            for line in lines:
                if line == '':
                    continue
                print(line)
                status = line.split()[1]
                print(status)
                if (not ('STATUS' in status or 'Ready' in status)) or ('NotReady' in status):
                    print('The Kubenetes is not in ready state on cluster!' % cluster)
                    return False
               
                    
            return True
        except Exception as e:
            print('The cluster is down. Unable to reach %s' % cluster)
            print(e)
            return False
        finally:
            if queenCon:
                queenCon.close()
            
    
if __name__ == "__main__":
    def printUsage():
        usage = '''
        Usage Example:
        GetHealthyClusters.py -c clusterList
        GetHealthyClusters.py -h
        '''
        print (usage)
        
    try:
        parser = argparse.ArgumentParser(description='GetHealthyClusters - Return  a list of tests healthy clusters')
        parser.add_argument('-c', '--clusterList',required=False, default=None, help='List of Clusters: Example "cdh251,cdh253"')
        
        args = parser.parse_args()

        if not args.clusterList:
            print "Cluster config file is required"
            printUsage()
            sys.exit(2)
            
        print(args.clusterList)
        
        GetClusters = GetHealthyClusters(args.clusterList)
        GetClusters.returnList()
        
    except Exception as e:
        print(e)
        print(sys.exc_info())
        print(traceback.format_exc())
        printUsage()
        sys.exit(2)
        
