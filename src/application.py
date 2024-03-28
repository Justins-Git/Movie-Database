import psycopg2
import datetime
import hashlib
import secrets
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
    curs.execute("SELECT c.collection_id, c.name, COUNT(m.movie_id), SUM(x.length) FROM collection c, collection_contains_movie m, movie x WHERE c.collection_id=m.collection_id AND m.movie_id=x.movie_id GROUP BY c.collection_id ORDER BY c.name ASC")
    print(f"| CollectionID\tName\t\t\t\t Number of Movies\tWatchtime")
    for collection in curs:
        hours = int(collection[3]/60)
        minutes = collection[3]%60
        print(f"| {collection[0]:<4d}\t\t{collection[1]:30s}\t{collection[2]:<3d}\t\t\t{hours}:{minutes:02d}")
    while True:    
        answer = input("Create Collection (C) | View Collection (V CollectionID) | View Personal Collections (M) | Quit (Q): ")
        if answer[0:1] == "Q":
            break
        
        elif answer[0:1] == "V":
            collectionID = int(answer[2:6])
            curs.execute(f"SELECT c.name, COUNT(m.movie_id), SUM(x.length) FROM collection c, collection_contains_movie m, movie x "
                          + f"WHERE m.collection_id={collectionID} AND c.collection_id={collectionID} AND m.movie_id=x.movie_id GROUP BY c.name")
            values = curs.fetchone()
            hours = int(values[2]/60)
            minutes = values[2]%60
            print(f"| {values[0]}\t{values[1]}\t{hours}:{minutes:02d}\n|")
            curs.execute(f"SELECT m.name, m.length FROM collection c, movie m, collection_contains_movie x WHERE " +
                         f"x.collection_id = {collectionID} AND c.collection_id={collectionID} AND x.movie_id = m.movie_id")
            for values in curs:
                hours = int(values[1]/60)
                minutes = values[1]%60
                print(f"| {values[0]:40s}{hours}:{minutes:02d}")
            while True:
                answer = input("Watch Collection (W) | Quit (Q): ")
                if answer[0:1] == "Q":
                    break
                elif answer[0:1] == "W":
                    curs.execute(f"SELECT m.movie_id FROM movie m, collection_contains_movie x WHERE " +
                                 f"x.collection_id = {collectionID} AND x.movie_id = m.movie_id")
                    movieID = curs.fetchall()
                    for id in movieID:
                        command = "INSERT INTO user_watched VALUES ('" +username+"',"+str(id[0])+",'"+str(datetime.date.today())+"');"
                        curs.execute(command)
                        #curs.execute("INSERT INTO user_watched ([user], movie, time) VALUES (%s, %s, %s);", (username, movieID, datetime.date.today(),))
                        conn.commit()
                    
        elif answer[0:1] == "C":
            collectionName = input("\nInsert the name for the collection: ")
            curs.execute("INSERT INTO collection (name) VALUES (%s)", (collectionName,))
            conn.commit()
            curs.execute("SELECT MAX(collection_id) FROM collection")
            collID = int(curs.fetchone()[0])
            curs.execute(f"INSERT INTO user_collection (username, collection_id) VALUES {(username, collID)}")
            conn.commit()
            movieName = input("A collection must contain a movie, input a movie name: ")
            curs.execute(f"SELECT movie_id FROM movie where name = '{movieName}'")
            movID = int(curs.fetchone()[0])
            curs.execute(f"INSERT INTO collection_contains_movie (collection_id, movie_id) VALUES {(collID, movID)}")
            conn.commit()
            print("Collection successfully created and movie successfully added")
            
        elif answer[0:1] == "M":
            curs.execute(f"SELECT c.collection_id, c.name, COUNT(m.movie_id), SUM(x.length) FROM collection c, collection_contains_movie m, movie x, "
                          + f"user_collection u WHERE u.collection_id = c.collection_id AND m.collection_id = c.collection_id AND" + 
                          f" m.movie_id = x.movie_id AND u.username = '{username}' GROUP BY c.name, c.collection_id")
            print(f"| CollectionID\tName\t\t\t\t Number of Movies\tWatchtime")
            for collection in curs:
                hours = int(collection[3]/60)
                minutes = collection[3]%60
                print(f"| {collection[0]:<4d}\t\t{collection[1]:30s}\t {collection[2]:<3d}\t\t\t{hours}:{minutes:02d}")
            while True:
                option = input("Delete Collection (D collectionID) | Modify Collection (M collectionID) | Quit (Q): ")
                if option[0:1] == "D":
                    curs.execute(f"DELETE FROM collection WHERE collection_id = {option[2:6]}")
                    curs.execute(f"DELETE FROM collection_contains_movie WHERE collection_id = {option[2:6]}")
                    curs.execute(f"DELETE FROM user_collection WHERE collection_id = {option[2:6]}")
                    conn.commit()
                    print("Collection successfully deleted!\n")
                    
                elif option[0:1] == "M":
                    while True:
                        collectionID = int(option[2:6])
                        curs.execute(f"SELECT c.name, COUNT(m.movie_id), SUM(x.length) FROM collection c, collection_contains_movie m, movie x, user_collection u "
                                    + f"WHERE m.collection_id={collectionID} AND c.collection_id={collectionID} AND u.collection_id ={collectionID} AND u.username = '{username}' AND m.movie_id=x.movie_id GROUP BY c.name")
                        values = curs.fetchone()
                        hours = int(values[2]/60)
                        minutes = values[2]%60
                        print(f"| {values[0]}\t{values[1]}\t\t  {hours}:{minutes:02d}\n|")
                        curs.execute(f"SELECT m.name, m.length FROM collection c, movie m, collection_contains_movie x, user_collection u WHERE " +
                                    f"x.collection_id = {collectionID} AND c.collection_id={collectionID} AND u.collection_id ={collectionID} AND u.username = '{username}' AND x.movie_id = m.movie_id ORDERBY m.name ASC")
                        for values in curs:
                            hours = int(values[1]/60)
                            minutes = values[1]%60
                            print(f"| {values[0]:40s}{hours}:{minutes:02d}")
                        
                        answer = input("Watch Collection (W) | Add Movie (A movieName) | Remove Movie (R movieName) | Change Collection Name (C newName) | Quit (Q): ")
                        if answer[0:1] == "Q":
                            break
                        elif answer[0:1] == "W":
                            curs.execute(f"SELECT m.movie_id FROM movie m, collection_contains_movie x WHERE " +
                                        f"x.collection_id = {collectionID} AND x.movie_id = m.movie_id")
                            movieID = curs.fetchone()[0]
                            while movieID != None:
                                curs.execute(f"INSERT INTO user_watched (user, movie, time) VALUES {(username, movieID, datetime.date.today())}")
                                conn.commit()
                                movieID = curs.fetchone()[0]
                        elif answer[0:1] == "A":
                            curs.execute(f"SELECT movie_id FROM movie where name = '{answer[2:42]}'")
                            movID = int(curs.fetchone()[0])
                            curs.execute(f"INSERT INTO collection_contains_movie (collection_id, movie_id) VALUES {(collectionID, movID)}")
                            conn.commit()
                            print("Movie successfully added to collection!\n")
                        elif answer[0:1] == "R":
                            curs.execute(f"SELECT movie_id FROM movie where name = '{answer[2:42]}'")
                            movID = int(curs.fetchone()[0])
                            curs.execute(f"DELETE FROM collection_contains_movie WHERE movie_id = {movID}")
                            conn.commit()
                            print("Movie successfully deleted from collection!\n")
                        elif answer[0:1] == "C":
                            curs.execute(f"UPDATE collection SET name = '{answer[2:42]}' WHERE collection_id = {collectionID}")
                            conn.commit()
                            print("Collection name successfully changed")
                    
                elif option[0:1] == "Q":
                    break;

