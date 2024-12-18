#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: divya.sivanandan@teradata.com
# Secondary Owner: naveen.williams@teradata.com
#
# Description: Wrapper to Schedule and Run tests from Jenkins

import ast
import getopt
import json
import os
import sys
from collections import OrderedDict

# This code is not required if PYTHONPATH is set as an ENV variable
libPath = os.path.abspath(os.path.dirname(__file__)) + '/lib'
sys.path.insert(0, libPath)
libPath = os.path.abspath(os.path.dirname(__file__)) + '/testsrc'
sys.path.insert(0, libPath)


from lib.logger import logger, logfile
from lib.TestlinkDbConnector import TestLink
from Dart import Dart

class TestRunner(object):

    def __init__(self, testlink_file, test_run_config, job_name):
        """
        @summary: Gather the values from input configuration files
        """
        logger.info("Logfile is %s" % logfile)
        # Gather the input variables
        self.testplan = None
        self.testlink_user = None
        self.test_suites = None
        self.project = None
        self.build = None
        self.install_test = None
        self.platform = "VM"
        self.job_name = job_name
        self.testsuite_results = OrderedDict({})
        self.lib_path = os.path.abspath(os.path.dirname(__file__))
        config_file  = os.path.join(self.lib_path, 'schedules', testlink_file)
        testrun_file = os.path.join(self.lib_path, 'schedules', test_run_config)
        try:
            with open(config_file, 'r') as cfg_in:
                configs = json.load(cfg_in)
                self.testlink = configs['testplan']
            if 'project_name' in self.testlink:
                self.project = self.testlink['project_name']
            if 'testplan_name' in self.testlink:
                self.testplan = self.testlink['testplan_name']
            if 'build_name' in self.testlink:
                self.build = self.testlink['build_name']
            if 'user' in self.testlink:
                self.testlink_user = self.testlink['user']
            if 'platform' in self.testlink:
                self.platform = self.testlink['platform']
            if "cluster_config" in self.testlink:
                self.cluster_config = self.testlink["cluster_config"]
            if "install_test" in self.testlink:
                self.install_test = self.testlink["install_test"]

            self.cluster = None
            self.tlinkdb = TestLink()

        except ValueError as e:
            logger.error('The Json File may have syntax issues! Check the config file!')
            logger.error(e)
            logger.error('Exiting Program!')
            sys.exit(2)
        except Exception as e:
            logger.error(e)
            logger.error('The test raised an Unexpected Exception!')
            raise

        if self.testplan is None or self.project is None or self.build is None:
            logger.error("Unable to proceed without testplan, project or build information. exiting")
            sys.exit(2)

        # Get the test_run file information
        try:
            if os.path.isfile(testrun_file):
                tempTestFile = os.path.join('/tmp', test_run_config)
                fileT = open(tempTestFile, 'w')
                # Remove any commented tests from the schedule
                with open(testrun_file, 'r') as f:
                    for line in f:
                        if line.lstrip().startswith('#'):
                            continue
                        fileT.write(line)
                fileT.close()

            with open(tempTestFile, 'r') as tst_in:
                self.test_suites = json.load(tst_in, object_pairs_hook=OrderedDict)
        except ValueError as e:
            logger.error('The testrun_file may be not present or have issues. Please fix and rerun!')
            logger.error(e)
            logger.error('Exiting Program!')
            sys.exit(2)
        except Exception as e:
            logger.error(e)
            logger.error('The test raised an Unexpected Exception!')
            raise

    def main(self):
        """
        1. Read the testrun file
        2. Not in first version: Replace the test_suite_id for the current testplan+project
        3. Read the config file
        4. Modify with current testplan, project and build
        6. Invoke Dart engine with the testCase and config created

        """

        # Check if the given testplan relates to the project specified
        check_sql = "select id from nodes_hierarchy where name='%s' and id=(select " \
                    "parent_id from nodes_hierarchy where name='%s');" % (self.project, self.testplan)
        result =  self.tlinkdb.queryDb(check_sql)
        if not result:
            logger.error("Testplan and Project combination is not correct.Unable to proceed")
            sys.exit(2)

        # Check if the build name belongs to the testplan

        build_sql = "select name from builds where name like '%" + self.build + "%' and testplan_id " \
                    "=(select id from nodes_hierarchy where name='" + self.testplan + "')"
        result = self.tlinkdb.queryDb(build_sql)
        build_name = result[0][0]
        if build_name.strip() != self.build.strip():
            logger.error("The provided build name does not match with whats present for the testplan. Cannot proceed")
            sys.exit(2)

        # TODO: Make this work for various projects
        # testrunfile = self.createNewTestrunFile()

        # Create a cluster_config_file with testlink info
        self.createNewClusterConfig(self.cluster_config)

        # Setup the cluster
        if self.install_test:
            rc = self.setupCluster()
            if not rc:
                logger.error("Setup failed. Cannot proceed with the tests")
                raise Exception('Unable to run any tests. Installation failed.')

        #if the setup passed, continue with the schedule
        rc = self.runSchedule()
        if not rc:
            logger.error("Test Schedule Failed to complete")

        if self.testsuite_results:
                self.generateJunitXml()

    def setupCluster(self):
        """
        @summary: Install and setup the cluster
        """
        install_test_suite = self.testCase(self.install_test)
        testlist = ""
        for test in install_test_suite:
            testlist = testlist + ';' + test
        darttest = Dart(configFile=self.cluster_config, testFile='"[%s]"' % testlist[1:])

        testset_result = darttest.getResults()
        testsetResults = testset_result['CommandLine']
        for test in testsetResults:
            if not test[2]:
                return False
        return True

    def runSchedule(self):

        uninstall_test_suite = self.testCase('Uninstall.tst')
        healthcheck_test_suite = self.testCase('HealthCheck.tst')

        try:
            for name, testset in self.test_suites.iteritems():
                cluster_state = "UP"
                self.testsuite_results[name] = []
                for testcase in testset:
                    if type(testcase) is dict:
                        testname = testcase['NAME']
                        if 'clusterState' in testcase:
                            cluster_state = testcase['clusterState']
                    else:
                        line = testcase.split()
                        testname = line[0]
                        testparam_str = " ".join(line[1:])
                        testparams = ast.literal_eval(testparam_str)
                        if 'clusterState' in testparams:
                            cluster_state = testparams['clusterState']


                    if cluster_state == "CLEAN":
                        # Uninstall the cluster before proceeding
                        darttest = Dart(configFile=self.cluster_config, testFile='"[%s]"' % uninstall_test_suite[0])
                        testset_result = darttest.getResults()
                        testsetResults = testset_result['CommandLine']
                        for test in testsetResults:
                            if not test[2]:
                                logger.error(
                                    "The pre-test for %s didn't complete successfully, cannot proceed" % cluster_state)
                                return False
                            else:
                                logger.info('Pre-test for %s PASSED' % cluster_state)
                    elif cluster_state == "UP":
                        # Check is cluster is up before proceeding
                        darttest = Dart(configFile=self.cluster_config, testFile='"[%s]"' % healthcheck_test_suite[0])
                        testset_result = darttest.getResults()
                        testsetResults = testset_result['CommandLine']
                        for test in testsetResults:
                            if not test[2]:
                                logger.error(
                                "The pre-test for %s didn't complete successfully, cannot proceed" % cluster_state)
                                return False
                            else:
                                logger.info('Pre-test for %s PASSED' % cluster_state)
                    elif cluster_state == "NOCHECK":
                        logger.info('Not checking the state of the cluster. Tests running as is')

                    # Run the testCase
                    darttest = Dart(configFile=self.cluster_config, testFile='"[%s]"' % testcase, uploadTL=True)
                    test_result = darttest.getResults()
                    testResults = test_result['CommandLine']

                    testsetResults = self.testsuite_results[name]
                    testsetResults.append(testResults)
                    self.testsuite_results[name] = testsetResults

                    for test in testResults:
                        if cluster_state == "UP" and not test[2]:
                            # check if cluster is active
                            darttest = Dart(configFile=self.cluster_config, testFile='"[%s]"' % healthcheck_test_suite[0])
                            testset_result = darttest.getResults()
                            testsetResults = testset_result['CommandLine']
                            for test in testsetResults:
                                if not test[2]:
                                    logger.error("Testcase  %s Failed and cluster is down." \
                                                 "Exiting the test_run. Please investigate the cluster" % testcase)
                                    return False
                        else:
                            logger.info('Test %s PASSED' % testname)



        except Exception as e:
            logger.error(e)
            logger.error('The test raised an Unexpected Exception!')
            raise
        finally:
            return True


    def testCase(self, testrunfile):
        """
        @note: This function can only be used for testset files with a single testCase
        """
        testset_file = os.path.join(self.lib_path, 'testset', testrunfile)
        try:
            with open(testset_file, 'r') as tst_in:
                test_suites = json.load(tst_in)
        except ValueError as e:
            logger.error('The Json File may have syntax issues! Check the config file!')
            logger.error(e)
            logger.error('Exiting Program!')
            sys.exit(2)
        for testset in test_suites:
            return test_suites[testset]

    def createNewClusterConfig(self, cluster_cfg):
        cfg_file = os.path.join(self.lib_path, 'config', cluster_cfg)
        jsonFile = open(cfg_file, "r")
        data = json.load(jsonFile)
        jsonFile.close()

        testlinkInfo= {}
        testlinkInfo["testProject"] = self.project
        testlinkInfo["testPlan"] = self.testplan
        testlinkInfo["buildName"] = self.build
        testlinkInfo["tester"] = self.testlink_user
        testlinkInfo["platformType"] = self.platform

        data.update({'testlinkInfo' : testlinkInfo })

        self.cluster_config = '%s_%s' % ('testlink', cluster_cfg)
        new_cfg_file = os.path.join(self.lib_path, 'config', self.cluster_config)


        jsonFile = open(new_cfg_file, "w+")
        jsonFile.write(json.dumps(data))
        jsonFile.close()


    def createNewTestrunFile(self):
        m_test_suites = OrderedDict({})
        ignored_list =[]
        for name, testset in self.test_suites.iteritems():
            new_tests = []
            for tests in testset:
                if '{' in tests:
                    if type(tests) is dict:
                        testcase = tests['testCase']
                        test_suite_id= self.getTestSuiteId(testcase)
                        tests['testSuiteId'] = '%s' % test_suite_id #Update the value from testlink
                        new_tests.append(tests)
                    else:
                        line = tests.split()
                        testname = line[0]
                        testparam_str = " ".join(line[1:])
                        testparams = ast.literal_eval(testparam_str)
                        testcase = testparams['testCase']
                        test_suite_id= self.getTestSuiteId(testcase)
                        testparams['testSuiteId'] = '%s' % test_suite_id #Update the value from testlink
                        new_line = testname  + " " + str(testparams)
                        new_tests.append(new_line)
                    m_test_suites[name] = new_tests
                else:
                    logger.info("Ignoring the tests, Cannot run without test params")
                    ignored_list.append(tests)
        new_file = os.path.join(self.lib_path, 'testset', 'new_' + test_run_config)
        with open(new_file, 'w') as fp_in:
            json.dump(m_test_suites, fp_in)
        logger.info("Ignored tests due to lack of testparams : %s" % ignored_list)

        return os.path.split(new_file)[1]

    def getTestSuiteId(self, testcase):
        """
        @input: testCase name
        @return: test_suite Id
        """
        leaf_test_suite_sql = "with recursive testcasetree as (select id, name , parent_id from nodes_hierarchy where name='" + self.project + "'" \
                            "union " \
                            "select nh.id, nh.name, nh.parent_id from testcasetree ts, nodes_hierarchy as nh where nh.parent_id = ts.id )" \
                            "select parent_id from testcasetree where name like '%" + testcase + "%';"
        result = self.tlinkdb.queryDb(leaf_test_suite_sql)
        test_suite_id= result[0][0]
        return test_suite_id

    def generateJunitXml(self):
        """
        @sumary: generate an junit_xml output for using with jenkins
        """
        try:
            from junit_xml import TestSuite, TestCase
        except ImportError:
            logger.error("Unable to import junit_xml.")
            return
        ts = []
        for testset in self.test_suites:
            if testset in self.testsuite_results:
                testsetResults = self.testsuite_results[testset]
                for test in testsetResults:
                    test=test[0]
                    test_cases = []
                    if test[2]:
                        testStatus = 'PASSED'
                    else:
                        testStatus = 'FAILED'
                    timeTaken = test[1]
                    testLogFile = test[5]
                    testName = test[0]
                    tc = TestCase(testName, testName, timeTaken, testStatus, testLogFile)
                    if testStatus == 'FAILED':
                        tc.add_failure_info('Test Failed')
                    test_cases.append(tc)
                    ts.append(TestSuite(testset, test_cases))
        print(TestSuite.to_xml_string(ts))

        xml_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "log", "%s_junit.xml" % self.job_name )
        with open(xml_file, 'w') as f:
            TestSuite.to_file(f, ts, prettyprint=False)

if __name__ == "__main__":
    def printUsage():
        usage = '''
        TestRunner.py -c testlink_config_file -t testrun_file
        TestRunner.py -c testlink_config_file -t testrun_file -j jenkins_job_name
        '''
        logger.info(usage)

    try:
        argv = sys.argv[1:]
        opts, args = getopt.getopt(argv, "hc:t:j:")

    except getopt.GetoptError:
        print "Wrong Options Passed!"
        printUsage()
        sys.exit(2)

    testlink_config = None
    test_run_config = None
    job_name = 'testlink_nightly'
    for opt, arg in opts:
        if (opt == '-h'):
            printUsage()
            sys.exit(1)
        if (opt == '-c'):
            testlink_config = arg
        if (opt == '-t'):
            test_run_config = arg
        if (opt == '-j'): # jenkins job name
            job_name = arg
    schd = TestRunner(testlink_config, test_run_config, job_name)
    schd.main()
