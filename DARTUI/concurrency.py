import subprocess
import os, sys, time

def cmd():
    text =  {'command': 'python DartRunner.py -c test_cluster -t C_FAT_R2R.tst  -i NoInstall.tst --releaseName GGR3 -p MLEngine    --buildName beehive-ci-pipeline-main   -l Private '}
    path = '/root/Dart/'
    os.chdir( path )
    process = subprocess.Popen(text['command'], shell=True, stdout=subprocess.PIPE)
    processId = process.pid + 1;
    print type(processId)
    print("process id is:%s"%processId)
    return processId


def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )        
    stdout, stderr = proc.communicate()
    status = proc.poll()
    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status,stdout


def runid(processId):
    time.sleep(20)
    cmdStr = 'cd /root/Dart/log; ls -rt DartRunner*.log | tail -5'
    ret = execCmdLocal(cmdStr)
    logNames = ret[1].split()
    print logNames
    for log in logNames:
        print ("looping lognames %s" %log)
        grep = "cd /root/Dart/log;ls -rt DartRunner*.log | tail -5;grep -i 'Process Id' *"+log
        print ("this is grep command that is to be executed:",grep)
        ret1 = execCmdLocal(grep)
        print ("this is ret1:",ret1)
        x = ret1[1][-6:]
        DartProcessId = x[:-1]
        integer = int(DartProcessId)
        print type(integer)
        if (integer == processId):
            print integer
            print processId
            print("Matched pid is : %s" %processId)
            print log
            runId = ""
   	    print('The DartRunner Log generated is: %s'%log)
  	    with open('/root/Dart/log/' + log, "r") as fd:
 	        for line in fd:
           	    if 'runId' in line:
                        runId = line.split()[-1]
                        print('Run Id: %s'%runId)
                        break
        else: 
            print("Process Ids Does not match")
    return logNames

if __name__ == "__main__":
   processId = cmd()
   runid(processId)
