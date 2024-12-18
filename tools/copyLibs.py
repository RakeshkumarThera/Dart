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


ret = execCmdLocal('cp ../../common/bin/* ../build/bin/')
out = ret[1]
print(out)

ret = execCmdLocal('cp -r ../../common/jars ../build/jars')
out = ret[1]
print(out)

ret = execCmdLocal('cp -r ../../common/pkg/* ../build/pkg/')
out = ret[1]
print(out)

ret = execCmdLocal('cp -r ../../common/lib/* ../build/lib/')
out = ret[1]
print(out)

