import re
import os
import sys
import subprocess

def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )

    stdout, stderr = proc.communicate()
    status = proc.poll()

    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout, stderr

def getAsterConnectorFromJenkins(hudsonuser,hudsonpass,branch):
    b = "drops"
    if(branch == "master"):
        b = "main"
    curl_for_file = "curl -u " + hudsonuser + ":" + hudsonpass +" https://hudson-master.asterdata.com/job/beehive-compile-" + b + "/lastSuccessfulBuild/artifact/AsterConnector/distributions/tdqg-tdmle-connector-*.tar.gz"
    stat, std, err = execCmdLocal(curl_for_file)
    data = std.split(" ")
    if('ERROR' not in data):
        tarfile = []
        for i in range(len(data)):
            if("tdqg-tdmle-connector" in data[i] and "href" in data[i] and "*" not in data[i]):
                tarfile.append(data[i])
        tar = tarfile[0].split("\"")[1].strip("./")
        print(tar)
        tat,st,err = execCmdLocal("cd /root/pyscripts;curl -u " + hudsonuser + ":" + hudsonpass + " -O https://hudson-master.asterdata.com/job/beehive-compile-" + b + "/lastSuccessfulBuild/artifact/AsterConnector/distributions/"+tar)
        #stat, std, err = execCmdLocal("mv " + tar + " t" + tar.strip(".tar.gz") + "-" + branch + ".tar.gz")

def getAnaltyticsPlatformFromJenkins(hudsonuser,hudsonpass,RevisionNumber,branch):
    b = "drops"
    if(branch == "master"):
        b = "main"
    curl_for_file = "curl -u " + hudsonuser + ":"+ hudsonpass +" https://hudson-master.asterdata.com/job/all-packages-" + b + "/lastSuccessfulBuild/artifact/beehive/build/rpm/analytics-platform-installer*.rpm"
    stat, std, err = execCmdLocal(curl_for_file)
    data = std.split(" ")
    tarfile = []
    if('ERROR' not in data):
        for i in range(len(data)):
            if("analytics-platform-installer" in data[i] and "href" in data[i] and "*" not in data[i]):
                tarfile.append(data[i])
        tar = tarfile[0].split("\"")[1].strip("./")
        print(tar)
        tat,st,err = execCmdLocal("cd /root/pyscripts;curl -u " + hudsonuser + ":" + hudsonpass + " -O https://hudson-master.asterdata.com/job/all-packages-drops/lastSuccessfulBuild/artifact/beehive/build/rpm/"+tar)
        stat, std, err = execCmdLocal("mv analytics-platform-installer.rpm analytics-platform-installer-" + RevisionNumber + "-" + branch + ".x86_64.rpm") 

def pushAsterConnectorSnapshot(branch,drop):
    getAsterConnectorFromJenkins(branch)
    stat, std, err = execCmdLocal("curl -u da230151:CALLORuter92@$ -T tdqg-tdmle-connector-* https://sdartifact.td.teradata.com/artifactory/pkgs-generic-snapshot-sd/promethium-install/" + drop + "/qg_pkgs/")
    print("pushed Aster Connector to Snapshot")
    stat, std, err = execCmdLocal("rm tdqg-tdmle-connector-*")

def pushAnalyticsPlatformSnapshot(branch,RevisionNumber,drop):
    getAnaltyticsPlatformFromJenkins(RevisionNumber,branch)
    stat, std, err = execCmdLocal("curl -u da230151:CALLORuter92@$ -T analytics-platform-installer* https://sdartifact.td.teradata.com/artifactory/pkgs-generic-snapshot-sd/promethium-install/" + drop + "/analytic-platform-installer/")
    print("pushed Analytics platform to Snapshot")
    stat, std, err = execCmdLocal("rm analytics-platform-installer*")

def pushAsterConnectorQA():
    getAsterConnectorFromJenkins()
    stat, std, err = execCmdLocal("curl -u da230151:CALLORuter92@$ -T tdqg-tdmle-connector-* https://sdartifact.td.teradata.com/artifactory/pkgs-generic-qa-sd/promethium-install/drop24/qg_pkgs/")
    print("pushed Aster Connector to QA")

def pushAnalyticsPlatformQA():
    getAnaltyticsPlatformFromJenkins(RevisionNumber,branch)
    stat, std, err = execCmdLocal("curl -u da230151:CALLORuter92@$ -T analytics-platform-installer* https://sdartifact.td.teradata.com/artifactory/pkgs-generic-qa-sd/promethium-install/drop24/analytic-platform-installer/")
    print("pushed Analytics platform to QA")
    stat, std, err = execCmdLocal("rm analytics-platform-installer*")



if __name__ == '__main__':
    #getAsterConnectorFromJenkins()
    #getAnaltyticsPlatformFromJenkins()
    if(sys.argv[4] == "snapshot"):
        pushAsterConnectorSnapshot(sys.argv[1],sys.argv[3])
        pushAnalyticsPlatformSnapshot(sys.argv[1],sys.argv[2],sys.argv[3])
    elif(sys.argv[4] == "qa"):
         pushAsterConnectorQA()
         pushAnalyticsPlatformQA()
    #getAsterConnectorFromJenkins(sys.argv[2])
    #getAnaltyticsPlatformFromJenkins(sys.argv[1],sys.argv[2])
