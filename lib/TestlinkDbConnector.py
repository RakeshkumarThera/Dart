#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: divya.sivanandan@teradata.com
# Secondary Owner:
#
# Description: Testlink DB methods

import psycopg2

from logger import logger


class TestLink(object):
    """
    @summary: Includes library functions to access testlink
    """

    def __init__(self):

        self.hostname = "eat01.asterdata.com"
        self.dbname = "testlinkdb"
        self.db_user = "testlink"
        self.db_password = "aster4data"

        self.conn = self.connectDb()

    def connectDb(self):
        """
        @returns a connection object
        """
        conn_string = "host=%s dbname=%s user=%s password=%s" % (self.hostname, self.dbname, self.db_user, self.db_password)
        logger.info("Connecting to database\n	->%s" % (conn_string))

        try:
            conn = psycopg2.connect(conn_string)
        except Exception as e:
            logger.error("Exception raised when connecting to testlinkdb : %s " % e)
            raise
        return conn

    def queryDb(self, query):
        """
        @summary: Execute the query and return records as a list
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
        return records


