from Trains import database
from Trains import sections
from Trains import servo
from gpiozero import LED
from time import sleep, time

import busio
import smbus
import adafruit_pca9685
import board

# station route definitions

# Main line to platform 1
route_p1 = 1
# Main line to platform 2
route_p2 = 2
# Main line -> platform 2 -> crossover -> platform 1
route_p1xfer = 3
# Main line -> platform 1 -> headshunt
route_p1_hshunt = 4
# Main line to Goods 1 (rear of P2)
route_goods_1 = 5
# Main line to Goods 2
route_goods_2 = 6
# Main line to Goods 2 via loop
route_goods_2_loop = 7


# Turnout servo addresses
station_servos = 64
mainline_servos = 65
mainline_servos_2 = 67

turnout_controller = dict()
turnout_channel = dict()

# station turnouts on the station PWM board
turnout_xo_p1 = 8
turnout_xo_p2 = 9
turnout_g2 = 10
turnout_g1_g2 = 11
turnout_headshunt = 12
turnout_p2_goods = 13
turnout_3w_l = 14
turnout_3w_r = 15

# These are unique IDs, not addresses
turnout_slip_outer_station_end = 0
turnout_slip_outer_inner_end = 1
turnout_inner_to_slip = 2
turnout_crossover_inner = 3
turnout_crossover_outer = 4
turnout_canal = 5

# assign turnouts to channels
turnout_channel[turnout_slip_outer_station_end] = 0
turnout_channel[turnout_slip_outer_inner_end] = 1
turnout_channel[turnout_inner_to_slip] = 2
turnout_channel[turnout_crossover_inner] = 15
turnout_channel[turnout_crossover_outer] = 15
turnout_channel[turnout_canal] = 14


# assign turnouts to controller boards
turnout_controller[turnout_slip_outer_station_end] = mainline_servos
turnout_controller[turnout_slip_outer_inner_end] = mainline_servos
turnout_controller[turnout_inner_to_slip] = mainline_servos
turnout_controller[turnout_crossover_inner] = mainline_servos
turnout_controller[turnout_crossover_outer] = mainline_servos_2
turnout_controller[turnout_canal] = mainline_servos_2


# turnout states
s = 1
x = 2

station_turnout_states = dict()
mainline_turnout_states = dict()

# signal addresses
# Address of signal PWM controller for primary board 
mainline_signals_1 = 66
# Address of signal PWM controller for secondary board
mainline_signals_2 = 68

# Maps the controller objects for the board addresses
mainline_signals = dict()

sig_station_to_slip_g = 0
sig_station_to_slip_y = 1
sig_station_to_slip_r = 2

sig_inner_past_slip_g = 3
sig_inner_past_slip_r = 5

sig_outer_before_crossover_g = 0
sig_outer_before_crossover_r = 1

sig_inner_before_canal_g = 5
sig_inner_before_canal_y = 4
sig_inner_before_canal_r = 6
# On/off brightness values; 0x0000 is off, 0xffff is fully on
sig_off = 0x0000
sig_on  = 0x4500

