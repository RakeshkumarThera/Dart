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
    return stdout, status, stderr

#parse cfg file
def getDataFromHosts(clusterConfig):
    jsonlines = {}
    f=open(clusterConfig, "r")
    lines = f.readlines()
    i = 0
    jsonstr = ""
    #flag for lists for host names and ip's in cfg file
    listflag = False
    datalst = []
    while(i < len(lines)):
        line = lines[i].strip(" ").strip("\n").strip(", ").replace("\"","")
        if(line not in "{[}]"):
            if("{" in line):
                listflag = False
                del lines[i]
                i += 1
            if("[" in line):
                listflag = True
                i += 1
                continue
            if(listflag is True):
                datalst.append(line)
            elif("[" not in line):
                listflag = False
                jsonlines[line.split(":")[0].strip(" ")] = line.split(":")[1].strip(" ")
        i += 1
    x = 0
    #change this if your domain changes
    jsonlines['domain'] = "labs.teradata.com"
    lstlen = len(datalst)
    while(x < lstlen):
        if(":" in datalst[x]):
            val = datalst[x].split(":")
            jsonlines[val[0]] = val[1]
            del datalst[x]
            lstlen -= 1
            continue
        x += 1
    datalst = sorted(datalst)
    for a in range(len(datalst)/2):
        if(a == 0):
            jsonlines['kubemaster'] = [datalst[a+4]+"."+jsonlines['domain'],datalst[a]]
        else:
            jsonlines['kubenode0' + str(a)] = [datalst[a+4]+"."+jsonlines['domain'],datalst[a]]
    
    for k,v in jsonlines.items():
        if v == "{":
            del jsonlines[k]
    return(jsonlines)

def createHosts(clusterConfig):
    data = getDataFromHosts(clusterConfig)
    queenCon = SshConnect(data['kubemaster'][1],"root","aster4data")
    queenCon.connect()
    print(data)
    #print(data['kubemaster'][1])
    nodeout, nodeerr, nodestat  = queenCon.execCommand("cd /root;curl -u sr250064:Baseball123 -O https://sdartifact.td.teradata.com/artifactory/dependencies-released-sd/uda/kubekit/kubekit-configurator/1.1.2.20180504-151315.5467ff1.45/kubekit-configurator-1.1.2.20180504-151315.5467ff1.45.tar.gz;tar -xvf kubekit-configurator-1.1.2.20180504-151315.5467ff1.45.tar.gz;cd kubekit-configurator/")
    print("getting kubekit")
    hostsout, hostserr, hostsstat  = queenCon.execCommand("cd /root/kubekit-configurator;cat example-inventory.yaml")
    writeout, writeerr, writestat  = execCmdLocal("touch hosts.yaml")
    lines = hostsout.split("\n")
    f = open("hosts.yaml","w+")
    servercount = 2
    for line in lines:
        if("ansible_user" in line):
            line = line.split(":")[0] + ": root"
        elif("cluster_name" in line):
            line = line.split(":")[0] + ": Dart_Cluster_" + data['name'].split("-")[len(data['name'].split("-"))-1]
        elif("ansible_ssh_private_key_file" in line):
            line = "    # " + line.strip(" ")
            f.write(line + "\n")
            f.write("    ansible_ssh_pass:" + data['password'] + "\n")
            continue
        elif("ansible_byn1" in line):
            line = "    # " + line.strip(" ")
        elif("ansible_eth0" in line):
            line = "   " + line.split("#")[1]
        elif("kube_api_ssl_port" in  line):
            line = line.replace(line.split(": ")[1],"8081")
        elif("master_schedulable_enabled" in line):
            line = line.replace(line.split(": ")[1],"true")
        elif("<SERVER_DNS_NAME_1>" in line):
            line = "            " + str(data['kubemaster'][0]) + ":"
            f.write(line + "\n")
            f.write("              ansible_host: " + data['kubemaster'][1] + "\n")
            continue
        elif("<SERVER_DNS_NAME_" + str(servercount) + ">" in line):
            line = "            " + str(data['kubenode0' + str(servercount-1)][0]) + ":"
            f.write(line + "\n")
            f.write("              ansible_host: " + data['kubenode0' + str(servercount-1)][1] + "\n")
            servercount += 1
            continue
        elif("ansible_host: <IP>" in line):
            continue
        f.write(line + "\n")
    f.close()
    contentout, contenterr, contentstat  = execCmdLocal("cat hosts.yaml")
    ansibleout, ansibleerr, ansiblestat = queenCon.execCommand("cd /root;curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py;python get-pip.py;python get-pip.py;pip install ansible==2.4.2")
    cleanout, cleanerr, cleanstat  = execCmdLocal("sshpass -p '" + data['password'].strip(" ") + "' scp hosts.yaml root@" + str(data['kubemaster'][1]) + ":/root/kubekit-configurator")
    print("moving hostsfile to kubemaster")
    playbookout, playbookerr, playbookstat = queenCon.execCommand("cd /root/kubekit-configurator;ansible -i hosts.yaml all -m ping")
    print(playbookout)
    playout, playerr, playstat = queenCon.execCommand("cd /root/kubekit-configurator;ansible-playbook -i hosts.yaml kube-cluster.yml")
    print(playout)
    podsout, podserr, podsstat = queenCon.execCommand("kubectl get pods --all-namespaces")
    print(podsout)
    cleanout, cleanerr, cleanstat  = queenCon.execCommand("cd /root;rm /root/kubekit-configurator-1.1.2.20180504-151315.5467ff1.45.tar.gz;rm get-pip.py")
    localcleanout, localcleanerr, localcleanstat  = execCmdLocal("rm hosts.yaml")
if __name__ == '__main__':
    #print(sys.argv)
    #print("queenNode: " + sys.argv[1])
    #print("config_file: "+ sys.argv[2])
    createHosts(sys.argv[1])
