import sys
import os
from tempfile import mkstemp

repoHost = 'sdartifact.td.teradata.com'
revision = sys.argv[1]
repoPath = sys.argv[2]
argumentLen = len(sys.argv) -1
if argumentLen > 2:
    repoHost = sys.argv[3]
    if ':' in repoHost:
        vals = repoHost.split(':')
        repoHost = vals[0].strip()

def replaceInFile(filePath, pattern, subst):
    fh, absPath = mkstemp()
    with open(absPath, 'w') as newFile:
        with open(filePath) as oldFile:
            for line in oldFile:
                if pattern in line:
                    newFile.write(subst)
                else:
                    newFile.write(line)

    os.close(fh)
    os.remove(filePath)
    os.rename(absPath, filePath)


dirPath = os.path.abspath(os.path.dirname(__file__))
testRunFile = os.path.join(dirPath,'../testset/AsterInstallOnK8sUpdated.est')
pattern = 'dockerRepoPath'
subst = '			\"dockerRepoPath\" : \"%s/%s\",\n'%(repoPath,revision)
replaceInFile(testRunFile,pattern,subst)

pattern = 'dockerRepoTag'
subst = '			\"dockerRepoTag\" : \"%s\",\n'%revision
replaceInFile(testRunFile,pattern,subst)

if argumentLen > 2:
    pattern = 'dockerRepoHost'
    subst = '			\"dockerRepoHost\" : \"%s\",\n'%repoHost
    replaceInFile(testRunFile,pattern,subst)
