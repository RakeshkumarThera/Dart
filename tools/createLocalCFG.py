import os

currentFileLoc = os.path.abspath(os.path.dirname(__file__))
dirs = currentFileLoc.split('/')
buildLoc = os.path.join(dirs[0],dirs[1],dirs[2],dirs[3])
fileH = open('config/local.cfg','w')
fileH.write('{\n')
fileH.write('	"common": {\n')
lineStr = '		"buildLoc": "/%s/",\n'%buildLoc
fileH.write(lineStr)
lineStr = '		"actLoc": "/%s/build/bin/act",\n'%buildLoc
fileH.write(lineStr)
lineStr = '		"nClusterLoaderLoc": "/%s/build/bin/ncluster_loader"\n'%buildLoc
fileH.write(lineStr)
fileH.write('	},\n')
fileH.write('	"analytics": {\n')
fileH.write('		"AnalyticsPkgLoc": "",\n')
fileH.write('		"AsterConnectorPkgLoc": ""\n')
fileH.write('	}\n')
fileH.write('}\n')
fileH.close()

