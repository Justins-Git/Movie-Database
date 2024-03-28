#!/usr/bin/env python3

import psycopg2
from sshtunnel import SSHTunnelForwarder

try:
    file = open("logininfo.txt", "r")
except:
    print("Create a file named logininfo.txt in the src directory")
    exit()

username = file.readline().strip()
password = file.readline().strip()
file.close()

dbName = "p320_18"

try:
    with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=username,
                            ssh_password=password,
                            remote_bind_address=('127.0.0.1', 5432)) as server:
        server.start()
        print("SSH tunnel established")
        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }


        conn = psycopg2.connect(**params)
        curs = conn.cursor()
        print("Database connection established")

        #DB work here....

        conn.close()
except:
    print("Connection Failed...")
