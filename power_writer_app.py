from Trains import database
from Trains import tpic695
from gpiozero import LED
from time import sleep, time

# route definitions

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

# Far loop inner; P2 left if P2/P1 xover set (1); as near loop if not (0)
relay_far_loop = 0
# Near loop inner; Main left if 3w right is set (1); main right if not (0)
relay_near_loop = 1
# Headshunt; main right if hshunt turnout is set (no hs access) (0); as near loop inner if hshunt turnout if not (hs access) (1)
relay_hshunt = 2
# 3 way left frog; main left if 3w left is set (1); main right if not (0)
relay_3way_left = 3

# Station isolators; relay on isolates section
relay_isolator_headshunt = 7
relay_isolator_far_loop = 6
relay_isolator_g1_g2 = 5
relay_isolator_g2_from_main = 4

def main():
    db = database.db_connect("trains.db")
    database.create_state_table(db)

    update_interval_s = 0.25

    current_station_route = 0
    current_isolator_roads_state = 0
    current_isolator_headshunt_state = 0
    current_isolator_loop_state = 0

    current_station_relay_state = 0

    # station track relays
    station_channel_srout = LED(10)
    station_channel_srclk = LED(9)
    station_channel_rclk = LED(11)

    current_section_state = 0

    # section relays
    section_channel_srout = LED(25)
    section_channel_srclk = LED(8)
    section_channel_rclk = LED(7)

    while True:
        
        next_iteration_time = time() + update_interval_s
        
        # Retrieve current station state as single value
        new_station_route = database.get_state(db, "station_route")
        # Retrieve isolator states
        new_isolator_roads_state = database.get_state(db, "station_iso_roads")
        new_isolator_headshunt_state = database.get_state(db, "station_iso_hshunt")
        new_isolator_loop_state = database.get_state(db, "station_iso_loop")
        
        relay_state_changed = False
        
        # if the station route has changed, recalculate the new power relay state
        if new_station_route != current_station_route:
            current_station_route = new_station_route
            current_station_relay_state = calculate_station_route_relay_state(new_station_route, current_station_relay_state, current_isolator_loop_state)
            print("New station route selected: ", new_station_route)
            relay_state_changed = True            

        # Station road end isolators
        if new_isolator_roads_state != current_isolator_roads_state:
            current_isolator_roads_state = new_isolator_roads_state
            current_station_relay_state = set_bit(current_station_relay_state, relay_isolator_far_loop, new_isolator_roads_state)
            current_station_relay_state = set_bit(current_station_relay_state, relay_isolator_g1_g2, new_isolator_roads_state)
            print("New station road isolator state: ", new_isolator_roads_state)
            relay_state_changed = True            
            
        # Station headshunt isolator    
        if new_isolator_headshunt_state != current_isolator_headshunt_state:
            
            current_isolator_headshunt_state = new_isolator_headshunt_state
            current_station_relay_state = set_bit(current_station_relay_state, relay_isolator_headshunt, new_isolator_headshunt_state)
            print("New station headshunt isolator state: ", new_isolator_headshunt_state)
            relay_state_changed = True            

        # Goods 2 / main feed isolator    
        if new_isolator_loop_state != current_isolator_loop_state:
            
            current_isolator_loop_state = new_isolator_loop_state
            # Only reactivate G2 if G2 or the loop is actually selected; otherwise it 
            # might get turned on even if a different route is set.
            if new_isolator_loop_state == 0 and (current_station_route != route_goods_2 and current_station_route != route_goods_2_loop):
                print("G2 isolator opened but different route set (route: ",current_station_route,")",sep='')
            else:
                current_station_relay_state = set_bit(current_station_relay_state, relay_isolator_g2_from_main, new_isolator_loop_state)
            print("New station loop isolator state: ", new_isolator_loop_state)
            relay_state_changed = True            
 
        # If anything changed, apply to outputs
        if relay_state_changed:
            print("New station relay state: ", format(current_station_relay_state, 'b'))

            # set new station state. Should it do this continuously in case it gets reset?
            tpic695.output_station_power_value(station_channel_srout,
                                               station_channel_srclk,
                                               station_channel_rclk,
                                               current_station_relay_state)


        # Retrieve current section state as single value
        new_section_state = database.get_state(db, "sections")
        if new_section_state != current_section_state:
            print("New section state:",new_section_state,"-",bin(new_section_state))
            current_section_state = new_section_state
            
            # set new section state. Should it do this continuously in case it gets reset?
            tpic695.output_section_value(section_channel_srout,
                                         section_channel_srclk,
                                         section_channel_rclk,
                                         current_section_state)


        #print("Elapsed: ",time() - iteration_start_time)
        iteration_remaining_time = next_iteration_time - time()
        #print("Remaining: ", iteration_remaining_time)
        if iteration_remaining_time > 0:
            sleep(iteration_remaining_time)

    
