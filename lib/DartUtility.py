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
# DESCRIPTION: DartUtility Class provides general utility function


import time
from datetime import date

from DartDBConnect import DartDBConnect

DB_HOST = "dartdashboard.labs.teradata.com:8080"
DB_NAME = "dartdb"

class DartUtility:

    def __init__(self):
        pass


    @staticmethod
    def generateRunId():
        handler = DartDBConnect(DB_HOST, DB_NAME)

        dateStr = handler.selectDate()
        if dateStr == "":
            return ""

        dateList = dateStr.split("-")
        runIdPrefix = "%s%s%s" %(dateList[0][2:], dateList[1], dateList[2])
        runIdSuffix = handler.selectSequence("dartrunidsuffix")
        if runIdSuffix == "":
            return ""

        runId = "%s-%s" %(runIdPrefix, runIdSuffix)

        return runId


    @staticmethod
    def intToTimeFormat(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        return "%02d:%02d:%02d" %(h, m, s)


    @staticmethod
    def getDbHost():
        return DB_HOST

    @staticmethod
    def getDbName():
        return DB_NAME


if __name__ == "__main__":
    print DartUtility.generateRunId()