def main():
    db = database.db_connect("trains.db")
    database.create_state_table(db)

    update_interval_s = 0.25

    current_station_route = -1
    current_section_state = -1
    current_canal_siding_state = -1

    # This writes to the i2c interface directly to set INVRT on the
    # 9685 device of the signal controllers to drive the LEDs between the PWM output and 5v instead of 0v.
    # This is bit 4 (16).
    # Bit 2 is set by default ("totem pole mode") so 2^4 + 2^2 must be set (=20)
    bus = smbus.SMBus(1)
    #val = bus.read_i2c_block_data(66, 1, 1)
    bus.write_i2c_block_data(mainline_signals_1, 1, [20])
    bus.write_i2c_block_data(mainline_signals_2, 1, [20])

    # PCA9685 controller used to control LEDs
    i2c = busio.I2C(board.SCL, board.SDA)
    mainline_signals[mainline_signals_1] = adafruit_pca9685.PCA9685(i2c, address=mainline_signals_1)
    mainline_signals[mainline_signals_1].frequency = 200

    mainline_signals[mainline_signals_2] = adafruit_pca9685.PCA9685(i2c, address=mainline_signals_2)
    mainline_signals[mainline_signals_2].frequency = 200
        
    while True:
        
        next_iteration_time = time() + update_interval_s
        
        # Retrieve current station state as single value
        new_station_route = database.get_state(db, "station_route")
                
        if new_station_route != current_station_route:
            current_station_route = new_station_route
            print("New station route selected: ", new_station_route)

            try:
                # only set turnout state when the route changes
                set_station_turnouts(db, new_station_route)
            except Exception as e:
                print("Error setting station turnouts:",e)
       
        # Retrieve current mainline section state as single value
        new_section_state = database.get_state(db, "sections")
        
        # Retrieve current canal siding state
        new_canal_siding_state = database.get_state(db, "canal_siding")

        if new_section_state != current_section_state:
            print("New section state:",new_section_state,"-",bin(new_section_state))
            current_section_state = new_section_state
       
            try:
                # only set turnout state when the route changes
                set_mainline_turnouts(db, new_section_state)
                set_mainline_signals(new_section_state, new_canal_siding_state)
            except Exception as e:
                print("Error setting mainline turnouts:",e)

        if new_canal_siding_state != current_canal_siding_state:
            print("New canal siding state:",new_canal_siding_state)
            current_canal_siding_state = new_canal_siding_state
            
            try:
            
                if new_canal_siding_state == 1:
                    servo.apply_setpoint_x(db, turnout_controller[turnout_canal], turnout_channel[turnout_canal])
                else:
                    servo.apply_setpoint_s(db, turnout_controller[turnout_canal], turnout_channel[turnout_canal])

                set_mainline_signals(new_section_state, new_canal_siding_state)

            except Exception as e:
                print("Error setting canal siding state:",e)

        #print("Elapsed: ",time() - iteration_start_time)
        iteration_remaining_time = next_iteration_time - time()
        #print("Remaining: ", iteration_remaining_time)
        if iteration_remaining_time > 0:
            sleep(iteration_remaining_time)


def set_station_turnouts(db, route_to_set):
    
    # list of turnouts that must be set for the route. They will only be changed
    # if not already set
    new_turnout_states = dict()
    # P1
    if route_to_set == 1:
        # 3W; must set L before R for right route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = x
        new_turnout_states[turnout_headshunt] = x
        # P1/P2 crossover straight
        new_turnout_states[turnout_xo_p2] = s
        new_turnout_states[turnout_xo_p1] = s
        
    # P2; also the default route
    elif route_to_set == 2 or route_to_set == 0:
        # 3W order not important for straight route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = s
        new_turnout_states[turnout_p2_goods] = s
        # P1/P2 crossover straight
        new_turnout_states[turnout_xo_p2] = s
        new_turnout_states[turnout_xo_p1] = s
    
    # P2/P1 CX
    elif route_to_set == 3:
        
        # 3W order not important for straight route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = s
        new_turnout_states[turnout_p2_goods] = s
        # P1/P2 crossover curved
        new_turnout_states[turnout_xo_p2] = x
        new_turnout_states[turnout_xo_p1] = x
        
    # P1 headshunt
    elif route_to_set == 4:

        # 3W; must set L before R for right route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = x
        new_turnout_states[turnout_headshunt] = s
        # P1/P2 crossover straight
        new_turnout_states[turnout_xo_p2] = s
        new_turnout_states[turnout_xo_p1] = s

    # Goods 1
    elif route_to_set == 5:

        # 3W order not important for straight route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = s
        new_turnout_states[turnout_p2_goods] = x
        new_turnout_states[turnout_g1_g2] = x
        
    # Goods 2    
    elif route_to_set == 6:
        
        # 3W order not important for straight route
        new_turnout_states[turnout_3w_l] = s
        new_turnout_states[turnout_3w_r] = s
        new_turnout_states[turnout_p2_goods] = x
        new_turnout_states[turnout_g1_g2] = s
        new_turnout_states[turnout_g2] = x
        
    # Goods 2 via loop
    elif route_to_set == 7:

        # 3W; must set R before L for left route
        new_turnout_states[turnout_3w_r] = s
        new_turnout_states[turnout_3w_l] = x
        new_turnout_states[turnout_g1_g2] = s
        new_turnout_states[turnout_g2] = s

    # for each turnout to set, check its current state (if known)
    # and only set if required
    for turnout in new_turnout_states:
        if new_turnout_states[turnout] != station_turnout_states.get(turnout,0):
            if new_turnout_states[turnout] == s:
                servo.apply_setpoint_s(db, station_servos, turnout)
            else:
                servo.apply_setpoint_x(db, station_servos, turnout)
            station_turnout_states[turnout] = new_turnout_states[turnout]
             
             
