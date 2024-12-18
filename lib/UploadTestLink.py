#
# Unpublished work.
# Copyright (c) 2011-2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: This module will upload Dart test results to TestLink

from Dlog import dlog
import traceback

class UploadTestLink(object):

    def __init__(self, testResults):
        #testResults = [testProject, testPlan, buildName, tester, executionTimeStamp, testSuite, testCase, testResult, duration, notes]:
        
        self.testResults = testResults
        
        
    def load(self):
        

        
        if 'testlinkDB' not in self.testResults:
            dlog.error('testlinkDB is required!')
            return False
        testlinkDB = self.testResults['testlinkDB']
        
        if 'testlinkUser' not in self.testResults:
            dlog.error('testlinkUser is required!')
            return False
        testlinkUser = self.testResults['testlinkUser']
        
        if 'testlinkPass' not in self.testResults:
            dlog.error('testlinkPass is required!')
            return False
        testlinkPass = self.testResults['testlinkPass']
        
        if 'testlinkServer' not in self.testResults:
            dlog.error('testlinkServer is required!')
            return False
        testlinkServer = self.testResults['testlinkServer']
        
        if 'testlinkPort' not in self.testResults:
            dlog.error('testlinkPort is required!')
            return False
        testlinkPort = self.testResults['testlinkPort']
        
        if 'testProject' not in self.testResults:
            dlog.error('testProject is required!')
            return False
        testProject = self.testResults['testProject']
        if 'testPlan' not in self.testResults:
            dlog.error('testPlan is required!')
            return False
        testPlan = self.testResults['testPlan']
        if 'buildName' not in self.testResults:
            dlog.error('buildName is required!')
            return False
        buildName = self.testResults['buildName']
        
        if 'tester' not in self.testResults:
            dlog.error('tester is required!')
            return False
        tester = self.testResults['tester']


        if 'testSuiteId' not in self.testResults:
            dlog.error('testSuiteId is required!')
            return False
        testSuiteId = self.testResults['testSuiteId']
        
        if 'testCase' not in self.testResults:
            dlog.error('testCase is required!')
            return False
        testCase = self.testResults['testCase']
        
        if 'tcVersion' in self.testResults:
            tcVersion = self.testResults['tcVersion']
        else:
            tcVersion = '1'
        
        if 'status' not in self.testResults:
            dlog.error('status is required!')
            return False
        status = self.testResults['status']
        if status == 'Pass':
            testStatus = 'p'
        elif status == 'Fail':
            testStatus = 'f'
        elif status == 'Blocked':
            testStatus = 'b'
        else:
            testStatus = 'f'
            
        if 'executionTimeStamp' not in self.testResults:
            dlog.error('executionTimeStamp is required!')
            return False
        executionTimeStamp = self.testResults['executionTimeStamp']
        if 'duration' not in self.testResults:
            dlog.error('duration is required!')
            return False
        duration = self.testResults['duration']
        
        notes = ''
        if 'notes' in self.testResults:
            notes = self.testResults['notes']
       
        executionMode = '2'
        if 'executionMode' in self.testResults:
            executionMode = self.testResults['executionMode']
            
            
        #Custom Fields
        buildInfo = None
        if 'buildInfo' in self.testResults:
            buildInfo = self.testResults['buildInfo']
        
        clusterInfo = None   
        if 'clusterInfo' in self.testResults:
            clusterInfo = self.testResults['clusterInfo']
        
        hadoopType = None
        if 'hadoopType' in self.testResults:
            hadoopType = self.testResults['hadoopType']
            
        kernelVersion = None
        if 'kernelVersion' in self.testResults:
            kernelVersion = self.testResults['kernelVersion']
            
        osVersion = None
        if 'osVersion' in self.testResults:
            osVersion = self.testResults['osVersion']
            
        platformType = None
        if 'platformType' in self.testResults:
            platformType = self.testResults['platformType']
            
        testCategory = None
        if 'testCategory' in self.testResults:
            testCategory = self.testResults['testCategory']
            
        testComponent = None
        if 'testComponent' in self.testResults:
            testComponent = self.testResults['testComponent']
       
        try:
            import psycopg2
        except ImportError:
            dlog.info('The python module psycopg2 is not installed! Install this module using \'pip install psycopg2\' command')
            return False
        conn = psycopg2.connect(database=testlinkDB, user=testlinkUser, password=testlinkPass, host=testlinkServer, port=testlinkPort)
        cur = conn.cursor()
        # Get the project id
        sqlStr = "select id from nodes_hierarchy where node_type_id = '1' and name = '" + testProject + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        testProjectId = None
        for row in rows:
            testProjectId = str(row[0])
            dlog.debug ("Project Id = %s" % testProjectId)
        if testProjectId == None:
            dlog.info('The Project Id is not valid! Please check the Project Id %s' % testProject)
            return False
        
        #Get the testPlanId
        testPlanId = None
        sqlStr = "select id from nodes_hierarchy where node_type_id = '5' and parent_id = '" + testProjectId + "' and name = '" + testPlan + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            testPlanId = str(row[0])
            dlog.debug ("Plan Id = %s" % testPlanId)
        if testPlanId == None:
            dlog.info('The Project Id and the Test Plan combination is not returning any values. Please check the validity of the TestPlan Name! %s ' % testPlan)
            return False
        
        #Get the buildId
        buildId = None
        sqlStr = "select id from builds where testplan_id = '" + testPlanId + "' and name like '%" + buildName + "%'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            buildId = str(row[0])
            dlog.debug("Build Id = %s" % buildId)
        if buildId == None:
            dlog.info('The Build Name is not not valid for the TestPlan! Please check the Build Name! %s' % buildName)
            return False
        
        #Get the testerId
        testerId = None
        sqlStr = "select id from users where login = '" + tester + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            testerId = str(row[0])
            dlog.debug ("tester Id = %s" % testerId )    
        if testerId == None:
            dlog.info('The tester Name is  not valid! Please check TestLink! %s' % tester)
            return False
        
        #Get the testcase_id
        testCaseId = None
        sqlStr = "select id from nodes_hierarchy where node_type_id = '3' and name = '"  \
                    + testCase + "' and parent_id = '" + testSuiteId + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            testCaseId = str(row[0])
            dlog.debug("TestCase Id = %s" % testCaseId )
        if testCaseId == None:
            dlog.info('The testCase and the testSuiteId combination  is  not valid! %s %s' % (testSuiteId, testCase))
            return False
        
        #Get the tcversion_id
        tcVersionId = None
        sqlStr = "select id from nodes_hierarchy where node_type_id = '4' and parent_id = '" + testCaseId + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            nodeId = str(row[0])
            sqlStr1 = "select id from tcversions where id = '" + nodeId + "' and version = '" + tcVersion + "'"
            cur1 = conn.cursor()
            cur1.execute(sqlStr1)
            rows1 = cur1.fetchall()
            for row1 in rows1:
                tcVersionId = str(row1[0])
                dlog.debug ("tcVersion Id = %s" % tcVersionId) 
            
        if tcVersionId == None:
            dlog.info('The testCase and the testSuiteId combination  is  not valid! %s %s' % (testSuiteId, testCase))
            return False
        
        
        dlog.info ('Test Version %s' % tcVersion)
        dlog.info ('Test Execution Mode %s' % executionMode)
        dlog.info ('Test Status %s ' % testStatus)
        dlog.info ('Test Execution Time Stamp %s' % executionTimeStamp)
        dlog.info ('Test Duration %s' % duration)
        dlog.info ('Test Notes %s' % notes)
        
        #Insert into testLink
        insertStr = "insert into executions (build_id, tester_id, execution_ts, status, testplan_id," \
                    + "tcversion_id, tcversion_number, execution_type, execution_duration, notes ) " \
                    + "values ( '" + buildId + "','" + testerId  + "','" + executionTimeStamp \
                    + "','" + testStatus + "','" + testPlanId + "','" + tcVersionId + "','" + \
                    tcVersion + "','" + executionMode + "','" + duration + "','" + notes + "' )" 
        dlog.debug(insertStr)
        cur2 = conn.cursor()
        cur2.execute(insertStr);
        conn.commit()
        
        #Get the executionId
        executionId = None
        sqlStr = "select id from executions where build_id = '" + buildId + "' and tester_id = '" \
        + testerId + "' and execution_ts = '" +  executionTimeStamp + "' and status = '" \
        + testStatus + "' and testplan_id = '" + testPlanId + "' and tcversion_number = '" \
        + tcVersion + "' "
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            executionId = str(row[0])
            dlog.debug("Execution Id = %s" % executionId )
        if executionId == None:
            dlog.info('Unable to fetch the execution id! The Insert must have failed!')
            return False
        
        #Get the tcStepId
        tcStepId = None
        sqlStr = "select id from nodes_hierarchy where node_type_id = '9' and parent_id = '" + tcVersionId + "'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            tcStepId = str(row[0])
            dlog.debug ("tcStep Id = %s" % tcStepId)
            #Insert into testLink
            insertStr = "insert into execution_tcsteps (execution_id, tcstep_id, status, notes ) " \
                    + "values ( '" + executionId + "','" + tcStepId  + "','"  + testStatus \
                    + "','"  + notes + "' )" 
            dlog.debug(insertStr)
            cur3 = conn.cursor()
            cur3.execute(insertStr);
            conn.commit()
        
        #Get the custom Field Ids
        customFieldId = None
        sqlStr = "select id from custom_fields where show_on_execution = '1'"
        cur.execute(sqlStr)
        rows = cur.fetchall()
        for row in rows:
            customFieldId = str(row[0])
            dlog.debug("customField Id = %s" % customFieldId)
            if customFieldId == '3' and buildInfo:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + buildInfo + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '4' and clusterInfo:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + clusterInfo + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '5' and hadoopType:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + hadoopType + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '6' and kernelVersion:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + kernelVersion + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '7' and osVersion:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + osVersion + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '8' and platformType:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + platformType + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '9' and testCategory:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + testCategory + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()
            if customFieldId == '10' and testComponent:
                insertStr = "insert into cfield_execution_values (field_id, execution_id, testplan_id, tcversion_id, value ) " \
                    + "values ( '" + customFieldId + "','" + executionId  + "','"  + testPlanId \
                    + "','"  + tcVersionId  + "','"  + testComponent + "' )"
                cur3 = conn.cursor()
                cur3.execute(insertStr)
                conn.commit()    
            
        conn.close()
        return True
        
            
