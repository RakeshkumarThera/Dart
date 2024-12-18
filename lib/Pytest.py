#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: PankajVinod.Purandare@teradata.com
# Secondary Owner:

import os
import codecs
import subprocess
from lib.Dlog import dlog
from lib.TestBase import TestBase

PYTEST_EXEC_COMMAND = "pytest -s "
EXEC_BY_TEST = " -k "
EXEC_BY_MARKER = " -m "

# DEFAULT DB USERS
TD_USER = "tdqg"
TD_PASSWD = "tdqg"
ASTER_DB = "beehive"
ASTER_DB_USER = "beehive"
ASTER_DB_PASSWD = "beehive"
FS = "coprocessor"

# Indent Variables
tab = "    "
double_tab = 2 * tab

class Pytest(TestBase):

    def __init__(self, cfgJson, testParams=None):
        """
        Class init method, gets the details from config file and test file.
        :param cfgJson: A hash map with details from .cfg file.
        :param testParams: A hash map with test parameter details.
        """
        TestBase.__init__(self, cfgJson, testParams)
        self.cfgJson = cfgJson
        self.clusterDict = self.cfgJson["cluster"]
        self.tdClusterDict = self.cfgJson["tdCluster"]
        self.aster_server = self.clusterDict["queenNodes"][0]
	if '.' not in self.aster_server:
	    self.aster_server = self.aster_server + '.' + self.clusterDict['domain']
        self.aster_server_user = self.clusterDict["username"]
        self.aster_server_password = self.clusterDict["password"]
        if "deployment" in self.clusterDict:
            self.deployment = self.clusterDict["deployment"]
        else:
            self.deployment = ""
        self.td_server = self.tdClusterDict["tdMasterNode"]
        self.td_server_user = self.tdClusterDict["tdUserName"]
        self.td_server_password = self.tdClusterDict["tdPassword"]
        if 'LOCATION' in self.testParams:
            self.pytest_location = self.testParams["LOCATION"]
       


    def update_config_pytest(self):
        """
        Update the config.json file which is used for executing PyTest cases.
        :return: None
        """
        # Get the config.json file
        config_json_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                        "../testsrc/analytic_ffe/src/config.json")
        file = codecs.open(config_json_file, "w", 'utf-8')

        # Get the test related required variables from test parameters (.tst) file
        aster_db = self.testParams['ASTER_DATABASE'] if 'ASTER_DATABASE' in self.testParams else ASTER_DB
        aster_db_user = self.testParams['ASTER_DB_USER'] if 'ASTER_DB_USER' in self.testParams else ASTER_DB_USER
        aster_db_password = self.testParams['ASTER_DB_PASSWORD'] if 'ASTER_DB_PASSWORD' in self.testParams else ASTER_DB_PASSWD
        td_user = self.testParams['DATABASE'] if 'DATABASE' in self.testParams else TD_USER
        td_passwd = self.testParams['PASSWORD'] if 'PASSWORD' in self.testParams else TD_PASSWD
        if self.deployment == "docker":
            add_port_to_config = ",\n{0}\"deployment\": \"{1}\"".format(double_tab, self.deployment)
        else:
            add_port_to_config = ""  
        
        # Generate the content of config.json and write the content to the file at once.
        config_json_file_content = '{\n' + tab + '"sql": {\n'
        config_json_file_content = '{0}{1}"server": "{2}",\n' \
                                   '{1}"databasename": "{3}",\n' \
                                   '{1}"actlocation": "",\n' \
                                   '{1}"username": "{4}",\n' \
                                   '{1}"password": "{4}",\n'\
                                   '{1}"aster_server_user_id": "{6}",\n' \
                                   '{1}"aster_server_pwd": "{7}"' \
                                   '{8}\n\n'.format(config_json_file_content, double_tab, self.aster_server, aster_db,
                                                    aster_db_user, aster_db_password, self.aster_server_user,
                                                    self.aster_server_password, add_port_to_config)
        if self.privateKey:
            add_privateKey_to_config = ",\n{0}\"privateKey\": \"{1}\"".format(double_tab, self.privateKey)
            config_json_file_content += add_privateKey_to_config
        
        config_json_file_content += tab + '},\n' + tab + '"teradata": {\n'
        config_json_file_content = '{0}{1}"td_server": "{2}",\n' \
                                   '{1}"td_server_user_id": "{3}",\n' \
                                   '{1}"td_server_pwd": "{4}",\n' \
                                   '{1}"td_db_username": "{5}",\n' \
                                   '{1}"td_db_password": "{6}",\n' \
                                   '{1}"td_coprocessor": "{7}"\n\n'.format(config_json_file_content, double_tab,
                                                                           self.td_server, self.td_server_user,
                                                                           self.td_server_password, td_user, td_passwd,
                                                                           FS)
        if self.tdPrivateKey:
            add_tdPrivateKey_to_config = ",\n{0}\"tdPrivateKey\": \"{1}\"".format(double_tab, self.tdPrivateKey)
            config_json_file_content += add_tdPrivateKey_to_config
                                   
        config_json_file_content += tab + '}\n' + '}'
        file.write(config_json_file_content)

    def execute_pytest(self, exec_pytest_by, pytest_case_name, pytest_marker, pytest_pattern):
        """
        Execute the test cases using 'pytest', either by using a test case name, or marker or by pattern matching
        :param exec_pytest_by: A parameter deciding how to execute pytest
        :param pytest_case_name: Test case name
        :param pytest_marker: Pytest case marker to be used to execute pytest using marker
        :param pytest_pattern: A pattern to be used for pytest execution
        :return: TRUE or FALSE i.e. a test success
        """
        # Build the PyTest execution command
        exec_cmd = ""
        # Use the test case location to look for test cases.
        if self.pytest_location:
            exec_cmd += PYTEST_EXEC_COMMAND + self.pytest_location

        # User can either use test case name or pattern, only if EXEC_BY is not set to 'marker'
        if exec_pytest_by == "name":
            exec_cmd += EXEC_BY_TEST + pytest_case_name
        elif exec_pytest_by == "pattern":
            exec_cmd += EXEC_BY_TEST + "'" + pytest_pattern + "'"

        # Marker can be used regardless of execution type.
        if pytest_marker:
            exec_cmd += EXEC_BY_MARKER + pytest_marker

        dlog.info("Executing: " + exec_cmd)
        try:
            pytest_output = subprocess.check_output([exec_cmd], shell=True, stderr=subprocess.STDOUT)
            dlog.info(pytest_output)
            return True
        except subprocess.CalledProcessError as e:
            dlog.error("Test case: " + pytest_case_name + " failed.")
            dlog.error("Following are test failure details:\n" + e.output)
            return False

    def run(self):
        """
        Execute a test case using PyTest
        :return: Test execution success or failure (True or False)
        """
        self.update_config_pytest()
        pytest_case_name = self.testParams['NAME'] if 'NAME' in self.testParams else exit(-1)

        # Get test details
        # Check PyTest execution details requested
        if 'EXEC_BY' in self.testParams:
            if self.testParams['EXEC_BY'] in ["name", "marker", "pattern"]:
                exec_pytest_by = self.testParams['EXEC_BY']
            else:
                exit("ERROR: Wrong value provided for EXEC_BY parameter in .tst file.")
        else:
            exec_pytest_by = "name"

        # Check the 'MARKER', if user has asked to execute test cases by using marker.
        if exec_pytest_by == "marker" and 'MARKER' not in self.testParams:
            exit("ERROR: Please provide 'MARKER' in .tst file, to execute test cases by marker.")
        else:
            pytest_marker = self.testParams['MARKER']

        # Check the 'PATTERN' and its details, if user has asked to execute test cases by using a pattern match.
        if exec_pytest_by == "pattern" and 'PATTERN' not in self.testParams:
            exit("ERROR: Please provide 'PATTERN' in .tst file, to execute test case by pattern match.")
        elif exec_pytest_by == "pattern" and 'PATTERN' in self.testParams:
            pytest_pattern = self.testParams['PATTERN']
        else:
            pytest_pattern = ""

        return self.execute_pytest(exec_pytest_by, pytest_case_name, pytest_marker, pytest_pattern)
