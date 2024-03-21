import psycopg2
import datetime
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

#try:
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
    
    # curs.execute("SELECT * from genre;")
    # for line in curs:
    #     print(line)

    while True:
        print("Enter username: ")
        username = input("")
        print("Enter password: ")
        password = input("")

        infos = []
        success = False
        curs.execute("SELECT username, password FROM movie_user;")
        for info in curs:
            if (username, password) == info:
                success = True

        if not success:
            print("This login information does not exist, do you wish to create an account with this information? (y/n)")
            ans = input("")
            if ans != "y": break
            else: 
                print("Enter first name")
                firstname = input("")
                print("Enter last name")
                lastname = input("")
                curs.execute("INSERT INTO movie_user (username, password, creation_date, last_access_date, first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s);", (username, password, datetime.date.today(), datetime.date.today(), firstname, lastname))
                conn.commit()
                print("Account successfully created")

        curs.execute("INSERT INTO user_access_date (access_date, username) VALUES (%s, %s);", (datetime.date.today(), username))
        conn.commit()

        
                
                

            

                

        curs.close()
    conn.close()
#except:
    #print("Connection Failed...")