def set_mainline_turnouts(db, section_state):

    # list of turnouts that must be set for the route. They will only be changed
    # if not already set
    new_turnout_states = dict()

    # slip; both tiebars are set together
    # curved if: outer and station are active and on same controller
    if (sections.is_section_active(section_state, sections.outer_section) and
        sections.get_section_controller(section_state, sections.outer_section) == sections.get_section_controller(section_state, sections.station_section)):        
        new_turnout_states[turnout_slip_outer_station_end] = x
        new_turnout_states[turnout_slip_outer_inner_end] = x
        
    # straight if: outer is active and outer and station are not on same controller, or if inner is active and inner and station are on same controller
    if ((sections.is_section_active(section_state, sections.outer_section) and
        sections.get_section_controller(section_state, sections.outer_section) != sections.get_section_controller(section_state, sections.station_section)) or
        (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) == sections.get_section_controller(section_state, sections.station_section))):
        new_turnout_states[turnout_slip_outer_station_end] = s
        new_turnout_states[turnout_slip_outer_inner_end] = s


    # inner loop to slip turnout
    # straight (ie. inner to slip) if inner active and station on same controller
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) == sections.get_section_controller(section_state, sections.station_section)):
        new_turnout_states[turnout_inner_to_slip] = s

    # curved (ie. inner is continuous) if inner active and station on different controller
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) != sections.get_section_controller(section_state, sections.station_section)):
        new_turnout_states[turnout_inner_to_slip] = x
     
    # crossover / inner
    # straight if inner active and inner and crossover are on different controllers
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) != sections.get_section_controller(section_state, sections.crossover_section)):
        new_turnout_states[turnout_crossover_inner] = s

    # curved if inner active and inner and crossover are on the same controller
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) == sections.get_section_controller(section_state, sections.crossover_section)):
        new_turnout_states[turnout_crossover_inner] = x

    # crossover / outer
    # straight if outer active and outer and crossover are on different controllers
    if (sections.is_section_active(section_state, sections.outer_section) and
        sections.get_section_controller(section_state, sections.outer_section) != sections.get_section_controller(section_state, sections.crossover_section)):
        new_turnout_states[turnout_crossover_outer] = s

    # curved if outer active and outer and crossover are on the same controller
    if (sections.is_section_active(section_state, sections.outer_section) and
        sections.get_section_controller(section_state, sections.outer_section) == sections.get_section_controller(section_state, sections.crossover_section)):
        new_turnout_states[turnout_crossover_outer] = x

    # for each turnout to set, check its current state (if known)
    # and only set if required
    for turnout in new_turnout_states:
        if new_turnout_states[turnout] != mainline_turnout_states.get(turnout,0):
            if new_turnout_states[turnout] == s:
                servo.apply_setpoint_s(db, turnout_controller[turnout], turnout_channel[turnout])
            else:
                servo.apply_setpoint_x(db, turnout_controller[turnout], turnout_channel[turnout])
            mainline_turnout_states[turnout] = new_turnout_states[turnout]

