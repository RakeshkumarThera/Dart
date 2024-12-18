from lib.SshConnect import SshConnect
from lib.Sftp import Sftp
from lib.Dlog import dlog

import base64
import re

class Kubernetes():

    """
    This class provides functions to connect to a kubernetes cluster and execute commands
    """
    def __init__(self, cfgJson):
        kubeDict = cfgJson["kubeCluster"]
        clusterDict = cfgJson["cluster"]

        self.k8sMasters = None
        self.k8sNodes = None
        self.domainName = None
        self.kubemasterCon = None
        self.kubeNodeCon = None
        if "kubemaster" in kubeDict:
            self.k8sMasters = kubeDict["kubemaster"]
        if "kubenodes" in kubeDict:
            self.k8sNodes = kubeDict["kubenodes"]
        if "domain" in kubeDict:
            self.domainName = kubeDict['domain']

        self.kubeMasters = list()
        self.kubeNodes = list()
        for node in self.k8sMasters:
            if '.' in node:
                nodeWithDomain = node
            else:
                if self.domainName is None:
                    dlog.error("Cannot proceed without domainName")
                    raise
                nodeWithDomain = node + '.' + self.domainName
            self.kubeMasters.append(nodeWithDomain)

        for node in self.k8sNodes:
            if '.' in node:
                nodeWithDomain = node
            else:
                if self.domainName is None:
                    dlog.error("Cannot proceed without domainName")
                    raise
                nodeWithDomain = node + '.' + self.domainName
            self.kubeNodes.append(nodeWithDomain)

        if "username" in kubeDict:
            self.kubeUsername = kubeDict['username']
        if "password" in kubeDict:
            self.kubePassword = kubeDict['password']

        if "privateKey" in clusterDict:
            privateKey = clusterDict['privateKey']
        else:
            privateKey = None
                
        self.kubeMasterCons = list()
        self.kubeMasterSftpCons = list()
        for masternode in self.kubeMasters:
            kubeMasterCon = SshConnect(masternode, self.kubeUsername, self.kubePassword, privateKey)
            self.kubeMasterCons.append(kubeMasterCon)
            kubeMasterSftpCon = Sftp(masternode, self.kubeUsername, self.kubePassword, privateKey)
            self.kubeMasterSftpCons.append(kubeMasterSftpCon)

        self.kubeNodeCons = list()
        self.kubeNodeSftpCons = list()
        for kubenode in self.kubeNodes:
            kubeNodeCon = SshConnect(kubenode, self.kubeUsername, self.kubePassword, privateKey)
            self.kubeNodeCons.append(kubeNodeCon)
            kubeNodeSftpCon = Sftp(kubenode, self.kubeUsername, self.kubePassword, privateKey)
            self.kubeNodeSftpCons.append(kubeNodeSftpCon)


    def execKubeMaster(self, commandStr, node=0, timeout=60):
        """
        Execute a command on the KubeMaster
        """
        dlog.info("Executing command [%s]: %s" % (self.kubeMasters[node], commandStr))

        self.kubemasterCon = self.kubeMasterCons[node]
        self.kubemasterCon.connect()

        return self.kubemasterCon.execCommand(commandStr, timeout=timeout)

    def execKubeNode(self, commandStr, node=0, timeout=60):
        """
        Execute a command on the KubeNodes
        """
        dlog.info("Executing command [%s]: %s" % (self.kubeNodes[node], commandStr))

        self.kubeNodeCon = self.kubeNodeCons[node]
        self.kubeNodeCon.connect()

        return self.kubeNodeCon.execCommand(commandStr, timeout=timeout)

    def openKubeMasterInteract(self, node=0, timeout=60, buffer_size=1024, display=False):
        '''
        Open an interactive session on the Master Node
        '''
        kubeCon = self.kubeMasterCons[node]
        kubeCon.connect()
        return kubeCon.interact(display=display, timeout=timeout, buffer_size=buffer_size)

    def kubeMasterPut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the MasterNode location
        '''
        kubeMasterSftpCon = self.kubeMasterSftpCons[node]
        kubeMasterSftpCon.connect()

        kubeMasterSftpCon.sftp.put(localFile, remoteFile)

    def kubeNodePut(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the KubeNode location
        '''
        kubeNodeSftpCon = self.kubeNodeSftpCons[node]
        kubeNodeSftpCon.connect()

        kubeNodeSftpCon.sftp.put(localFile, remoteFile)

    def kubeMasterGet(self, remoteFile, localFile, node=0, timeout=300):
        '''
        Sftp a localFile to the MasterNode location
        '''
        kubeMasterSftpCon = self.kubeMasterSftpCons[node]
        kubeMasterSftpCon.connect()

        kubeMasterSftpCon.sftp.get(remoteFile, localFile)

    def kubeNodeGet(self, localFile, remoteFile, node=0, timeout=300):
        '''
        Sftp a localFile to the KubeNode location
        '''
        kubeNodeSftpCon = self.kubeNodeSftpCons[node]
        kubeNodeSftpCon.connect()

        kubeNodeSftpCon.sftp.get(localFile, remoteFile)

    def createInventoryFile(self,ansibleLoc):
        """
        @note: The IP address given as queenNode/WorkerNodes are mapped to kube-master and kube-nodes respectively
        """
        inventory_file = ansibleLoc + '/inventory/inventory_%s.local' % self.kubeMasters[0]


        with open(inventory_file, 'w') as output:
            output.write("[kube-master]" + "\n")
            for i, node in enumerate(self.kubeMasters):
                self.writeToFile(outfile=output, node=node, nodeId=i,master='yes')
            output.write("[aster-queen]" + "\n")
            if len(self.kubeMasters) > 1:
                node = self.kubeMasters[0]
                self.writeToFile(outfile=output, node=node, nodeId=0, master='yes')
            else:
                node = self.kubeNodes[0]
                self.writeToFile(outfile=output, node=node, nodeId=0, master='no')

            output.write("[aster-workers]" + "\n")
            if len(self.kubeMasters) > 1:
                for i, node in enumerate(self.kubeMasters):
                    if i == 0:
                        continue
                    self.writeToFile(outfile=output, node=node, nodeId=i, master='yes')
            for i, node in enumerate(self.kubeNodes):
                if len(self.kubeMasters) < 2:
                    if i == 0:
                        continue
                self.writeToFile(outfile=output, node=node, nodeId=i, master='no')

            output.write("[kube-aster:children]" + "\n")
            output.write("kube-master" + "\n")
            output.write("aster-queen" + "\n")
            output.write("aster-workers" + "\n")
            
        return inventory_file

    def createHostsFile(self,ansibleLoc, localRegistry="False", deleteDockerImages="False"):
	"""
	@note: creates hosts file in inventory directory
	"""
	inventory_file = ansibleLoc + '/inventory/hosts_%s' % self.kubeMasters[0]

	with open(inventory_file, 'w') as output:
	    output.write("[aster_local]" + "\n" + "localhost ansible_connection=local" + "\n" + "[kube_master]" + "\n")
	    if localRegistry == 'True' or deleteDockerImages == 'True':
		for i, node in enumerate(self.kubeMasters):
		    self.writeToFile(outfile=output, node=node, nodeId=i,master='yes')
	    output.write("\n")
	    if deleteDockerImages == 'False':
		output.write("[aster_queen]" + "\n\n" + "[aster_workers]" + "\n\n")
	    else:
		output.write("[aster_queen]" + "\n")
		if len(self.kubeMasters) > 1:
		    node = self.kubeMasters[0]
		    self.writeToFile(outfile=output, node=node, nodeId=0, master='yes')
		else:
		    node = self.kubeNodes[0]
		    self.writeToFile(outfile=output, node=node, nodeId=0, master='no')
		output.write("[aster_workers]" + "\n")
		if len(self.kubeMasters) > 1:
		    for i, node in enumerate(self.kubeMasters):
			if i == 0:
			    continue
			self.writeToFile(outfile=output, node=node, nodeId=i, master='yes')
		for i, node in enumerate(self.kubeNodes):
		    if len(self.kubeMasters) < 2:
			if i == 0:
			    continue
		    self.writeToFile(outfile=output, node=node, nodeId=i, master='no')
	    output.write("[kube_aster:children]" + "\n")
	    output.write("kube_master" + "\n")
	    output.write("aster_queen" + "\n")
	    output.write("aster_workers" + "\n")
	    output.write("[aster_local:vars]" + "\n")
            output.write("kubeconfig=%s/inventory/remote-kubeconfig-%s"% (ansibleLoc ,self.kubeMasters[0] + "\n"))
            output.write("queen=" + "\n")
	    
	return inventory_file

    def writeToFile(self, outfile, node, nodeId, master='yes'):
        # Check if node is an IP address
        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        check = pat.match(node)
        if check:
            ipOfNode = node
        else:
            # Get IP adderess
            if master == 'yes':
                stdout, stderr, status = self.execKubeMaster("host %s" % node, node=nodeId)
            else:
                stdout, stderr, status = self.execKubeNode("host %s" % node, node=nodeId)
            dlog.info(stdout)
            ipOfNode = stdout.split()[3]
        outfile.write(
            "%s ansible_host=%s ansible_connection=ssh ansible_ssh_user=%s ansible_ssh_pass=%s ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n" % (
                node, ipOfNode, self.kubeUsername, self.kubePassword))

    def checkClusterStatus(self):
        """
        Returns True if all nodes are ready
        """
        cmdStr = "kubectl get nodes 2>/dev/null"
        stdout, stderr, status = self.execKubeMaster(cmdStr)
        stdout = stdout + stderr
        dlog.info(stdout)
        if status != 0 or len(stdout.splitlines()) < 3:
            dlog.info("Number of nodes less than two, cluster is not ready")
            return False

        # Check if each node is in Ready State
        for line in stdout.splitlines():
            if "NAME" in line:
                continue
            line = line.split()
            node = line[0]
            if 'NotReady' in line[1]:
                dlog.info("%s is not in Ready state" % node)
                return False
            else:
                dlog.info("%s is in Ready state" % node)
        return True

    def getQueenNode(self):

        cmdstr = 'kubectl get -o template po queen --namespace=cloud-aster --template={{.spec.nodeName}}'
        dlog.info(cmdstr)
        stdout, stderr, status = self.execKubeMaster(cmdstr, timeout=30)
        dlog.info(stdout)
        queenNodes = []
        if stdout is not None:
            nodeName = stdout.splitlines()[0] + '.' + self.domainName
            queenNodes.append(nodeName)
        return queenNodes

    def getWorkerNode(self, workername):

        cmdstr = 'kubectl get -o template po %s --namespace=cloud-aster --template={{.spec.nodeName}}' % workername
        dlog.info(cmdstr)
        stdout, stderr, status = self.execKubeMaster(cmdstr, timeout=30)
        dlog.info(stdout)
        workerNodes = []
        if stdout is not None:
            nodeName = stdout.splitlines()[0] + '.' + self.domainName
            workerNodes.append(nodeName)
        return workerNodes

    def getContainerId(self, nodeId, type='queendb'):

        cmdstr = 'docker ps | grep %s' % type

        stdout, stderr, status = self.execKubeNode(cmdstr, node=nodeId)
        containerId = stdout.splitlines()[0].split()[0]
        return containerId

    def getQueenPodIp(self):
        # Get the queen pod IP
        kubeCmd = "kubectl get -o template po queen --namespace=cloud-aster --template={{.status.podIP}}"
        stdout, stderr, status = self.execKubeMaster(kubeCmd)
        dlog.info("Queen pod IP is %s" % stdout)
        if status != 0:
            dlog.error("Error in running %s. Error: %s" % (kubeCmd, stderr))
        return stdout.strip()

    def queenContainerExecCommand(self, commandStr, container = 'queendb', node=0, timeout=60):
        '''
        Execute a command on the Queen container in the kubernetes aster cluster
        return: The stdout,stderr,status from the
        '''

        containerId = self.getContainerId(node, container)
        dlog.info("Executing after connecting to a container..")
        cmdstr = 'docker exec -i %s /bin/bash -c "%s" ' % (containerId, commandStr)
        stdout, stderr, status = self.execKubeNode(cmdstr, node=node, timeout=timeout)

        return stdout, stderr, status

    def workerContainerExecCommand(self, commandStr, container='runner', node=1, timeout=60):
        '''
        Execute a command on the Queen container in the kubernetes aster cluster
        return: The stdout,stderr,status from the
        '''

        containerId = self.getContainerId(node, container)
        dlog.info("Executing after connecting to a container..")
        cmdstr = 'docker exec -i %s /bin/bash -c "%s" ' % (containerId, commandStr)
        stdout, stderr, status = self.execKubeNode(cmdstr, node=node, timeout=timeout)

        return stdout, stderr, status

    def excNcliCommand(self, ncliCommandStr, node=0, timeout=60):
        passwd = base64.b64decode('YXN0ZXI0ZGF0YQ==')

        # Get the queen pod IP
        queenPodIp = self.getQueenPodIp()
        # Execute ncli command on astershell
        commandStr = 'ssh-keygen -f \"/root/.ssh/known_hosts\" -R %s' % queenPodIp
        stdout, stderr, status = self.execKubeNode(commandStr, node, timeout)
        commandStr = "sshpass -p %s ssh -o StrictHostKeyChecking=no beehive@%s '%s'" % (passwd, queenPodIp, ncliCommandStr)
        stdout, stderr, status = self.execKubeNode(commandStr, node, timeout)
        return stdout, stderr, status

    def copyToContainer(self, containerId, from_location, to_location, node=0, timeout=60):
        """
        Copy a file from the localhost to inside a running container
        """
        cp_cmd = "docker cp %s %s:%s" % (from_location, containerId, to_location)
        stdout, stderr, status = self.execKubeNode(cp_cmd, node, timeout)
        dlog.info(stdout + stderr)
        if status != 0:
            return False
        return True

    def copyFromContainer(self, containerId, from_location, to_location, node=0, timeout=60):
        """
        Copy a file from inside a running container to  the localhost
        """
        cp_cmd = "docker cp  %s:%s %s" % (containerId,from_location, to_location)
        dlog.info(cp_cmd)
        stdout, stderr, status = self.execKubeNode(cp_cmd, node, timeout)
        dlog.info(stdout + stderr)
        if status != 0:
            return False
        return True
