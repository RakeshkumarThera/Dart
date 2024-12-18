import os
import sys
import subprocess
#sys.path.append(os.path.abspath(os.path.join('lib/', '')))                                                                    
#from SshConnect import SshConnect

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )

    stdout, stderr = proc.communicate()
    status = proc.poll()

    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout, stderr

#covStream,covView,covProject
def runStaticAnalysis(pathtoDir):
    os.chdir(pathtoDir)
    os.system("cov-build --dir "  + pathtoDir + " make build")
    os.system("cov-analyze --dir "  + pathtoDir)
    #queenCon = SshConnect('10.25.215.6','sr250064','Baseball123')
    #queenCon.connect()
    #fappend = open("StaticAnalysisLog.txt","a+")
    #f = open("StaticAnalysisLog.txt","w+")
    #stdout, stderr, status = queenCon.execCommand('cd ' + pathtoDir + ';cov-build --dir ' + pathtoDir + ' make build_for_docker')
    #anaout, anaerr, anastatus = queenCon.execCommand('cd ' + pathtoDir + ';cov-analyze --dir ' + pathtoDir)
    #print(anaout)

if __name__ == '__main__':
        #print(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
        directory = sys.argv[1]
        #covStream = sys.argv[3]
        #covView = sys.argv[4]
        #covProject = sys.argv[5]
        runStaticAnalysis(directory)
