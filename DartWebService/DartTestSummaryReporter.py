#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: alen.cheng@teradata.com
# Secondary Owner:
#
# DESCRIPTION: DartTestSummaryReporter Class generates data which is
#              showed on /summaryReport page

import numpy as np
from operator import itemgetter

from DartDBHandler import DartDBHandler

class DartTestSummaryReporter:

    def __init__(self, handler):
        self.handler = handler


    def __getAllValuesToList(self, dicts):
        l = []
        for d in dicts:
            if d.values()[0] is None:
                continue
            l = l + d.values()

        return sorted(l)


    def __getRunIdWithMaxTestcaseCount(self, releaseName, buildNumber):
        results = self.handler.select("dartruninfo", "release_name='%s' and build_number='%s' order by start_time desc" %(releaseName, buildNumber), \
                                     "distinct run_id,start_time", "")
        maxTestCaseNumber = 0
        runIdWithMaxCount = ""
        for res in results:
            runId = res['run_id']
            countDict = self.handler.select("darttest", "run_id='%s'" %runId, \
                                      "count(distinct testcase)", "")
            if len(countDict) != 0:
                count = countDict[0]['count']
                if count > maxTestCaseNumber:
                    maxTestCaseNumber = count
                    runIdWithMaxCount = runId

        return runId


    def __getBuildNumberByRelease(self, release, osVersions, dbTypes):
        l = []
        for os in osVersions:
            for d in dbTypes:
                res = self.handler.select("darttest", "release_name='%s' and os_version='%s' and db_version='%s'  \
                                      and build_number<>'' order by start_time desc limit 1" %(release, os, d), \
                                     "run_id,build_number,release_name,os_version,db_version", "")
       
                if len(res) != 0:
                    buildNumber = res[0]['build_number']
                    runId = self.__getRunIdWithMaxTestcaseCount(release, buildNumber)
                    count = self.handler.select("darttest", "run_id='%s' and status<>'PASS' and priority<>3" %runId, "count(distinct testcase)", "")
                    if count[0]['count'] == 0:
                        res[0]['status'] = "PASS"
                    else:
                        res[0]['status'] = "FAIL"
                    l = l + res
        
        return l 


    def __getBuildNumber(self, releases, osVersions, dbTypes):
        data = []
        for release in releases:
            l = self.__getBuildNumberByRelease(release, osVersions, dbTypes)
            data = data + l

        data = sorted(data, key=itemgetter('release_name'))
       
        return data


    def __getEncodedDict(self, itemList):
        d = {}

        for i in range(len(itemList)):
            d[itemList[i]] = i

        return d


    def __generateResponseData(self, dataDicts, releaseEncodedDict, osEncodedDict, dbTypeEncodedDict):
        dataArray = np.ndarray((len(releaseEncodedDict), len(osEncodedDict) * len(dbTypeEncodedDict) + 1), dtype='object')
        dataArray.fill("")

        for data in dataDicts:
            osPos = osEncodedDict[data['os_version']]
            dbTypePos = dbTypeEncodedDict[data['db_version']]
            colIndex = (osPos * len(dbTypeEncodedDict)) + dbTypePos + 1
            rowIndex = releaseEncodedDict[data['release_name']]
            dataArray[rowIndex][0] = data['release_name']
            dataArray[rowIndex][colIndex] = {'build_number': data['build_number'], 'status': data['status'], 'run_id': data['run_id']}

        return dataArray


    def getDataByReleaseName(self, releaseNames):
        dataDicts = []
        for releaseName in releaseNames:
            d = self.handler.select("darttest", "release_name='%s' order by start_time desc" %releaseName, 
                               "distinct build_number,release_name,os_version,db_version", "")
            dataDicts.append(d)

        return dataDicts


    def __renameHeader(self, headers):
        for key in headers:
            if "SUSE" in headers[key]:
                headers[key] = headers[key].replace(" ", "")
            elif "RedHatEnterpriseServer" in headers[key]:
                headers[key] = headers[key].replace("RedHatEnterpriseServer", "RHEL")
            elif "-cdh" in headers[key] or "-hdp" in headers[key]: 
                headers[key] = headers[key].split("-")[1]

        return headers


    def getTestResultsSummary(self, releaseName):
        if releaseName is None:
            osDict = self.handler.select("darttest", "os_version<>'' order by os_version", "distinct os_version", "")
        else:
            osDict = self.handler.select("darttest", "release_name='%s' order by os_version" %releaseName, "distinct os_version", "")
        osVersions = self.__getAllValuesToList(osDict)
        osEncodedDict = self.__getEncodedDict(osVersions)

        if releaseName is None:
            dbTypeDict = self.handler.select("darttest", "release_name<>'Private' and db_version <>'' order by db_version", "distinct db_version", "")
        else:
            dbTypeDict = self.handler.select("darttest", "release_name='%s' order by db_version" %releaseName, "distinct db_version", "")
        dbTypes = self.__getAllValuesToList(dbTypeDict)
        dbTypeEncodedDict = self.__getEncodedDict(dbTypes)

        if releaseName is None:
            releaseDict = self.handler.select("darttest", "release_name<>'Private' and build_number<>''", "distinct release_name", "")
        else:
            releaseDict = self.handler.select("darttest", "release_name='%s' and release_name<>'Private'" %releaseName, "distinct release_name", "")

        releaseNames = self.__getAllValuesToList(releaseDict)
        releaseEncodedDict = self.__getEncodedDict(releaseNames)

        dataDicts = self.__getBuildNumber(releaseNames, osVersions, dbTypes)

        resData = self.__generateResponseData(dataDicts, releaseEncodedDict, osEncodedDict, dbTypeEncodedDict)

        osHeader = dict((v, k) for k, v in osEncodedDict.iteritems())
        osHeader = self.__renameHeader(osHeader)
        dbTypeHeader = dict((v, k) for k, v in dbTypeEncodedDict.iteritems())
        dbTypeHeader = self.__renameHeader(dbTypeHeader)

        res = {}
        res['data'] = resData.tolist()
        res['os_header'] = osHeader
        res['dbtype_header'] = dbTypeHeader

        return res


if __name__ == "__main__":
    pass
