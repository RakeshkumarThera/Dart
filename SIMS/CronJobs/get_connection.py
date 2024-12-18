# author: Saif ali Karedia

import psycopg2


def get_connection_object():
    hostname = 'localhost'
    username = 'sk186170'
    password = 'aster4data'
    database = 'Sims_Database'
    myConnection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
    return myConnection
