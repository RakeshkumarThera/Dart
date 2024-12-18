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
# DESCRIPTION: DartDashboard Class generates data which is
#              showed on Dart dashboard page


from DartDBHandler import DartDBHandler

class DartDashboard:

    def __init__(self, handler):
        self.handler = handler
        self.cols = ["run_id", "run_label", "branch", "release", "release_name", "revision", "tester", "start_time", "duration", 
                     #"num_cluster", "jira_number", "total", "running", "waiting", "pass",
                     #"fail", "abort", "skip", 
                     "build_number", "keywords", "comments"]
        self.start = 0
        self.amount = 10
        self.private = 0
        self.runId = ""
        self.project = ""
        self.branch = ""
        self.release = ""
        self.draw = 0
        self.col = 0
        self.dir = "asc"
        self.searchVaule = ""
        self.startdate = ""
        self.enddate = ""
        self.showTag = False


    def getAllDataCount(self):
        columns = "count(*)"
        condition = ""
        if self.private == 0:
            condition = condition + "run_type ='Public'"

        if self.runId != "":
            if self.private == 0:
                condition = condition + " AND "
            condition = condition + "run_id='%s'" %self.runId

        if self.branch != "":
            if self.private == 0 or self.runId != "":
                condition = condition + " AND "
            condition = condition + "branch='%s'" %self.branch
            
        if self.release != "":
            if self.private == 0 or self.runId != "" or self.branch != "":
                condition = condition + " AND "
            condition = condition + "release='%s'" %self.release
            
        if self.project != "":
            if self.private == 0 or self.runId != "" or self.branch != "" or self.release != "":
                condition = condition + " AND "
            condition = condition + "release_name='%s'" %self.project

        
        
        

        globeSearch = " (upper(run_id) like '%" + self.searchValue + "%'" \
                    " or upper(run_label) like '%" + self.searchValue + "%'" \
                    " or upper(branch) like '%" + self.searchValue + "%'" \
                    " or upper(release_name) like '%" + self.searchValue + "%'" \
                    " or upper(release) like '%" + self.searchValue + "%'" \
                    " or upper(build_number) like '%" + self.searchValue + "%'" \
                    " or upper(revision) like '%" + self.searchValue + "%'" \
                    " or upper(tester) like '%" + self.searchValue + "%'" \
                    " or upper(keywords) like '%" + self.searchValue + "%'" \
                    " or upper(comments) like '%" + self.searchValue + "%'" \
                    " or start_time::text like '%" + self.searchValue + "%'" \
                    " or duration::text like '%" + self.searchValue + "%')"

        dateCondition = ""
        if self.startdate != "":
            dateCondition = " start_time between '" + self.startdate + "'::date and '" + self.enddate + "'::date "

        if condition != "":
            if dateCondition != "":
                dateCondition = " AND " + dateCondition
            condition = condition + dateCondition
            if self.searchValue != "":
                condition = globeSearch + " AND "  + condition
            data = self.handler.select("dartruninfo", condition, columns, "")
        else:
            command = dateCondition
            if self.searchValue != "" or dateCondition != "":
                command = globeSearch
                #command = globeSearch + " AND "  + command
                data = self.handler.select("dartruninfo", command, columns, "")
            else:
                data = self.handler.select("dartruninfo", "", columns, command)

        count = data[0]['count']

        return count


    def queryDataFromDartTest(self, runId):
        column = ""
        column = column + "(select count(cluster_name) from (select distinct cluster_name from darttest where run_id='%s') as c) as num_cluster," %runId
        column = column + "(select count(status) from darttest where run_id='%s') as total," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='RUNNING') as running," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='WAITING') as waiting," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='PASS') as pass," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='SKIP') as skip," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='ABORT') as abort," %runId
        column = column + "(select count(status) from darttest where run_id='%s' and status='FAIL') as fail," %runId
        column = column + "(select count(distinct jira_number) from darttest where run_id='%s' and jira_number<>'') as jira" %runId

        data = self.handler.select("", "", column, "")
      
        return data[0]


    def queryDataFromDartRunInfo(self):
        columns = ""
        for i in range(len(self.cols)):
            columns = columns + self.cols[i] + ","
       

        columns = columns + "tag"

        condition = ""
        if self.private == 0:
            condition = condition + "run_type='Public'"

        if self.runId != "":
            if self.private == 0:
                condition = condition + " AND "
            condition = condition + "run_id='%s'" %self.runId

        if self.branch != "":
            if self.private == 0 or self.runId != "":
                condition = condition + " AND "
            condition = condition + "branch='%s'" %self.branch
            
        if self.release != "":
            if self.private == 0 or self.runId != "" or self.branch != "":
                condition = condition + " AND "
            condition = condition + "release='%s'" %self.release
            
        if self.project != "":
            if self.private == 0 or self.runId != "" or self.branch != "" or self.release != "":
                condition = condition + " AND "
            condition = condition + "release_name='%s'" %self.project
        
        globeSearch = " (upper(run_id) like '%" + self.searchValue + "%'" \
                    " or upper(run_label) like '%" + self.searchValue + "%'" \
                    " or upper(branch) like '%" + self.searchValue + "%'" \
                    " or upper(release_name) like '%" + self.searchValue + "%'" \
                    " or upper(release) like '%" + self.searchValue + "%'" \
                    " or upper(build_number) like '%" + self.searchValue + "%'" \
                    " or upper(revision) like '%" + self.searchValue + "%'" \
                    " or upper(tester) like '%" + self.searchValue + "%'" \
                    " or upper(keywords) like '%" + self.searchValue + "%'" \
                    " or upper(comments) like '%" + self.searchValue + "%'" \
                    " or start_time::text like '%" + self.searchValue + "%'" \
                    " or duration::text like '%" + self.searchValue + "%')"

        dateCondition = ""
        if self.startdate != "":
            dateCondition = " start_time between '" + self.startdate + "'::date and '" + self.enddate + "'::date "

        orderByCol = self.cols[self.col]
        order = self.dir
        if self.showTag:
            orderByCol = "tag"
            order = "asc"

        if condition != "":
            if dateCondition != "":
                dateCondition = " AND " + dateCondition
            condition = condition + dateCondition
            condition = condition + " ORDER BY " + orderByCol + " "  + order + " LIMIT " + str(self.amount) + " OFFSET " + str(self.start)
            if self.searchValue != "":
                condition = globeSearch + " AND "  + condition
            data = self.handler.select("dartruninfo", condition, columns, "")
        else:
            command = dateCondition
            command = command + " ORDER BY " + orderByCol + " "  + order + " LIMIT " + str(self.amount) + " OFFSET " + str(self.start)
            if self.searchValue != "" or dateCondition != "":
                #command = globeSearch + " AND "  + command
                command = globeSearch + command
                data = self.handler.select("dartruninfo", command, columns, "")
            else:
                data = self.handler.select("dartruninfo", "", columns, command)
        
        return data


    def convertResultToList(self, data, key):
        res = []
        for d in data:
            res.append(d[key])

        return res


    def queryAllProject(self):
        condition = ""
        if self.private == 0:
            condition = condition + "run_type ='Public'"

        columns = "DISTINCT release_name" 
        data = self.handler.select("dartruninfo", condition, columns, "")
        data = self.convertResultToList(data, "release_name")

        return data


    def queryAllBranch(self):
        condition = ""
        if self.private == 0:
            condition = condition + "run_type='Public' and branch <> '' or branch <> null"

        columns = "DISTINCT branch"
        data = self.handler.select("dartruninfo", condition, columns, "")
        data = self.convertResultToList(data, "branch")

        return data

    def queryAllRelease(self):
        condition = ""
        if self.private == 0:
            condition = condition + "run_type='Public' and release <> '' or release <> null"

        columns = "DISTINCT release"
        data = self.handler.select("dartruninfo", condition, columns, "")
        data = self.convertResultToList(data, "release")

        return data

    def queryAllRunID(self):
        condition = ""
        if self.private == 0:
            condition = condition + "run_type='Public'"

        columns = "DISTINCT run_id"
        data = self.handler.select("dartruninfo", condition, columns, "")
        data = self.convertResultToList(data, "run_id")

        return data


    def parseParameter(self, request):
        sStart = request.args['start']
        if sStart is not None:
            self.start = int(sStart)
            if self.start < 0:
                self.start = 0

        sAmount = request.args['length']
        if sAmount is not None:
            self.amount = int(sAmount)
            if self.amount < 10 or self.amount > 100:
                self.amount = 10

        sCol = request.args['order[0][column]']
        if sCol is not None:
            self.col = int(sCol)
            if self.col < 0 or self.col > 20:
                self.col = 0
            if self.col > 17:
                self.col = self.col - 9

        sDir = request.args['order[0][dir]']
        if sDir is not None:
            if sDir != "asc":
                self.dir = "desc"

        self.private = int(request.args['private'])
        self.runId = request.args['columns[0][search][value]']
        self.project = request.args['columns[4][search][value]']
        self.release = request.args['columns[3][search][value]']
        self.branch = request.args['columns[2][search][value]']
        if request.args['show_tag'] != "" and request.args['show_tag'] == "true":
            self.showTag = True

        self.draw = request.args['draw']
        self.searchValue = request.args['search[value]'].upper()


    def main(self, request):
        self.parseParameter(request)
        count = self.getAllDataCount()
        data = self.queryDataFromDartRunInfo()
        
        for d in data:
            res = self.queryDataFromDartTest(d['run_id'])
            d.update(res)

        projectData = self.queryAllProject()
        branchData = self.queryAllBranch()
        releaseData = self.queryAllRelease()
        runIdData = self.queryAllRunID()

        array = {}
        array['draw'] = self.draw
        array['recordsTotal'] =  count
        array['recordsFiltered'] = count
        array['data'] = data
        array['yadcf_data_0'] = runIdData
        array['yadcf_data_2'] = branchData
        array['yadcf_data_3'] = releaseData
        array['yadcf_data_4'] = projectData

        return array
