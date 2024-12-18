import json
import os
import collections

from lib.DartDBConnect import DartDBConnect

class DartFailedTestParser():

    def __init__(self, dbHost, dbName):
        self.dbHost = dbHost
        self.dbName = dbName
        self.test = {}
        self.failedTest = {}
        self.failedTestName = []


    def __getTestInfo(self, runFileList):
        test = {}
        for fileName in runFileList:
            #fileName = os.path.abspath(os.path.dirname(__file__)) + '/testset/' + fileName.strip()
            with open(fileName, "r") as f:
                s = ""
                while True:
                    line = f.readline()
                    if not line:
                        break

                    line_tmp = line.strip()
                    if line_tmp.startswith("#"):
                        continue
                    s = s + line

                t = json.loads(s)
                test.update(t)
        
        return test


    def __getFailedTestName(self, failedTestRunId):
        tests = []
        handler = DartDBConnect(self.dbHost, self.dbName)
        result = handler.selectRows("darttest", "testcase", "run_id='%s' and status='FAIL' or run_id='%s' and status='SKIP' or run_id='%s' and status='ABORT'" %(failedTestRunId, failedTestRunId, failedTestRunId))
        for r in result:
            if type(r) == dict:
                tests.append(r["testcase"])
            else:
                tests.append(r[0])

        return tests


    def __parseFailedTestInfo(self, test, failedTestName):
        failedCount = 0
        for setName in test:
            testset = test[setName]
            testsetList = []
            templateDict = {}
            setupList = []
            teardownList = []
            for t in testset:
                if 'TEMPLATE' in t:
                    templateDict = t

                if 'SETUP' in t:
                    setupList.append(t)

                if 'TEARDOWN' in t:
                    teardownList.append(t)

                if 'NAME' in t and t['NAME'] in failedTestName:
                    testsetList.append(t)
                    failedCount = failedCount + 1

            if len(testsetList) != 0:
                if len(setupList) != 0:
                    testsetList = setupList + testsetList
                if len(templateDict) != 0:
                    testsetList.insert(0, templateDict)
                if len(teardownList) != 0:
                    testsetList.extend(teardownList)

            if setName not in self.failedTest and len(testsetList) != 0:
                self.failedTest[setName] = testsetList


    def ParseFailedTest(self, runFileList, failedTestRunId):
        self.test = self.__getTestInfo(runFileList)

        self.failedTestName = self.__getFailedTestName(failedTestRunId)
        self.__parseFailedTestInfo(self.test, self.failedTestName)

        return collections.OrderedDict(self.failedTest)
