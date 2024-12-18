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
# DESCRIPTION: DartDBConnect Class to establish database connection using Restful API
#              And provides database operation

import urllib2
import urllib
import requests
import json
import traceback
import sys

import paramiko

from Dlog import dlog

class DartDBConnect:

    def __init__(self, hostname, dbname, postgressClient=True):
        self.hostname = hostname
        self.dbname = dbname
        #self.host = 'eat01.asterdata.com'  if the host is hardcoded, we can't change to development site
        self.host = self.hostname.split(":")[0]
        self.dbuser = 'dart'
        self.dbPassword = 'aster4data'
        self.dbPort = '5432'
        self.postgressClient = postgressClient
        if self.postgressClient:
            try:
                import psycopg2
            except ImportError:
                dlog.info('The python module psycopg2 is not installed! Install this module using \'pip install psycopg2\' command')
                self.postgressClient = False
        if self.postgressClient:    
            self.conn = psycopg2.connect(database=self.dbname, user=self.dbuser, password=self.dbPassword, host=self.host, port=self.dbPort)


    def __parseResult(self, page, columns): 
        columnList = columns.split(",")

        result = []
        for p in page:
            r = []
            for column in columnList:
                column = column.lower()
                r.append(p[column.strip()])

            result.append(tuple(r))

        return result


    def __composeData(self, data):
        column = []
        for d in data:
            column.append({"name": d, "value": data[d]})

        return column


    def selectSequence(self, table):
        """
            table (string): table name
        """
        url = "http://%s/api/select_sequence?dbname=%s&table=%s" %(self.hostname, self.dbname, table)
        req = urllib2.Request(url)
        req.get_method = lambda: 'GET'
        code = None
        try:
            response = urllib2.urlopen(req)
            page = response.read()
            res = json.loads(page)

            sequence = res["sequence"]

            return sequence
        except urllib2.HTTPError, e:
            return ""


    def selectDate(self):
        url = "http://%s/api/select_date?dbname=%s" % (self.hostname, self.dbname)
        req = urllib2.Request(url)
        req.get_method = lambda: 'GET'
        code = None
        try:
            response = urllib2.urlopen(req)
            page = response.read()
            res = json.loads(page)

            date = res["date"]

            return date
        except urllib2.HTTPError, e:
            return ""


    def selectRowsUsingPG(self, table, columns, condition):
        """
            table (string): table name
            columns [list]: (column1, column2)
                ex:
                    ('status', 'id')
            condition (string): where clause
                ex:  'id = 178923'    
        """
        try:
            selectColString = ''
            rows = []
            for item  in columns:    
                if not (isinstance(item, unicode) or isinstance(item, str)):
                    column = str(item)
                else:
                    column = item
                selectColString = selectColString + column + ","
                    
            sql = "SELECT %s from %s WHERE %s;" %(selectColString[:-1], table, condition)
            dlog.info('Running the sql:')
            dlog.info(sql)
            cursor = self.conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            dlog.info('Select Return Value ========')
            dlog.info(rows)
            return rows
        except Exception as e:
            dlog.info(e)
            dlog.info("Select statement failed!")
            return rows

            
        

    def selectRows(self, table, columns, condition):
        """
            table (string): table name
            columns (string): what columns you want to select 
            condition (string): condition of record what you want to select
        """

        if self.postgressClient:
            try:
                if columns is None or len(columns) == 0:
                    columns = "*"

                if condition is not None and len(condition) != 0:
                    sql = "SELECT %s FROM %s WHERE %s;" % (columns, table, condition)
                elif len(table) == 0:
                    sql = "SELECT %s;" % columns
                else:
                    sql = "SELECT %s FROM %s;" % (columns, table)

                cursor = self.conn.cursor()
                cursor.execute(sql)

                colName = []

                for d in cursor.description:
                    colName.append(d[0])

                rows = cursor.fetchall()
                results = []
                for row in rows:
                    res = {}
                    for i in range(len(row)):
                        res[colName[i]] = row[i]

                    results.append(res)

                return results
            except Exception as e:
                dlog.info('Insert Failed!')
                return []
        else:
            conditionArg = urllib.urlencode({"condition": condition})
            columnsArg = urllib.urlencode({"columns": columns})

            url = "http://%s/api/select_rows?dbname=%s&table=%s&%s&%s" %(self.hostname, self.dbname, table, conditionArg, columnsArg)
            req = urllib2.Request(url)
            req.get_method = lambda: 'GET'
            code = None
            try:
                response = urllib2.urlopen(req)
                page = response.read()
                res = json.loads(page)

                result = self.__parseResult(res["results"], columns)

                return result
            except urllib2.HTTPError, e:
                return []


    def insertRow(self, table, data):
        """
            table (string): table name
            data (dictionary): {"column_name": column_value}
                  ex:
                      {'creator': 'alen.cheng@teradata.com', 
                       'test_category': 'service test', 
                       'owner': 'alen.cheng@teradata.com', 
                       'test_feature': 'feature', 
                       'priority': 1, 
                       'cluster_type': 'ubuntu', 
                       'tester': 'alen.cheng@teradata.com', 
                       'cluster_name': 'eat01', 
                       'os_version': 'ubuntu', 
                       'branch': 'release', 
                       'job_name': 'test db module', 
                       'revision': 'revision', 
                       'status': 'waiting', 
                       'queen_nodes': '1.1.1.1', 
                       'execution_time': 10, 
                       'start_time': '2016-10-17 13:00:00', 
                       'build_name': 'fake build', 
                       'build_info': '1234', 
                       'kernel_version': '2.6.17', 
                       'test_component': 'web service', 
                       'cluster_info': 'Dart database', 
                       'testcase': 'test database', 
                       'platform_type': 'ubuntu', 
                       'testcase_loc': '/home/beehive/', 
                       'end_time': '2016-10-17 13:10:00', 
                       'loader_nodes': '2.2.2.2'}
        """

        postData = {}
        postData["dbname"] = self.dbname
        postData["table"] = table
        postData["column"] = self.__composeData(data)
        
        if self.postgressClient:
            try:
                columns = ""
                values = ""
                for key in data:
                    columns = columns + key + ","
                    if isinstance(data[key], unicode) or isinstance(data[key], str):
                        values = values + "'" + data[key] + "',"
                    else:
                        values = values + str(data[key]) + ","

                sql = "INSERT INTO %s (%s) VALUES (%s) RETURNING id;" %(table, columns[:-1], values[:-1])
                cursor = self.conn.cursor()
                cursor.execute(sql)
                self.conn.commit()
                rowid = cursor.fetchone()[0]
            except Exception as e:
                dlog.info('Insert Failed!')
                return (0, False)
            
            return (rowid, True)
        else: 
            req = urllib2.Request("http://%s/api/insert_row" %self.hostname, json.dumps(postData))
            req.get_method = lambda: 'POST'
            code = None
            try:
                response = urllib2.urlopen(req)
                code = response.getcode()
                page = response.read()
                res = json.loads(page)
            except urllib2.HTTPError, e:
                code = e.code

            if code == 200:
                return (res["id"], True)
            else:
                return (0, False)


    def deleteRow(self, table, condition):
        """
            table (string): table name
            condition (string): condition of record what you want to delete
        """

        condition = urllib.urlencode({"condition": condition})
        req = urllib2.Request("http://%s/api/delete_row?dbname=%s&table=%s&%s" %(self.hostname, self.dbname, table, condition))
        req.get_method = lambda: 'DELETE'
        code = None
        msg = ""
        try:
            response = urllib2.urlopen(req)
            page = response.read()
            code = response.getcode()
            msg = json.loads(page)["msg"]
        except urllib2.HTTPError, e:
            code = e.code
            msg = "Delete record fail"

        if code == 200:
            return (msg, True)
        else:
            return (msg, False)


    def updateRow(self, table, data, condition):
        """
            table (string): table name
            data (dictionary): {"column_name": column_value}
                ex:
                    {"status": "pass"}
            condition (string): condition of record what you want to update    
        """

        if self.postgressClient:
            try:
                updatingColString = ""
                conditionString = ""

                for key in data:
                    if isinstance(data[key], unicode) or isinstance(data[key], str):
                        updatingColString = updatingColString + key + "='" + data[key] + "',"
                    else:
                        updatingColString = updatingColString + key + "=" + str(data[key]) + ","

                sql = "UPDATE %s SET %s WHERE %s;" %(table, updatingColString[:-1], condition)
                cursor = self.conn.cursor()
                cursor.execute(sql)
                self.conn.commit()
                
            except Exception as e:
                print(e)
                msg = "Update record fail"
                return (msg, False)
            msg = ""
            return (msg, True)
                
        else:
            postData = {}
            postData["dbname"] = self.dbname
            postData["table"] = table
            postData["updating_column"] = self.__composeData(data)
            postData["condition"] = condition
            req = urllib2.Request("http://%s/api/update_row" %self.hostname, json.dumps(postData))
            req.get_method = lambda: 'POST'
            code = None
            msg = ""
            try:
                response = urllib2.urlopen(req)
                page = response.read()
                code = response.getcode()
            except urllib2.HTTPError, e:
                code = e.code
                msg = "Update record fail"

            if code == 200:
                return (msg, True)
            else:
                return (msg, False)


    def uploadLogFile(self, logFile, logFileShortName):
        hname = self.hostname.split(":")[0]

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(hostname=hname, username="dart", password="aster4data", allow_agent=False, look_for_keys=False)
            sftp = client.open_sftp()

            sftp.put(logFile, "/root/DartLogs/" + logFileShortName)

            sftp.close()
            client.close()

            return ("", True)

        except Exception as e:
            dlog.error(e)
            dlog.error(str(sys.exc_info()))
            dlog.error(traceback.format_exc()) 
            dlog.error("Uploading log fail!")
            return ("Uploading log fail!", False)

        '''
        code = None
        msg = ""
        fp = None
        try:
            fp = open(logFile, "rb")
            fileData = {'file': fp, 'filename': logFileShortName}
            response = requests.put("http://%s/api/upload_log" % self.hostname, files=fileData)
            code = response.status_code
            msg = json.loads(response.text)["msg"]
        except:
            msg = "Upload lo fail"
        finally:
            if fp is not None:
                fp.close()

        if code == 200:
            return (msg, True)
        else:
            return (msg, False)
        '''