def movies(conn, curs, username):
    # TODO: Search for movies by name, release date, cast members, studio, or
    # genre. The resulting list of movies must show the movie’s name, the cast members, the
    # director, the length and the ratings (MPAA and user). The list must be sorted alpha-
    # betically (ascending) by movie’s name and release date. Users can sort the resulting
    # list by: movie name, studio, genre, and released year (ascending and descending).
    # Rate movies, Watch movies
    while True:
        answer = input("Watch Movie (W movieName) | Rate Movie (R name rating(1-5)) | Search for Movie (S) | Quit (Q)")
        if answer[0:1] == "Q":
            break
        elif answer[0:1] == "W":
            movieName = answer[2:]
            curs.execute(f"SELECT m.name, m.length, m.mpaa_rating, m.movie_id FROM movie m"
                          + f"WHERE m.name={movieName}")
            values = curs.fetchone()
            print(f"| {values[0]}\t{values[1]}\t{values[2]}\n|")
            movieID = {values[3]}
            curs.execute(f"SELECT m.release_date FROM released_on m"
                         + f"WHERE m.movie_id={movieID}")
            values = curs.fetchone()
            print(f"| {values[0]}\n|")
            curs.execute(f"INSERT INTO user_watched (user, movie, time) VALUES {(username, movieID, datetime.date.today())}")
            conn.commit()
            print("Film watched.")
        elif answer[0:1] == "R":
            movieName, rating = [x for x in answer[2:].split() if x != ""]
            rating = int(rating)
            assert 1 <= rating and 5 >= rating
            curs.execute("SELECT movie_id from movie where name = %s", movieName)
            movieID = curs.fetchall()
            if len(movieID) == 0:
                print("Movie not found")
            elif len(movieID) > 1:
                print("!!! Multiple movies found")
            else:
                movieID = movieID[0]
                curs.execute("INSERT INTO user_rating (username, movie_id, star_rating) VALUES (%s, %s, %s)", (username, movieID, rating))
                conn.commit()
                print("Rated")
        elif answer[0:1] == "S":
            answer = input("Search by Title (T) | Release Date (D) | Cast Members (C) | Studio (S) | Genre (G): ")

            ##answer[0:1] == "T":
            ##    check = "title"
            ##elif answer[0:1] == "D":
            ##    check = ""
            ##elif an wer[0:1] == "C":
            ##    pass
            ##elif answer[0:1] == "S":
            ##    pass
            ##elif answer[0:1] == "G":
            ##    pass           
            ##    pass           
        else:
            print("Invalid Input.")
            break

    return

