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
# DESCRIPTION: DartTestResultsDetail Class generates data which is
#              showed on /summaryDetail page

import numpy as np
from operator import itemgetter

from DartDBHandler import DartDBHandler

class DartTestResultsDetail:

    def __init__(self, handler):
        self.handler = handler


    def __getAllValuesToList(self, dicts):
        l = []
        for d in dicts:
            if d.values()[0] is None:
                continue
            l = l + d.values()

        return sorted(l)


    def __getEncodedDict(self, itemList):
        d = {}

        for i in range(len(itemList)):
            d[itemList[i]] = i

        return d


    def __getRunIdWithMaxTestcaseCount(self, releaseName, buildNumber):
        results = self.handler.select("dartruninfo", "release_name='%s' and build_number='%s' order by start_time" %(releaseName, buildNumber), \
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
        


    def __getBuildNumberByComponent(self, releaseName, component, osVersions, dbTypes):
        l = []
        for os in osVersions:
            for d in dbTypes:
                res = self.handler.select("darttest", "test_component='%s' and os_version='%s' and db_version='%s'  \
                                      and build_number<>'' and release_name='%s' order by start_time limit 1" %(component, os, d, releaseName), \
                                     "run_id,build_number,test_component,os_version,db_version", "")

                if len(res) != 0:
                    component = res[0]['test_component']
                    buildNumber = res[0]['build_number']
                    runId = self.__getRunIdWithMaxTestcaseCount(releaseName, buildNumber) 
                    columns = "(select revision from darttest where test_component='%s' and build_number='%s' and run_id='%s' limit 1) as revision, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=1 and run_id='%s') as total_p1, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=2 and run_id='%s') as total_p2, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=3 and run_id='%s') as total_p3, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=1 and status='PASS' and run_id='%s') as pass_p1, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=2 and status='PASS' and run_id='%s') as pass_p2, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=3 and status='PASS' and run_id='%s') as pass_p3, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=1 and status<>'PASS' and run_id='%s') as fail_p1, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=2 and status<>'PASS' and run_id='%s') as fail_p2, " \
                              "(select count(testcase) from darttest where test_component='%s' and build_number='%s' and priority=3 and status<>'PASS' and run_id='%s') as fail_p3 " \
                              %(component, buildNumber, runId, component, buildNumber, runId, component, buildNumber, runId, \
                                component, buildNumber, runId, component, buildNumber, runId, component, buildNumber, \
                                runId, component, buildNumber, runId, component, buildNumber, runId, component, buildNumber, runId, component, buildNumber, runId)

                    count = self.handler.selectByTestResultDetail("select " + columns)
                    if count[0]['revision'] is None and count[0]['total_p1'] == 0 and count[0]['total_p2'] == 0 and count[0]['total_p3'] == 0 and  \
                       count[0]['pass_p1'] == 0 and count[0]['pass_p2'] == 0 and count[0]['pass_p3'] == 0 and  \
                       count[0]['fail_p1'] == 0 and count[0]['fail_p2'] == 0 and count[0]['fail_p3'] == 0:
                           continue
                    res[0]['revision'] = count[0]['revision']

                    res[0]['total'] = {}
                    res[0]['total']['high'] = count[0]['total_p1']
                    res[0]['total']['mid'] = count[0]['total_p2']
                    res[0]['total']['low'] = count[0]['total_p3']
                   
                    res[0]['pass'] = {}
                    res[0]['pass']['high'] = count[0]['pass_p1']
                    res[0]['pass']['mid'] = count[0]['pass_p2']
                    res[0]['pass']['low'] = count[0]['pass_p3']
                    
                    res[0]['fail'] = {}
                    res[0]['fail']['high'] = count[0]['fail_p1']
                    res[0]['fail']['mid'] = count[0]['fail_p2']
                    res[0]['fail']['low'] = count[0]['fail_p3']

                    l = l + res

        return l


    def __getBuildNumber(self, releaseName, components, osVersions, dbTypes):
        data = []
        for component in components:
            l = self.__getBuildNumberByComponent(releaseName, component, osVersions, dbTypes)
            data = data + l

        data = sorted(data, key=itemgetter('test_component'))

        return data


    def __generateResponseData(self, dataDicts, componentsEncodedDict, osEncodedDict, dbTypeEncodedDict):
        dataArray = np.ndarray((len(componentsEncodedDict), len(osEncodedDict) * len(dbTypeEncodedDict) + 1), dtype='object')
        dataArray.fill("")

        for data in dataDicts:
            osPos = osEncodedDict[data['os_version']]
            dbTypePos = dbTypeEncodedDict[data['db_version']]
            colIndex = (osPos * len(dbTypeEncodedDict)) + dbTypePos + 1
            rowIndex = componentsEncodedDict[data['test_component']]
            dataArray[rowIndex][0] = data['test_component']
            dataArray[rowIndex][colIndex] = {'build_number': data['build_number'], 'revision': data['revision'], 'total': data['total'], \
                                             'pass': data['pass'], 'fail': data['fail'], 'run_id': data['run_id']}

        return dataArray


    def __renameHeader(self, headers):
        for key in headers:
            if "SUSE" in headers[key]:
                headers[key] = headers[key].replace(" ", "")
            elif "RedHatEnterpriseServer" in headers[key]:
                headers[key] = headers[key].replace("RedHatEnterpriseServer", "RHEL")
            elif "-cdh" in headers[key] or "-hdp" in headers[key]:
                headers[key] = headers[key].split("-")[1]

        return headers


    def getTestResultsDetail(self, releaseName): 
        osDict = self.handler.select("darttest", "os_version<>'' order by os_version", "distinct os_version", "")
        osVersions = self.__getAllValuesToList(osDict)
        osEncodedDict = self.__getEncodedDict(osVersions)

        dbTypeDict = self.handler.select("darttest", "release_name='%s' and release_name<>'Private' and db_version <>'' order by db_version" %releaseName, "distinct db_version", "")
        dbTypes = self.__getAllValuesToList(dbTypeDict)
        dbTypeEncodedDict = self.__getEncodedDict(dbTypes)

        componentDict = self.handler.select("darttest", "release_name='%s' and release_name<>'Private'" %releaseName, "distinct test_component", "")
        components = self.__getAllValuesToList(componentDict)
        #componentsEncodedDict = self.__getEncodedDict(components)

        dataDicts = self.__getBuildNumber(releaseName, components, osVersions, dbTypes)
        components = []
        for data in dataDicts:
            if data['test_component'] not in components:
                components.append(data['test_component'])

        componentsEncodedDict = self.__getEncodedDict(components)
        resData = self.__generateResponseData(dataDicts, componentsEncodedDict, osEncodedDict, dbTypeEncodedDict)

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
    dartdbHostname = "127.0.0.1"
    dartdbName = "dartdb"
    dartdbUser = "dart"
    dartdbPassword = "aster4data"
    handler = DartDBHandler(dartdbHostname, dartdbName, dartdbUser, dartdbPassword)
    d = DartTestResultsDetail(handler)
    #d.getTestResultsDetail("AX7.0 FFR2")
    d.getTestResultsDetail("AD6.20")
