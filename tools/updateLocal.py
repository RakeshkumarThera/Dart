import sys
import os
from tempfile import mkstemp

analyticsPkgLoc = sys.argv[1]
asterConnectorPkgLoc = sys.argv[2]

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
testRunFile = os.path.join(dirPath,'../config/local.cfg')
pattern = 'AnalyticsPkgLoc'
subst = '			\"AnalyticsPkgLoc\" : \"%s\",\n'%analyticsPkgLoc
replaceInFile(testRunFile,pattern,subst)

pattern = 'AsterConnectorPkgLoc'
subst = '			\"AsterConnectorPkgLoc\" : \"%s\"\n'%asterConnectorPkgLoc
replaceInFile(testRunFile,pattern,subst)
