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
# DESCRIPTION: DartDBHandler Class is a handler to operate PostgreSQL
#              database for Dart

import time
import psycopg2

import DartException

class DartDBHandler:

    def __init__(self, dbHostname, dbName, dbUser, dbPassword):
        self.hostname = dbHostname
        self.dbname = dbName
        self.user = dbUser
        self.password = dbPassword

        self.conn = None
        self.__connect()


    def __checkTable(self, table):
        if table is None or len(table) == 0:
            raise DartException.DartParameterException("Parameter table is missing")


    def __checkCondition(self, condition):
        if condition is None or len(condition.strip()) == 0:
            raise DartException.DartParameterException("Condition is not allowed empty")


    def __connect(self):
        cmd = "host=%s dbname=%s user=%s password=%s" % (self.hostname, self.dbname, self.user, self.password)

        self.conn = psycopg2.connect(cmd)


    def selectDate(self):
        sql = "SELECT CURRENT_DATE;"

        cursor = self.conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        for row in rows:
            return row[0]


    def selectSequence(self, table):
        sql = "SELECT nextval('%s');" %table

        cursor = self.conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        for row in rows:
            return row[0]


    def selectByTestResultDetail(self, sql):
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


    def select(self, table, condition, columns, command):
        start = time.time()

        sql = ""
        if columns is None or len(columns) == 0:
            columns = "*"
            
        if condition is not None and len(condition) != 0:
            sql = "SELECT %s FROM %s WHERE %s;" %(columns, table, condition)
        elif command is not None and len(command) != 0:
            sql = "SELECT %s FROM %s %s;" %(columns, table, command)
        elif len(table) == 0:
            sql = "SELECT %s;" %columns
        else:
            sql = "SELECT %s FROM %s;" %(columns, table)

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


    def update(self, table, updatingColumn, condition):
        updatingColString = ""
        conditionString = ""

        for c in updatingColumn:
            if isinstance(c['value'], unicode) or isinstance(c['value'], str):
                updatingColString = updatingColString + c['name'] + "='" + c['value'] + "',"
            else:
                updatingColString = updatingColString + c['name'] + "=" + str(c['value']) + ","

        sql = "UPDATE %s SET %s WHERE %s;" %(table, updatingColString[:-1], condition)
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()


    def insert(self, table, data):
        self.__checkTable(table)

        columns = ""
        values = ""
        for d in data:
            columns = columns + d['name'] + ","
            if isinstance(d['value'], unicode) or isinstance(d['value'], str):
                values = values + "'" + d['value'] + "',"
            else:
                values = values + str(d['value']) + ","

        sql = "INSERT INTO %s (%s) VALUES (%s) RETURNING id;" %(table, columns[:-1], values[:-1])
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()
        rowid = cursor.fetchone()[0]
        return rowid


    def delete(self, table, parameter):
        self.__checkTable(table)
        condition = parameter
        self.__checkCondition(condition)

        sql = "DELETE FROM %s WHERE %s;" %(table, condition)

        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()


    def __del__(self):
        self.conn.close()
        


if __name__ == "__main__":
    h = DartDBHandler("127.0.0.1", "dartdb", "dart", "aster4data")
    data = [{'name':'test_name', 'value': 'test demo'}, {'name': 'cluster_name', 'value': 'test_cluster'}]
    #h.insert("test_task", data)
    print h.selectDate()
