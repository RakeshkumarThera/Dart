import subprocess
import os
import json
import sys
from pprint import pprint

key = sys.argv[1]

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )
            
    stdout, stderr = proc.communicate()
    status = proc.poll()
        
    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout, stderr

dirPath = os.path.abspath(os.path.dirname(__file__))
envFile = os.path.join(dirPath,'../../../settings.env')

with open(envFile) as jsonFile:
    envDict = json.load(jsonFile)

value = envDict[key].strip()
print value,
