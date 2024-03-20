from Trains import database
from Trains import tpic695
from gpiozero import LED
from time import sleep, time

def main():
    db = database.db_connect("trains.db")
    database.create_state_table(db)

    # section relays
    channel_srout = LED(25)
    channel_srclk = LED(8)
    channel_rclk = LED(7)

    update_interval_s = 0.25
    #update_interval_s = 2
    
    current_state = 0
    
    while True:
        
        #iteration_start_time = time()
        next_iteration_time = time() + update_interval_s
        
        # Retrieve current state as single value
        new_state = database.get_state(db, "sections")
        if new_state != current_state:
            print("New state:",new_state,"-",bin(new_state))
            current_state = new_state
            tpic695.output_section_value(channel_srout, channel_srclk, channel_rclk, current_state)

        #print("Elapsed: ",time() - iteration_start_time)
        iteration_remaining_time = next_iteration_time - time()
        #print("Remaining: ", iteration_remaining_time)
        if iteration_remaining_time > 0:
            sleep(iteration_remaining_time)

    
    
    

if __name__ == '__main__':

    main()