if __name__ == '__main__':

   

    testResults = {}

    testResults['testlinkDB'] = 'testlinkdb'
    testResults['testlinkUser'] = 'testlink'
    testResults['testlinkPass'] = 'testlink'
    testResults['testlinkServer'] = '10.47.12.71'
    testResults['testlinkPort'] = '5432'
    
    testResults['testProject'] = 'AX7.0 FFR2'
    testResults['testPlan'] = 'Feature Complete Test Plan'
    testResults['buildName'] = 'FC'
    testResults['tester'] = 'naveenw'
    testResults['testSuiteId'] = '8'
    testResults['testCase'] = 'Check for CGroup dependency removal'
    testResults['tcVersion'] = '1'
    testResults['status'] = 'Pass'
 
    testResults['duration'] = '22'
    testResults['notes'] = 'Tests are Auto-Loaded'
    #Custom Fields
    testResults['buildInfo'] = 'Beehive Main'
    testResults['clusterInfo'] = 'hrh013'
    testResults['hadoopType'] = 'Aster'
    testResults['kernelVersion'] = 'Linux'
    testResults['osVersion'] = 'RHEL6.6'
    testResults['platformType'] = 'VM'
    testResults['testCategory'] = 'Functional'
    testResults['testComponent'] = 'Installer'
       

    import time
    ts = time.time()
    import datetime
    timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    #testResults['executionTimeStamp'] = '2016-06-15 15:50:00'
    testResults['executionTimeStamp'] = timeStamp


    try:
        uploadTestLink = UploadTestLink(testResults)
        returnStatus = uploadTestLink.load()
        if returnStatus:
            print('Successfully uploaded the test Results!')
        else:
            print('The test Results Failed to upload!')
    except Exception:
        traceback.print_exc()
    
