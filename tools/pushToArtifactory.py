import subprocess
import os
import sys

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )
            
    stdout, stderr = proc.communicate()
    status = proc.poll()
        
    if status != 0:
        print("Failed to execute command %s" % cmd)
    return status, stdout, stderr


artifactoryServer = sys.argv[1]
repoPath = sys.argv[2]
ret = execCmdLocal('docker images | grep arc | grep latest')
out = ret[1]
id = out.split()[2]

cmdStr = 'docker images | grep arc | grep -v latest | grep -v \'.com\' | grep -v centos |  grep %s'%id
ret = execCmdLocal(cmdStr)
out = ret[1]
revision = out.split()[1]
print(revision)


ret = execCmdLocal('docker login %s -u da230151 -p \'CALLORuter92@$\' '%artifactoryServer)
print(ret) 
ret = execCmdLocal('docker images | grep latest | grep -v centos')
out = ret[1]
outlines = out.split('\n')
for line in outlines:
    #print(line)
    if line.strip() != '':
        image = line.split()[0]
        #print(image)
        tagStr = 'docker tag %s:%s %s/%s/%s/%s:%s'%(image,revision,artifactoryServer,repoPath,revision,image,revision)
        #print(tagStr)
        ret = execCmdLocal(tagStr)
        #print(ret) 
        pushStr = 'docker push %s/%s/%s/%s:%s'%(artifactoryServer,repoPath,revision,image,revision)
        print(pushStr)
        ret = execCmdLocal(pushStr)
        print(ret)

pushStr = 'curl -u da230151:CALLORuter92@$ -T ../../builds/build-master/pkg/analytics-platform-installer*.rpm https://sdartifact.td.teradata.com/artifactory/pkgs-generic-snapshot-sd/promethium-install/null/analytic-platform-installer/'
print(pushStr)
ret = execCmdLocal(pushStr)
print(ret)


pushStr = 'curl -u da230151:CALLORuter92@$ -T ../../builds/build-master/pkg/tdqg-aster-connector-*gz https://sdartifact.td.teradata.com/artifactory/pkgs-yum-snapshot-sd/promethium-install/null/qg_pkgs/'
print(pushStr)
ret = execCmdLocal(pushStr)
print(ret)