def set_mainline_signals(section_state, canal_siding_state):
    
    print("Setting signals from state",section_state)
    
    # station to slip
    # green if: station and inner on and same controller and same polarity
    # yellow if: station and inner on and same controller but different polarity
    # red otherwise
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) == sections.get_section_controller(section_state, sections.station_section)):

        set_signal(mainline_signals_1, sig_station_to_slip_r, sig_off)
             
        if sections.get_section_polarity(section_state, sections.inner_section) == sections.get_section_polarity(section_state, sections.station_section):
            # Same polarity, green
            set_signal(mainline_signals_1, sig_station_to_slip_g, sig_on)
            set_signal(mainline_signals_1, sig_station_to_slip_y, sig_off)
        else:
            # Different polarity, yellow
            set_signal(mainline_signals_1, sig_station_to_slip_g, sig_off)
            set_signal(mainline_signals_1, sig_station_to_slip_y, sig_on)
            
    else:
        set_signal(mainline_signals_1, sig_station_to_slip_g, sig_off)
        set_signal(mainline_signals_1, sig_station_to_slip_y, sig_off)
        set_signal(mainline_signals_1, sig_station_to_slip_r, sig_on)
    
    # inner loop past slip
    # green if: inner on but not on same controller as station
    # red if: otherwise
    if (sections.is_section_active(section_state, sections.inner_section) and
        sections.get_section_controller(section_state, sections.inner_section) != sections.get_section_controller(section_state, sections.station_section)):
        # green
        set_signal(mainline_signals_1, sig_inner_past_slip_g, sig_on)
        set_signal(mainline_signals_1, sig_inner_past_slip_r, sig_off)
    else:
        # red
        set_signal(mainline_signals_1, sig_inner_past_slip_g, sig_off)
        set_signal(mainline_signals_1, sig_inner_past_slip_r, sig_on)
        
    # outer loop past crossover
    # green if: outer on but not on same controller as crossover
    # red if: otherwise
    if (sections.is_section_active(section_state, sections.outer_section) and 
        sections.get_section_controller(section_state, sections.outer_section) != sections.get_section_controller(section_state, sections.crossover_section)):
        # green
        set_signal(mainline_signals_2, sig_outer_before_crossover_g, sig_on)
        set_signal(mainline_signals_2, sig_outer_before_crossover_r, sig_off)
    else:
        # red
        set_signal(mainline_signals_2, sig_outer_before_crossover_g, sig_off)
        set_signal(mainline_signals_2, sig_outer_before_crossover_r, sig_on)
       
    # inner loop past canal siding
    # green if: inner on, canal siding not set, station on different controller as inner
    # yellow if: inner on, canal siding not set, station on same controller as inner
    # red if: inner not on or canal siding set
    if (sections.is_section_active(section_state, sections.inner_section) and
        canal_siding_state == 0 and
        sections.get_section_controller(section_state, sections.inner_section) != sections.get_section_controller(section_state, sections.station_section)):
        # green
        set_signal(mainline_signals_2, sig_inner_before_canal_g, sig_on)
        set_signal(mainline_signals_2, sig_inner_before_canal_y, sig_off)
        set_signal(mainline_signals_2, sig_inner_before_canal_r, sig_off)

    if (sections.is_section_active(section_state, sections.inner_section) and
        canal_siding_state == 0 and
        sections.get_section_controller(section_state, sections.inner_section) == sections.get_section_controller(section_state, sections.station_section)):
        # yellow
        set_signal(mainline_signals_2, sig_inner_before_canal_g, sig_off)
        set_signal(mainline_signals_2, sig_inner_before_canal_y, sig_on)
        set_signal(mainline_signals_2, sig_inner_before_canal_r, sig_off)
        
    if (sections.is_section_active(section_state, sections.inner_section) == False or
        canal_siding_state == 1):
        # red
        set_signal(mainline_signals_2, sig_inner_before_canal_g, sig_off)
        set_signal(mainline_signals_2, sig_inner_before_canal_y, sig_off)
        set_signal(mainline_signals_2, sig_inner_before_canal_r, sig_on)
        
        
def set_signal(controller, channel, value):
    print("Signal: ",controller,"/",channel," - ",value,sep='')
    mainline_signals[controller].channels[channel].duty_cycle = value

if __name__ == '__main__':

    main()

