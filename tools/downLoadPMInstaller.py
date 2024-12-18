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


pminstallPkg = sys.argv[1]
buildLoc = sys.argv[2]
cmdStr = 'cd %s; rm -rf multinode; curl -u da230151:CALLORuter92@$ -O %s'%(buildLoc,pminstallPkg)
ret = execCmdLocal(cmdStr)
if ret[0] != 0:
    print(1)
    exit(0)

baseTarFile = pminstallPkg.split('/')[-1]

cmdStr = 'cd %s; tar xvfz %s'%(buildLoc,baseTarFile)
ret = execCmdLocal(cmdStr)
if ret[0] != 0:
    print(1)
    exit(0)

print(0)

