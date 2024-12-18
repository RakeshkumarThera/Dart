import os
import sys
import subprocess
#sys.path.append(os.path.abspath(os.path.join('lib/', '')))
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

def runTests(pathtoFolder):
    heapcheckruns = {}
    status, stdout, stderr = execCmdLocal("hostname -I")
    server = stdout.split(" ")[0]
    print(server)
    dirs = ['sqlmr','sqlstore','compression','common/database','cloneidsvc','common/base','common/testutils','common/thread','common/storage','clusterservices','txman','common/networking','tools/loggather','directory','procmgmt','loader','upgrade','worker','sysman','qos']
    #dirs = ['common/database']
    prompt = '~]# $'
    queenCon = SshConnect(server,'sr250064','Baseball123')
    queenCon.connect()
    #f = open("/root/pyscripts/log.txt","w+")
    #fappend = open("/root/pyscripts/log.txt","a+")
    logout, logerr, logstat = queenCon.execCommand('touch log.txt')
    fappend = open("log.txt","a+")
    f = open("log.txt","w+")
    for direct in dirs:
        try:
            out, err, stat = queenCon.execCommand('kill `lsof -t -i:19002`;kill `lsof -t -i:19001`')
        except Exception:
            print("There is no processes to kill")
        try:
            stdout, stderr, status = queenCon.execCommand('cd ' + pathtoFolder + ';make -C ' + direct + ' heapcheck')
        except Exception:
            heapcheckruns[direct] = 'FAILURE'
            continue
        print(stdout)
        if(os.path.getsize('log.txt') > 0):
            fappend.write(stdout)
        else:
            f.write(stdout)
        if('ok' in stdout or 'OK' in stdout):
            heapcheckruns[direct] = 'PASSED'
        elif('Failed' in stdout or 'FAILURE' in stdout or 'FAILURES' in stdout):
            heapcheckruns[direct] = 'FAILURE'
        else:
            heapcheckruns[direct] = 'NOT SURE'
        print(heapcheckruns)
        print(direct + " ran")
        print("-"*90)
    
    print(heapcheckruns)
    return(heapcheckruns)

def runOneTest(directory,queenCon):
    stdout, stderr, status = queenCon.execCommand('cd /root/workspace/MLEngine/' + directory + ';make heapcheck')
    if(os.path.getsize('/root/pyscripts/log.txt') > 0):
        fappend.write(stdout)
    else:
        f.write(stdout)
    if('Failed' in stdout or 'FAILURE' in stdout or 'FAILURES' in stdout):
        return('FAILURE')
    elif('ok' in stdout or 'OK' in stdout):
        return('PASSED')
    else:
        return('NOT SURE')
    print(direct + " ran")
    print("-"*90)

def runTestsinParallel():
    heapcheckruns = {}
    pool = mp.Pool(processes=10)
    dirs = ['amc','cloneidsvc','common/base','common/testutils','common/thread','common/storage','common/database','clusterservices','txman','common/networking','tools/loggather','directory','procmgmt','loader','upgrade','worker','sysman','qos','compression']
    queenCon = SshConnect('10.25.215.6','sr250064','Baseball123')
    queenCon.connect()
    for direct in dirs:
        results = pool.apply(runOneTest, args=(direct,queenCon))
        heapcheckruns[direct] = results.get()
    print(heapcheckruns)
    return(heapcheckruns)

def clearFile():
    #f = open('/root/pyscripts/log.txt', 'r+')
    queenCon = SshConnect('10.25.215.6','sr250064','Baseball123')
    queenCon.connect()
    logout, logerr, logstat = queenCon.execCommand('touch log.txt')
    f = open('log.txt', 'r+')
    f.truncate()

if __name__ == '__main__':
    clearFile()
    #print(sys.argv[1])
    runTests(sys.argv[1])
    #runTestsinParallel()
