import subprocess
import os

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )
            
    stdout, stderr = proc.communicate()
    status = proc.poll()
        
    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout, stderr


ret = execCmdLocal('docker images | grep arc | grep latest')
out = ret[1]
id = out.split()[2]

cmdStr = 'docker images | grep arc | grep -v latest | grep -v \'.com\' | grep -v centos |  grep %s'%id
ret = execCmdLocal(cmdStr)
out = ret[1]
revision = out.split()[1]
print(revision)


ret = execCmdLocal('docker login sdartifact.td.teradata.com:7001 -u da230151 -p \'CALLORuter92@$\' ')
print(ret) 
ret = execCmdLocal('docker images | grep latest | grep -v centos')
out = ret[1]
outlines = out.split('\n')
for line in outlines:
    #print(line)
    if line.strip() != '':
    	image = line.split()[0]
    	print(image)
	tagStr = 'docker tag %s:%s sdartifact.td.teradata.com:7001/asterdata/ax/docker/stage/%s/%s:%s'%(image,revision,revision,image,revision)
	#print(tagStr)
        ret = execCmdLocal(tagStr)
        #print(ret) 
	pushStr = 'docker push sdartifact.td.teradata.com:7001/asterdata/ax/docker/stage/%s/%s:%s'%(revision,image,revision)
	print(pushStr)
        ret = execCmdLocal(pushStr)
        #print(ret)
