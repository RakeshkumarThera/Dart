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

cmdStr = 'docker images | grep arc | grep -v latest | grep -v \'.com\' | grep %s'%id
ret = execCmdLocal(cmdStr)
out = ret[1]
revision = out.split()[1]
print(revision)
