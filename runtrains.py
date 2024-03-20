"""
This script runs the Trains application using a development server.
"""

from os import environ
from Trains import app
from Trains import database

def InitDatabase():

    db = database.db_connect("trains.db")
    database.create_state_table(db)
    # No need to reset the section state; whatever the previous state was
    # will be set by the periodic writer
    #database.update_section_state(db, 0)
    database.close(db)


if __name__ == '__main__':

    InitDatabase()

    HOST = environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('SERVER_PORT', '80'))
    except ValueError:
        PORT = 80
    app.run(HOST, PORT)

