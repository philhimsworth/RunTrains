from Trains import database

# Just store the route in the database; the route writer app will work out
# the state required.
def set_route(db, new_route):
    
    try:

        print("Set station route: ",new_route)
        database.set_state(db, "station_route", new_route)

    except Exception as e:
        print(e)




# Just store the isolator state in the database; the route writer app will work out
# how to set them.
def set_isolator(db, isolator, state):
    
    try:
        print("Set isolator: ", isolator, state)
        if isolator == "roads":
            database.set_state(db, "station_iso_roads", state)
        if isolator == "headshunt":
            database.set_state(db, "station_iso_hshunt", state)
        if isolator == "g2_loop":
            database.set_state(db, "station_iso_loop", state)

    except Exception as e:
        print(e)


def set_isolators(db, isolator_dict):
    
    try:
        
        print("Set isolators: ",isolator_dict)
        database.set_state(db, "station_iso_roads", int("roads" in isolator_dict))
        database.set_state(db, "station_iso_hshunt", int("headshunt" in isolator_dict))
        database.set_state(db, "station_iso_loop", int("g2_loop" in isolator_dict))
            

    except Exception as e:
        print(e)

