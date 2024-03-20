"""
Routes and views for the flask application.
"""

import os
import subprocess
from datetime import datetime
from flask import render_template, request, send_from_directory, redirect, url_for

from Trains import app
from Trains import database
from Trains import sections
from Trains import station_route
from Trains import servo



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                 'manifest.json', mimetype='application/json')
                                 
                                 
@app.route('/')
@app.route('/control', methods = ['GET','POST'])
def control():
    return render_template(
        'control.html')

@app.route('/controlstable', methods = ['GET'])
def controlstable():

    db = OpenDatabase()

    return RenderControlPage(db)

@app.route('/setsection', methods = ['GET','POST'])
def setsection():

    db = OpenDatabase()

    # If this is a POST, perform requested section change
    if request.method == "POST":

        form = request.form.to_dict()
        if 'section' in form:
            section = int(form['section'])
            controller = int(form['controller'])
            sections.set_section(db, section, controller)

    database.close(db)
            
    return redirect(url_for('controlstable'))


@app.route('/setstationpolarity', methods = ['GET','POST'])
def setstationpolarity():

    db = OpenDatabase()

    # If this is a POST, perform requested polarity change
    if request.method == "POST":

        form = request.form.to_dict()
        if "polarity" in form:
            new_polarity=int(form["polarity"])

            # station direction setting
            station_direction_same_as_inner = database.get_state(db, "station_direction")
            new_polarity = (station_direction_same_as_inner == new_polarity)
     
            sections.manual_set_station_polarity(db, new_polarity)

    database.close(db)

    return redirect(url_for('controlstable'))
 
 
# "Next" auto sequence button handler
# Should only be available if (1) it can identify the current step;
# it may not if the current state does not match any in the auto sequence,
# and (2) a section required by the next step is not in use by the other
# controller.

@app.route('/next', methods = ['GET','POST'])
def next():
    
    db = OpenDatabase()

    if request.method == "POST":

        form = request.form.to_dict()
        
        if "controller" in form:
            controller = int(form['controller'])
            sections.next_auto_sequence_step(db, controller)
    
    database.close(db)

    return redirect(url_for('controlstable'))


@app.route('/reset', methods = ['GET','POST'])
def reset():
    
    db = OpenDatabase()

    # If this is a POST, perform section reset
    if request.method == "POST":
        sections.all_off(db)

    database.close(db)

    return redirect(url_for('controlstable'))


@app.route('/setstationroute', methods = ['GET','POST'])
def setstationroute():
    
    db = OpenDatabase()

    if request.method == "POST":

        form = request.form.to_dict()
        
        if "route" in form:
            route = int(form['route'])
            station_route.set_route(db, route)
    
    database.close(db)

    return redirect(url_for('controlstable'))
    

@app.route('/setisolator', methods = ['GET','POST'])
def setisolators():

    db = OpenDatabase()

    if request.method == "POST":

        form = request.form.to_dict()
        
        if "isolator" in form:
            isolator = form['isolator']
            state = form['state'] == 'true'
            station_route.set_isolator(db, isolator, state)
    
    database.close(db)

    return redirect(url_for('controlstable'))
    
    
@app.route('/setcanalsiding', methods = ['GET','POST'])
def setcanalsiding():

    db = OpenDatabase()

    if request.method == "POST":

        form = request.form.to_dict()
        
        if "state" in form:
            state = form['state'] == 'true'
            database.set_state(db, "canal_siding", state)

    database.close(db)

    return redirect(url_for('controlstable'))
    
    

@app.route('/teach', methods = ['GET','POST'])
def teach():

    db = OpenDatabase()
    
    if request.method == "POST":
        servo.add_channel(db, request.form["board"], request.form["channel"])

    return RenderTeachPage(db)

@app.route('/channel', methods = ['GET','POST'])
def channel():

    last_set_angle = 0
    board = request.args.get('board')
    channel = request.args.get('channel')

    db = OpenDatabase()

    # If this is a POST, a channel set or save setpoints operation has been requested
    if request.method == "POST":
        form = request.form.to_dict()
        print(form)
        if "save" in form:
            board = form['board']
            channel = form['channel']
            setpoint_s = form['setpoint_s']
            setpoint_x = form['setpoint_x']
            description = form['description']
            servo.save_setpoints(db, board, channel, description, setpoint_s, setpoint_x)
        elif "set" in form:
            board = form['board']
            channel = form['channel']
            angle = form['angle']
            last_set_angle = angle
            servo.set_angle(board,channel,angle)
            
    return RenderChannelPage(db, board, channel, last_set_angle)


@app.route('/system', methods = ['GET','POST'])
def system():

    db = OpenDatabase()

    return RenderSystemPage(db)
    
    
def RenderSystemPage(db):
    
    pgrep_result = subprocess.run(["pgrep", "-af", "RunTrains"], stdout=subprocess.PIPE)

    # station direction setting
    station_direction_same_as_inner = database.get_state(db, "station_direction")
    
    # section / auto states
    section_state = database.get_state(db, "sections")
    auto_step_c1 = sections.identify_auto_sequence_step(1, section_state)
    auto_step_c2 = sections.identify_auto_sequence_step(2, section_state)
    auto_next_step_ok_c1 = sections.is_next_auto_sequence_step_available(1, section_state, auto_step_c1)
    auto_next_step_ok_c2 = sections.is_next_auto_sequence_step_available(2, section_state, auto_step_c2)


    database.close(db)

    return render_template(
        'system.html',
        pgrep_results = pgrep_result.stdout.splitlines(),
        i2c_boards = GetI2CBoards(),
        station_direction_same_as_inner = station_direction_same_as_inner,
        section_state = section_state,
        auto_step_c1 = auto_step_c1,
        auto_step_c2 = auto_step_c2,
        auto_next_step_ok_c1 = '>>' if auto_next_step_ok_c1 else '',
        auto_next_step_ok_c2 = '>>' if auto_next_step_ok_c2 else '')

