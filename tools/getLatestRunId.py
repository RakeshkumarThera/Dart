import os
from pprint import pprint
import time
import subprocess

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )
            
    stdout, stderr = proc.communicate()
    status = proc.poll()
    return status, stdout, stderr

time.sleep(3)
cmdStr = 'cd log; ls -rt DartRunner*.log | tail -1;'
ret = execCmdLocal(cmdStr)
#pprint(ret)
if ret[0] == 0:
    logName = 'log/%s'%ret[1].strip()
else:
    print('0')

cmdStr = 'grep run_id= %s | tail -1;'%logName
ret = execCmdLocal(cmdStr)
#pprint(ret)
if ret[0] == 0:
    line = ret[1]
    items = line.split('run_id=')
    runId = items[1].strip()
    print (runId)
else:
    print('0')

