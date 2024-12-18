import psycopg2
import sys
import traceback

class database_handler:

    def __init__(self, hostname="sdl06847.labs.teradata.com", dbname="sims_database"):
        self.hostname = hostname
        self.dbname = dbname
        self.dbuser = 'sims'
        self.dbPassword = 'aster4data'
        self.dbPort = '5432'
        self.conn = psycopg2.connect(database=self.dbname, user=self.dbuser, password=self.dbPassword, host=self.hostname, port=self.dbPort)


    def get_vm_name_ip(self, number, dhcp):
        try:
            sql = ""
            if dhcp:
                sql = "SELECT vm_name, vm_ip FROM vm_info where vm_ip = '' ORDER BY vm_name ASC LIMIT %s" %number
            else:
                sql = "SELECT vm_name, vm_ip FROM vm_info ORDER BY vm_name ASC LIMIT %s" %number
            cursor = self.conn.cursor()
            cursor.execute(sql)

            colName = []    
            for d in cursor.description:
                colName.append(d[0])

            rows = cursor.fetchall()
            if len(rows) != number:
                return []

            results = []
            for row in rows:
                res = {}
                for i in range(len(row)):
                    res[colName[i]] = row[i]

                results.append(res)

            return results
        except Exception as e:
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Get VM name and IP Failed!'
            return []


    def delete_unavailable_vm_name_ip(self, vms):
        try:
            for vm in vms:
                sql = "DELETE FROM vm_info WHERE vm_name='%s'" %vm["vm_name"]
                cursor = self.conn.cursor()
                cursor.execute(sql)
                self.conn.commit()
        except Exception as e:
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Delete VM name and IP Failed!'
            return False

        return True


    def insert_vm_name_ip(self, vm_name, vm_ip):
        try:
            sql = "INSERT INTO vm_info (vm_name, vm_ip) VALUES ('%s', '%s');" %(vm_name, vm_ip)
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Insert Node Information Failed!'
            return False

        return True


    def insert_node(self, cluster_id, node_info):
        try:
            sql = "INSERT INTO node_info (cluster_id, node_type, node_ip, hostname, node_status, taken, node_location, node_cluster_type)  \
                   VALUES ('%s', '%s', '%s', '%s', 'offline', 'yes', '', 'VM-Aster');" %(cluster_id, node_info["node_type"], node_info["node_ip"], node_info["hostname"])  
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Insert Node Information Failed!'
            return False

        return True


    def insert_cluster(self, cluster_info):
        try:
            sql = "INSERT INTO cluster_info (cluster_name, no_of_nodes, cluster_status, cluster_deployment, project, maintenance_flag)"
            sql = sql + " VALUES ('%s', '%s', 'Offline', '%s', '', 'No') RETURNING cluster_id" %(cluster_info["cluster_name"], cluster_info["no_of_nodes"], cluster_info["cluster_type"])
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
            rowid = cursor.fetchone()[0]
        except Exception as e:
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Insert Cluster Information Failed!'
            return (0, False)
            
        return (rowid, True)


    def select_cluster(self, cluster_name):
        try:
            sql = "SELECT * FROM cluster_info where cluster_name='%s'" %cluster_name
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
            print sys.exc_info()
            print traceback.format_exc(sys.exc_info()[2])
            print 'Select cluster fail'
            return []


if __name__ == "__main__":
    h = database_handler()
    #vms = h.get_vm_name_ip(2)
    #print vms
    #h.delete_unavailable_vm_name_ip(vms)
    #print h.select_cluster("dart-ad-sls12-17")
    vms = h.get_vm_name_ip(6, False)
    print "vms = ", vms
    h.delete_unavailable_vm_name_ip(vms)    