def calculate_station_route_relay_state(route_to_set, current_relay_state, current_isolator_loop_state):
    
    new_state = current_relay_state
    
    # P1
    if route_to_set == 1:
        # near loop power to main/left
        new_state = set_bit(new_state, relay_near_loop, 1)
        # far loop power to main/left (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # hshunt power to main/right (no hs access)
        new_state = set_bit(new_state, relay_hshunt, 0)
        # 3way L frog to main/left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # Turn off G2
        new_state = set_bit(new_state, relay_isolator_g2_from_main, 1)

# P2; also the default route
    elif route_to_set == 2 or route_to_set == 0:
        # near loop power to main/right
        new_state = set_bit(new_state, relay_near_loop, 0)
        # far loop power to main/right (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # 3way L frog to main/left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # headshunt to main/right to turn it off
        new_state = set_bit(new_state, relay_hshunt, 0)
        # Turn off G2
        new_state = set_bit(new_state, relay_isolator_g2_from_main, 1)
 
    # P2/P1 CX
    elif route_to_set == 3:
        # near loop power to main/right
        new_state = set_bit(new_state, relay_near_loop, 0)
        # far loop power to main/left ()
        new_state = set_bit(new_state, relay_far_loop, 1)
        # 3way L frog to main/left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # headshunt to main/right to turn it off
        new_state = set_bit(new_state, relay_hshunt, 0)
        # Turn off G2
        new_state = set_bit(new_state, relay_isolator_g2_from_main, 1)

    # P1 headshunt
    elif route_to_set == 4:
        # near loop power to main/left
        new_state = set_bit(new_state, relay_near_loop, 1)
        # far loop power to main/left (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # hshunt power to main/left (as near loop)
        new_state = set_bit(new_state, relay_hshunt, 1)
        # 3way L frog to main left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # Turn off G2
        new_state = set_bit(new_state, relay_isolator_g2_from_main, 1)
        
    # Goods 1
    elif route_to_set == 5:
        # near loop power to main/right
        new_state = set_bit(new_state, relay_near_loop, 0)
        # far loop power to main/right (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # 3way L frog to main/left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # headshunt to main/right to turn it off
        new_state = set_bit(new_state, relay_hshunt, 0)
        # Turn off G2
        new_state = set_bit(new_state, relay_isolator_g2_from_main, 1)

    # Goods 2
    elif route_to_set == 6:
        # near loop power to main/right
        new_state = set_bit(new_state, relay_near_loop, 0)
        # far loop power to main/right (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # 3way L frog to main/left         
        new_state = set_bit(new_state, relay_3way_left, 0)
        # headshunt to main/right to turn it off
        new_state = set_bit(new_state, relay_hshunt, 0)
        # Turn on G2 unless isolated
        if current_isolator_loop_state == 0:
            new_state = set_bit(new_state, relay_isolator_g2_from_main, 0)
        
    # Goods 2 via loop
    elif route_to_set == 7:
        # 3way L frog to main right
        new_state = set_bit(new_state, relay_3way_left, 1)
        # near loop power to main/right (to turn off as same as 3-way L frog)
        new_state = set_bit(new_state, relay_near_loop, 0)
        # far loop power to main/right (as near loop)
        new_state = set_bit(new_state, relay_far_loop, 0)
        # Turn on G2 unless isolated (although it may get turned off again by the loop / G2 isolator)
        if current_isolator_loop_state == 0:
            new_state = set_bit(new_state, relay_isolator_g2_from_main, 0)
      
    return new_state;


# set a specified bit in a value to a specified state
def set_bit(value, bit_index, bit_state):

    mask = 1 << bit_index  # value with just the specified bit set
    value &= ~mask         # set the specified bit to zero by inverting the mask
    if bit_state == 1:
        value = value | mask  # if the bit is to be set, OR the mask back in        
    return value    


if __name__ == '__main__':

    main()

