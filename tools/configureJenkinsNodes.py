import os
import sys
import subprocess
sys.path.append(os.path.abspath(os.path.join('lib/', '')))
from SshConnect import SshConnect

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )

    stdout, stderr = proc.communicate()
    status = proc.poll()

    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout, stderr

def connectToNode(server,username,password):
    try:
        queenCon = SshConnect(server,username,password)
        return(queenCon)
    except Exception:
        return("False")

def mountToolChain(server,username,password):
    conn = SshConnect(server,username,password)
    conn.connect()
    out, err, stat = conn.execCommand('apt-get -y install nfs-common;mkdir /asterfs;mkdir /asterfs/enghome;mkdir /asterfs/engtools_nobackup;mkdir /asterfs/engtools;mkdir /home/beehive; mkdir /root/workspace')
    stdout, stderr, stdstat = conn.execCommand('mount asterfs2.labs.teradata.com:/enghome /asterfs/enghome;mount asterfs2.labs.teradata.com:/engtools_nobackup /asterfs/engtools_nobackup;mount asterfs2.labs.teradata.com:/engtools /asterfs/engtools')
    print("aster mounted on vm")
    linkout, linkster, linkstats = conn.execCommand("ln -s /asterfs/engtools/toolchain /home/beehive/toolchain;ln -s /asterfs/engtools/xc-toolchain /home/beehive/xc-toolchain;ln -s /home/beehive/toolchain/x86_64-unknown-linux-gnu/aster-tcmain/asterdb-1GB-32KB/ /home/beehive/sqlstore")
    print("linked the toolchain to beehive")

#things to install: paramiko,docker,kubernetes,ansible,paramiko
def InstallDependencies(server,username,password):
    conn = SshConnect(server,username,password)
    conn.connect()
    #javaout, javaerr, javastat = conn.execCommand("apt-add-repository ppa:webupd8team/java -y;apt-get update;apt-get -y install oracle-java8-installer;apt-get -y install git;apt-get -y install rpm2cpio;apt-get -y install rpm;apt-get -y install rpmbuild")
    print("install java")
    ansiout, ansierr, ansistat = conn.execCommand("apt-get update;apt-get -y install software-properties-common;apt-add-repository ppa:ansible/ansible;apt-get update;apt-get -y install ansible;")
    nodeout, nodeerr, nodestat  = conn.execCommand("echo 'hello'")
    print("installed ansible")
    kubeout,kuberr,kubestat = conn.execCommand("cd root/workspace;curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl;chmod +x ./kubectl;mv ./kubectl /usr/local/bin/kubectl")
    print("installed kubernetes")
    dockout,dockerr,dockstat = conn.execCommand("mkdir /etc/apt/sources.list.d/docker.list;echo 'deb https://apt.dockerproject.org/repo ubuntu-trusty main' > /etc/apt/sources.list.d/docker.list;apt-get update;apt-get install -y docker-engine=1.12.3-0~trusty;gpasswd -a " + str(username) + " docker")
    print("installed docker")
    paraout,paraerr,parastat = conn.execCommand("cd root/workspace;wget https://pypi.python.org/packages/23/54/3a88b35388f0df0a12d8cccc3f7f80d4c689c24600dd64a100b7b3dff6c6/paramiko-1.16.0.tar.gz#md5=7e1203f5ffeb7d2bc2bffc4feb80421;wget https://pypi.python.org/packages/f9/e5/99ebb176e47f150ac115ffeda5fedb6a3dbb3c00c74a59fd84ddf12f5857/ecdsa-0.13.tar.gz#md5=1f60eda9cb5c46722856db41a3ae6670;wget https://pypi.python.org/packages/60/db/645aa9af249f059cc3a368b118de33889219e0362141e75d4eaf6f80f163/pycrypto-2.6.1.tar.gz#md5=55a61a054aa66812daf5161a0d5d7eda;tar -xzf ecdsa-0.13.tar.gz;cd ecdsa-0.13;python setup.py install;cd ..;tar -xzf pycrypto-2.6.1.tar.gz;cd pycrypto-2.6.1;python setup.py install;cd ..;tar -xzf paramiko01.16.0.tar.gz;cd paramiko01.16.0;python setup.py install")
    print("installed all dependencies")
    
#install coverity
def InstallCoverity(server,username,password):
    conn = SshConnect(server,username,password)
    conn.connect()
    serverout,servererr,serverstat = execCmdLocal("sshpass -p '" + password + "' scp -r /home/beehive/cov-analysis-linux64-2017.07 " + username + "@" + server + ":/home/beehive/cov-analysis-linux64-2017.07")
    print("move coverity to server")
    serverout,servererr,serverstat = conn.execCommand("echo 'export PATH=$PATH:/home/beehive/cov-analysis-linux64-2017.07/bin' >> ~/.bash_profile")
    print("adding coverity to the path")

def installNode(server,username,password):
    conn = SshConnect(server,username,password)
    conn.connect()
    serverout,servererr,serverstat = conn.execCommand("cd /root;wget https://nodejs.org/dist/v8.11.1/node-v8.11.1-linux-x64.tar.xz;tar xvf node-v8.11.1-linux-x64.tar.xz;cd /usr/bin;ln -s ~/node-v8.11.1-linux-x64/bin/node node;rm -rf node-v8.11.1-linux-x64;rm node-v8.11.1-linux-x64.tar.xz")
    print("installing node js")
    
if __name__ == '__main__':
    print(sys.argv)
    if(len(sys.argv) == 4):
        print("server: " + sys.argv[1])
        print("username: "+ sys.argv[2])
        print("password: "+ sys.argv[3])
        mount = raw_input("Do you want to mount toolchain?Yes or No ")
        if(mount.lower() == 'yes'):
            mountToolChain(sys.argv[1],sys.argv[2],sys.argv[3])
        dependencies = raw_input("Do you want to install dependencies?Yes or No ")
        if(dependencies.lower() == 'yes'):
            InstallDependencies(sys.argv[1],sys.argv[2],sys.argv[3])
        coverity = raw_input("Do you want to install coverity?Yes or No ")
        if(coverity.lower() == 'yes'):
            InstallCoverity(sys.argv[1],sys.argv[2],sys.argv[3])
        node = raw_input("Do you want to install node.js?Yes or No ")
        if(node.lower() == 'yes'):
            installNode(sys.argv[1],sys.argv[2],sys.argv[3])
    else:
        print("you need at least 3 parameters other than the file. The three are param1:server,param2:username,param3:password")