def friends(conn, curs, username):
    curs.execute("SELECT username_friend FROM user_friend WHERE username = %s;", (username,))
    has_friend = False
    for friend in curs:
        has_friend = True
        print(f"| {friend[0]}")

    if not has_friend: print("> No Friends")

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

    curs.execute("SELECT salt_value FROM movie_user WHERE username=%s;", (username,))

    salt_value = curs.fetchone()

    if salt_value != None:
        # Encrypt (password + salt_value)
        password = hashlib.sha256(password.join(salt_value[0]).encode('utf-8')).hexdigest()
        curs.execute("SELECT 1 FROM movie_user WHERE username=%s AND password=%s", (username, password,))

    if curs.fetchone() == None or salt_value == None:
        ans = input("This login information does not exist, do you wish to create an account with this information? (y/n): ")
        if ans != "y": return None
        else: 
            firstname = input("Enter first name: ")
            lastname = input("Enter last name: ")
            email = input("Enter email: ")
            salt_value = secrets.token_hex(8)
            password = hashlib.sha256(password.join(salt_value).encode('utf-8')).hexdigest()
            curs.execute("INSERT INTO movie_user (username, password, creation_date, last_access_date, first_name, last_name, salt_value) VALUES (%s, %s, %s, %s, %s, %s, %s);", (username, password, datetime.date.today(), datetime.date.today(), firstname, lastname, salt_value))
            curs.execute("INSERT INTO user_email (username, email) VALUES (%s, %s);", (username, email,))
            conn.commit()
            print("Account successfully created")
    else:
        print("> Login Successful")
    
    curs.execute("SELECT 1 FROM user_access_date where access_date=%s AND username=%s", (datetime.date.today(), username,))

    # Only if this user has not logged on today insert new row
    if curs.fetchone() == None:
        curs.execute("INSERT INTO user_access_date (access_date, username) VALUES (%s, %s);", (datetime.date.today(), username))
        conn.commit()

    return username


if __name__ == "__main__":
    main()
