#unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: esme.li@teradata.com
# Secondary Owner:
#
# DESCRIPTION: DartDataTransform Class is a handler to operate PostgreSQL
#              database and tranform data for compareResult table.

import time
import psycopg2
import DartException
import numpy as np
import operator

from DartDBHandler import DartDBHandler

class DartDataTransform:
    def __init__(self, runids):
        self.dartdbHostname = "127.0.0.1"
        self.dartdbName = "dartdb"
        self.dartdbUser = "dart"
        self.dartdbPassword = "aster4data"
	
	self.runids = runids.split(",")

    def main(self):
	handler = DartDBHandler(self.dartdbHostname, self.dartdbName, self.dartdbUser, self.dartdbPassword)
        
	table = "darttest"
	columns = "testcase,run_id,status,log_location"
	condition = ''
	
	for runid in self.runids:
	    condition = condition +  "run_id=" + "'" + runid + "'" + ' or '
	condition = condition[0:-3];
	command =""
	
	res = handler.select(table, condition, columns, command)
	
        row_index_dict = self.getIndex(res,'testcase')
        col_index_dict = self.getIndex(res, 'run_id')

        res =self.getStatusList(row_index_dict, col_index_dict, res)
	return res

    def getIndex(self,data, key):
        indexDict ={}

        if data is None or len(data) == 0:
            print('No data passed by')
            return indexDict

        i= 0
        for d in data:
            if d[key] not in indexDict:
                indexDictKey = d[key]
                indexDict[indexDictKey] = i
                i = i + 1

        return indexDict

    def getStatusList(self, row_index, col_index, data):
        statusArr=np.ndarray((len(row_index), len(col_index)), dtype=object)
        statusArr.fill("")

        if data is None or len(data) == 0:
            return statusArr
        for d in data:
            row_key = d['testcase']
            col_key = d['run_id']
	    if d['log_location'] == '' or d['log_location'] is None:
	        statusArr[row_index[row_key]][col_index[col_key]] = d['status']
	    else:
                statusArr[row_index[row_key]][col_index[col_key]] = "<a href='/file/log?filename=" + d['log_location'].split('/')[3]+ "' target='_blank'>" + d['status'] + "</a>"
	
	# sort row_index_dict and col_index_dict by value
	sortedRowIndexList = sorted(row_index, key = row_index.__getitem__)
	sortedColIndexList = sorted(col_index, key = col_index.__getitem__)
  	
        res = {}
        res['data'] = statusArr.tolist()
        res['col'] = sortedColIndexList
        res['row'] = sortedRowIndexList
        return res


if __name__ == '__main__':
    d = DartDataTransform(runidArr)
    d.main()






