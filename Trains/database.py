import sqlite3
from sqlite3 import Error


def db_connect(db_file):
    """ create a database connection to a SQLite database """
    db = None
    try:
        db = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return db

# run a query that does not need a result
def run_query(db, sql):
    try:
        c = db.cursor()
        c.execute(sql)
    except Exception as e:
        print(e)

# run a parameterised query that does not need a result
def run_query_with_params(db, sql, params):
    try:
        c = db.cursor()
        c.execute(sql, params)
    except Exception as e:
        print(e)

# create the state table if necessary.
# this is a table of (state_name, state_value) records.
def create_state_table(db):

    # Create table if it doesn't exist
    sql_create_state_table = """ CREATE TABLE IF NOT EXISTS states(
                                        name nvarchar(20) DEFAULT '',
                                        state integer DEFAULT 0
                                    ); """

    run_query(db, sql_create_state_table)

    # Ensure there are default data records
    initialise_state(db,"sections")
    initialise_state(db,"station_route")
    initialise_state(db,"station_iso_roads")
    initialise_state(db,"station_iso_hshunt")
    initialise_state(db,"station_iso_loop")
    initialise_state(db,"station_direction")
    initialise_state(db,"canal_siding")
    

# If necessary, initialise a single named record to zero and check it
def initialise_state(db, state_name):
    
    if get_state(db, state_name) == -1:
        print("Initialising ", state_name)
        sql_insert_state = 'INSERT INTO states (name, state) VALUES (\'' + state_name + '\',0);'
        run_query(db, sql_insert_state)
        
        # Check
        if get_state(db, state_name) == -1:
            print("Initialising state failed: ",state_name)

# return the state of a single named state
def get_state(db, state_name):

    try:
        sql_get_state = 'SELECT state FROM states WHERE name = \'' + state_name + '\';'
        db.row_factory = sqlite3.Row
        c = db.execute(sql_get_state)

        row = c.fetchone()
        if row is None:
            return -1
        else:
            return row["state"]
    except Exception as e:
        print(e)
        return -1

# set the state of a single named state
def set_state(db, state_name, new_state):
    try:
        sql_update_state = 'UPDATE states SET state = ? WHERE name = \'' + state_name + '\';'
        c = db.cursor()
        c.execute(sql_update_state, (new_state,))

    except Exception as e:
        print(e)

def close(db):
    try:
        db.commit()
        db.close()
    except Exception as e:
        print(e)

def commit(db):
    try:
        db.commit()
    except Exception as e:
        print(e)
        
# create the servo setpoint table if necessary.
# this is a table of (board, channel, description, setpoint_s, setpoint_x) records.
def create_servo_setpoint_table(db):

    # Create table if it doesn't exist
    sql_create_table = """ CREATE TABLE IF NOT EXISTS servo_setpoints(
                                        board integer,
                                        channel integer,
                                        description nvarchar(30) DEFAULT '',
                                        setpoint_s integer DEFAULT 0,
                                        setpoint_x integer DEFAULT 0,
                                        PRIMARY KEY (board, channel)
                                    ); """

    run_query(db, sql_create_table)
    
def set_setpoints(db, board, channel, description, setpoint_s, setpoint_x):
    
    print('database.set:', board, channel, description, setpoint_s, setpoint_x)
    
    sql_query = """ INSERT OR REPLACE INTO servo_setpoints (board, channel, description, setpoint_s, setpoint_x)
                    VALUES (?, ?, ?, ?, ?);"""
 
    c = db.cursor()
    params = (board, channel, description, setpoint_s, setpoint_x)
    c.execute(sql_query, params)



def get_setpoints_all_channels(db):
    
    try:
        
        list_boards = []
        list_channels = []
        list_descriptions = []
        list_setpoint_s = []
        list_setpoint_x = []
    
        sql_query = """SELECT * FROM servo_setpoints ORDER BY board,channel;"""

        cursor = db.cursor() 
        cursor.execute(sql_query)

        for row in cursor:
            list_boards.append(row["board"])
            list_channels.append(row["channel"])
            list_descriptions.append(row["description"])
            list_setpoint_s.append(row["setpoint_s"])
            list_setpoint_x.append(row["setpoint_x"])
            
        return list_boards,list_channels,list_descriptions,list_setpoint_s,list_setpoint_x
            
    except Exception as e:
        print(e)
        return -1


def get_setpoints_one_channel(db, board, channel):
    try:
        sql_get = 'SELECT description, setpoint_s, setpoint_x FROM servo_setpoints WHERE board = ? AND channel = ?;'
        params = (board, channel)
        db.row_factory = sqlite3.Row
        c = db.execute(sql_get, params)

        row = c.fetchone()
        if row is None:
            return "",0,0
        else:
            return row["description"], row["setpoint_s"], row["setpoint_x"]
        
    except Exception as e:
        print(e)
        raise
    
def add_channel(db, board, channel):
    try:
        sql_add = """INSERT INTO servo_setpoints (board, channel, description, setpoint_s, setpoint_x) VALUES (?, ?, ?, ?, ?);"""
        params = (board, channel, "New channel", 0, 0)
        c = db.cursor()
        c.execute(sql_add, params)
    except Exception as e:
        print(e)
