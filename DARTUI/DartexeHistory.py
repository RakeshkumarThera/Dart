import DatabaseConnection
class DartexeHistory:

    def __init__(self):
        self.cols = ["userid","runid","starttime","command"]
        self.start = 0
        self.amount = 10
        self.searchValue = ""
        self.col = 0
        self.draw = 0
        self.dir = "asc"

    def getAllDataCount(self): 
        query = "select count(*) "
        globeSearch = " (upper(userid) like '%" + self.searchValue + "%'" \
                    " or upper(runid) like '%" + self.searchValue + "%'" \
                    " or upper(command) like '%" + self.searchValue + "%'" \
                    " or upper(starttime) like '%" + self.searchValue + "%')"
         
        count_query = query + "from history where" + globeSearch
        count = DatabaseConnection.conn_count(count_query)
        return count
        
    def getData(self):
        globeSearch = "where  (upper(userid) like '%" + self.searchValue + "%'" \
                    " or upper(runid) like '%" + self.searchValue + "%'" \
                    " or upper(command) like '%" + self.searchValue + "%'" \
                    " or upper(starttime) like '%" + self.searchValue + "%')"

        orderByCol = self.cols[self.col]
        order = self.dir
        command = " ORDER BY " + orderByCol + " "  + order + " LIMIT " + str(self.amount) + " OFFSET " + str(self.start)
        data_query = "select userid, runid, starttime, command from history " + globeSearch + command
        data = DatabaseConnection.conn_history(data_query)
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
        
        self.draw = request.args['draw']
        self.searchValue = request.args['search[value]'].upper()

    def main(self, request):
        self.parseParameter(request)
        data = self.getData()
        count = self.getAllDataCount()

        array = {}
        array['data'] = data
        array['recordsTotal'] =  count
        array['recordsFiltered'] = count
        array['draw'] = self.draw
        return array