def GetI2CBoards():
    
    i2cdetect_results = subprocess.run(["i2cdetect", "-y", "1"], stdout=subprocess.PIPE).stdout.splitlines()
    
    i2c_boards = ""
    
    for line in i2cdetect_results:
        line2 = line.decode()
        colon_pos = line2.find(":")
        if colon_pos != -1:
            board_list = line2[colon_pos+1:].split()
            for board in board_list:
                if board != "--":
                    board_name = board
                    board_number = int(board, 16)
                    if board_number == 64:
                        board_name = "station"
                    if board_number == 65:
                        board_name = "main1"
                    if board_number == 67:
                        board_name = "main2"
                    if board_number == 66:
                        board_name = "signals1"
                    if board_number == 68:
                        board_name = "signals2"
                        
                    i2c_boards = i2c_boards + board_name + " "
    return i2c_boards


@app.route('/stationdirection', methods = ['GET','POST'])
def stationdirection():
    
    db = OpenDatabase()

    # If this is a POST, store supplied setting value
    if request.method == "POST":
        
        form = request.form.to_dict()
        print(form)
        
        if "direction_setting" in form:
            station_direction_same_as_inner = int("station_direction_same_as_inner" in form)
            database.set_state(db, "station_direction", station_direction_same_as_inner)

    return RenderSystemPage(db)
    

@app.route('/shutdown', methods = ['GET','POST'])
def shutdown():

    result = subprocess.run(["sudo", "halt"], stdout=subprocess.PIPE)

    return render_template(
        'system.html',
        status = "System shutdown"
    )

@app.route('/restart', methods = ['GET','POST'])
def restart():

    result = subprocess.run(["sudo", "reboot"], stdout=subprocess.PIPE)

    return render_template(
        'system.html',
        status = "System restarting"
    )

# Open the database and initialise it if it has never been used
def OpenDatabase():

    # Open database connection
    db = database.db_connect("trains.db")
    database.create_state_table(db)
    database.create_servo_setpoint_table(db)
    return db


# Generate combined control page, close db connection
def RenderControlPage(db):

    # Retrieve current state as single value from DB after any modifications
    section_state_value = database.get_state(db, "sections")

    # auto route current step
    auto_step_c1 = sections.identify_auto_sequence_step(1, section_state_value)
    auto_step_c2 = sections.identify_auto_sequence_step(2, section_state_value)
        
    auto_next_step_ok_c1 = sections.is_next_auto_sequence_step_available(1, section_state_value, auto_step_c1)
    auto_next_step_ok_c2 = sections.is_next_auto_sequence_step_available(2, section_state_value, auto_step_c2)
    
    print("Auto states: 1: ",auto_step_c1," next ok: ", auto_next_step_ok_c1," 2: ",auto_step_c2," next ok: ", auto_next_step_ok_c2, sep='')
    
    # Retrieve station route from db
    station_route = database.get_state(db, "station_route")

    # Retrieve station isolator states from db
    station_isolator_roads = database.get_state(db, "station_iso_roads")
    station_isolator_headshunt = database.get_state(db, "station_iso_hshunt")
    station_isolator_g2 = database.get_state(db, "station_iso_loop")

    # canal siding turnout state
    canal_siding = database.get_state(db, "canal_siding")
    
    # station direction setting
    station_direction_setting = database.get_state(db, "station_direction")

    station_polarity = sections.get_section_polarity(section_state_value, sections.station_section)
    station_polarity = (station_direction_setting == station_polarity)
    
    database.close(db)

    # Process template
    return render_template(
        'controlstable.html',
        section_states = GetSectionStates(section_state_value),
        station_polarity = station_polarity,
        auto_step_c1 = auto_step_c1,
        auto_step_c2 = auto_step_c2,
        auto_next_step_ok_c1 = auto_next_step_ok_c1,
        auto_next_step_ok_c2 = auto_next_step_ok_c2,
        station_route = station_route,
        station_isolator_roads = station_isolator_roads,
        station_isolator_headshunt = station_isolator_headshunt,
        station_isolator_g2 = station_isolator_g2,
        canal_siding = canal_siding
    )

def GetSectionStates(section_state_value):
    
    section_states = {}
    section_polarities = {}
    for section in range(1, 6):
        section_states[section] = sections.get_section_controller(section_state_value, section)
        section_polarities[section] = sections.get_section_polarity(section_state_value, section)
    print("Section states: ", section_state_value, " -> ", section_states, sep='')
    print("Section polarities: ", section_polarities, sep='')

    return section_states
    
    


def RenderTeachPage(db):

    board_list,channel_list,description_list,setpoint_s_list,setpoint_x_list = servo.get_setpoints_all_channels(db)
    
    database.close(db)
    
    # Process template
    return render_template(
        'teach.html',
        board_list = board_list,
        channel_list = channel_list,
        description_list = description_list,
        setpoint_s_list = setpoint_s_list,
        setpoint_x_list = setpoint_x_list,
        num_channels = len(board_list)
    )

def RenderChannelPage(db, board, channel, last_set_angle):
    
    description, setpoint_s, setpoint_x = servo.get_setpoints_one_channel(db, board, channel)
    
    database.close(db)

    return render_template(
        'channel.html',
        board = board,
        channel = channel,
        last_value = last_set_angle,
        current_description = description,
        current_setpoint_s = setpoint_s,
        current_setpoint_x = setpoint_x)
