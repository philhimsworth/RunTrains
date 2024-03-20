from adafruit_servokit import ServoKit
from time import sleep, time
from . import database

# set a servo to the specified angle immediately
def set_angle(board, channel, angle, turnoff = True):
    
    print("Set servo angle: Board:",board,"Channel:",channel,"To angle:",angle)
    kit = ServoKit(address = int(board), channels = 16)
    kit.servo[int(channel)].angle = int(angle)
    
    if turnoff == True:
        sleep(0.1)
        kit.servo[int(channel)].angle = None

def set_state(board, channel, state):

    print("Set state: Board:",board,"Channel:",channel,"To state:",state)
    kit = ServoKit(address = int(board), channels = 16)
    if state == True:
        kit.servo[int(channel)].angle = 100
    else:
        kit.servo[int(channel)].angle = None
    
    
# save servo setpoints to the database
def save_setpoints(db, board, channel, description, setpoint_s, setpoint_x):
    print("Save setpoints: Board:",board,"Channel:",channel,"Description:",description,"S:",setpoint_s,"X:",setpoint_x)
    
    database.set_setpoints(db,board,channel,description,setpoint_s,setpoint_x)
    
    
def add_channel(db, board, channel):
    database.add_channel(db, board, channel)
    
def get_setpoints_all_channels(db):
    return database.get_setpoints_all_channels(db)

def get_setpoints_one_channel(db, board, channel):
    return database.get_setpoints_one_channel(db, board, channel)

def apply_setpoint_s(db, board, channel):
    try:
        description, setpoint_s, setpoint_x = get_setpoints_one_channel(db, board, channel)
        print("Apply setpoint S: ",description)
        set_angle(board, channel, setpoint_s)
    except Exception as e:
        print("Error setting turnout (",board,":",channel,") setpoint S: ",e,sep='')

def apply_setpoint_x(db, board, channel):
    try:
        description, setpoint_s, setpoint_x = get_setpoints_one_channel(db, board, channel)
        print("Apply setpoint X: ",description)
        set_angle(board, channel, setpoint_x)
    except Exception as e:
        print("Error setting turnout (",board,":",channel,") setpoint X: ",e,sep='')
        
def turn_on(board, channel):
    try:
            set_state(board, channel, True)
    except Exception as e:
        print("Error turning on channel (",board,":",channel,"): ",e,sep='')
            
def turn_off(board, channel):
    try:
            set_state(board, channel, False)
    except Exception as e:
        print("Error turning off channel (",board,":",channel,"): ",e,sep='')
    