if __name__ == "__main__":
    d = DartDBConnect("153.64.28.228:8083", "dartdb", postgressClient=True)

    data = {}
    data["testcase"] = "test database"
    data["testcase_loc"] = "/home/beehive/"
    data["creator"] = "alen.cheng@teradata.com"
    data["owner"] = "alen.cheng@teradata.com"
    data["test_category"] = "service test"
    data["test_component"] = "web service"
    data["test_feature"] = "feature"
    data["tester"] = "alen.cheng@teradata.com"
    data["start_time"] = "2016-10-17 13:00:00"
    data["end_time"] = "2016-10-17 13:10:00"
    data["execution_time"] = 10
    data["status"] = "waiting"
    data["cluster_name"] = "eat01"
    data["cluster_info"] = "Dart database"
    data["cluster_type"] = "ubuntu"
    data["queen_nodes"] = "1.1.1.1"
    data["loader_nodes"] = "2.2.2.2"
    data["kernel_version"] = "2.6.17"
    data["os_version"] = "ubuntu"
    data["build_name"] = "fake build"
    data["build_info"] = "1234"
    data["platform_type"] = "ubuntu"
    data["job_name"] = "test db module"
    data["priority"] = 1
    data["branch"] = "release"
    data["revision"] = "revision"
    data["worker_nodes"] = "3.3.3.3"
    data["number_of_workers"] = 2
    data["db_type"] = "hadoop"
    data["db_version"] = "2.1"
    #print d.insertRow("darttestdev", data)
    #print d.deleteRow("darttest", "testcase=\'test database\' and creator=\'alen.cheng@teradata.com\' and status=\'waiting\'")
    #print d.deleteRow("darttest", "  ")
    #print d.updateRow("darttestdev1", {"status": "pass"}, "id =\'79949\'")

    #print d.selectRows("darttest", "testcase, testcase_loc, status", "testcase=\'test database\' and creator=\'alen.cheng@teradata.com\'")
    data2 = {}
    data2["darttest_id"] = 5
    data2["build_name"] = "fake build"
    data2["testProject"] = "test"	 
    data2["testPlan"] = "fake plan" 
    data2["tcVersion"] = "1234"
    data2["testSuiteId"] = "22"
    data2["testcase"] = "fake case"
    #print d.insertRow("darttestlinkinfo", data2)
    #print d.selectRows("darttestlinkinfo", "build_name, testProject, testPlan", "")
    #print d.selectDate()
    branchName = "docker"
    testProject = "GGR1" 
    release = "GGR1"
    testName = "MergeConcurrentTest3"
    sql = "run_id=(select run_id from dartruninfo where branch='%s' " %branchName
    sql = sql + "and release_name='%s' and " %testProject
    sql = sql + "release='%s' order by start_time desc limit 1) " %release
    sql = sql + "and testcase='%s' order by start_time limit 1;" %testName
    print d.selectRows("darttest", "jira_number", sql)





