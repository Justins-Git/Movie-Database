import psycopg2
import datetime
from sshtunnel import SSHTunnelForwarder

def main():

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

            username = login(conn, curs)
            # If the user entered valid login information or created an account
            if username != None:  
                while True:
                    print("---------------------------------------------------------------------")
                    result = input("View Collections (C) | View Movies (M) | View Friends (F) | Quit (Q): ")

                    if result == "C": collections(conn, curs, username)
                    elif result == "M": movies(conn, curs, username)
                    elif result == "F": friends(conn, curs, username)
                    elif result == "Q": break

                            
                        
            conn.close()
    except Exception as error:
            print("Connection Failed...", error)


def collections(conn, curs, username):
    return

def movies(conn, curs, username):
    return

def friends(conn, curs, username):
    curs.execute("SELECT username_friend FROM user_friend WHERE username = %s;", (username,))
    for friend in curs:
        print(f"| {friend[0]}")

    while True:
        result = input("Remove Friend (R friend-username) | Add Friend (A friend-email) | Quit (Q): ")

        if result[0:1] == "R":
            friend = result[2:]

            curs.execute("SELECT FROM user_friend WHERE username=%s AND username_friend=%s", (username, friend,))
            friend_exists = curs.fetchone() != None

            if friend_exists:
                curs.execute("DELETE FROM user_friend WHERE username=%s AND username_friend=%s", (username, friend,))
                conn.commit()
                print(f"> {friend} removed from friends list successfully")
            else:
                print(f"> User {friend} could not be found")

        elif result[0:1] == "A":
            friend_email = result[2:]
            curs.execute("SELECT username FROM user_email where email=%s;", (friend_email,))
            friend_username = curs.fetchone()
            
            if friend_username != None:
                friend_username = friend_username[0]
                curs.execute("INSERT INTO user_friend (username, username_friend) VALUES (%s, %s);", (username, friend_username,))
                conn.commit()

                print(f"> User {friend_username} with email {friend_email} has been added")
            else:
                print(f"> User with email {friend_email} could not be found")

        elif result[0:1] == "Q": break 

def login(conn, curs):
    username = input("Enter username: ")
    password = input("Enter password: ")

    infos = []
    success = False
    curs.execute("SELECT username, password FROM movie_user;")
    for info in curs:
        if (username, password) == info:
            success = True

    if not success:
        ans = input("This login information does not exist, do you wish to create an account with this information? (y/n)")
        if ans != "y": return None
        else: 
            firstname = input("Enter first name")
            lastname = input("Enter last name")
            curs.execute("INSERT INTO movie_user (username, password, creation_date, last_access_date, first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s);", (username, password, datetime.date.today(), datetime.date.today(), firstname, lastname))
            conn.commit()
            print("Account successfully created")
    else:
        print("> Login Successful")
    
    curs.execute("SELECT * FROM user_access_date where access_date=%s AND username=%s", (datetime.date.today(), username,))

    if curs.fetchone() == None:
        curs.execute("INSERT INTO user_access_date (access_date, username) VALUES (%s, %s);", (datetime.date.today(), username))
        conn.commit()

    return username


if __name__ == "__main__":
    main()
