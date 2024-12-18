import psycopg2

try:
    conn = psycopg2.connect("dbname='my_db' user='postgres' host='localhost' password='test'")
except:
     print ("Unable to connect to the database")

cur = conn.cursor()

def HealthCheck():
    cur.execute("""select * from HealthCheck;""")
    HealthCheck={}
    HealthCheck_list=[]
    for row in cur.fetchall():
       HealthCheck_list.append(row[0])
       HealthCheck['HealthCheck'] = HealthCheck_list
    full_dict = {}
    full_dict.update(HealthCheck)
    full_dict.update(BranchName())
    full_dict.update(RevisionNumber())
    return full_dict


def RevisionNumber():
    cur.execute("""select revisionnumber from revision;""")
    revision={}
    revision_number=[]
    for row in cur.fetchall():
       revision_number.append(row[0])
       revision['revision'] = revision_number
    return revision

def conn_UserId():
    cur.execute("""select * from UserId;""")
    UserId={}
    count = 0
    for row in cur.fetchall():
       UserId[count] = row[0]
       count += 1
    return UserId


def post_history(UserId, run_id, timestamp, Command):
    query = "insert into history(userid,runid,starttime,command) values('%s','%s','%s','%s');"
    cur.execute(query %(UserId, run_id, timestamp, Command))
    print(query %(UserId, run_id, timestamp, Command))
    conn.commit()

def post_gittime(starttime):
    query1 = "delete from gittime;"
    query = "insert into gittime(starttime) values('%s');"
    cur.execute(query1)
    cur.execute(query %(starttime))
    conn.commit()

def get_gittime():
    cur.execute("""select * from gittime;""")
    time = {}
    for row in cur.fetchall():
       time['time'] = row[0]
    return time

def BranchName():
    cur.execute("""select branchname from branch;""")
    BranchName={}
    Branch_Name=[]
    for row in cur.fetchall():
       Branch_Name.append(row[0])
       BranchName['BranchName'] = Branch_Name
    return BranchName

def conn_history(sql): 
    cur.execute(sql)
    history_table = []
    count = 0
    data = cur.fetchall()
    for row in data:
       d = {}
       d['user'] = row[0]
       d['run_id'] = row[1]
       d['date'] = row[2]
       d['command'] = row[3]
       history_table.append(d)
    return history_table

def conn_count(sql):
    cur.execute(sql)
    data_count  = cur.fetchall()
    return data_count

def delete(run_ids):
    #Example query for multiple deletes : DELETE FROM history WHERE runid = '180713-42' or runid= '180712-32';
    query = "DELETE FROM history WHERE (%s);"
    cur.execute(query %(run_ids))
    conn.commit() 
    
