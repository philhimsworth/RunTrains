
from time import sleep
from gpiozero import LED


def print_byte(value):
    print("value: ",value)
    for x in range(7,-1, -1):
        print((value & (1<<x)) >> x, end='', sep='')
    print()    

# write 8 bit value using specified channels
def write_byte(data_value, channel_srout, channel_srclk):
    
    write_data(data_value, 8, channel_srout, channel_srclk)
    
# write 16 bit value using specified channels
def write_word(data_value, channel_srout, channel_srclk):

    write_data(data_value, 16, channel_srout, channel_srclk)

# write value of specified data width using specified channels
def write_data(data_value, data_width, channel_srout, channel_srclk):

    sleep(0.1)

    serdelay = 0.01

    for x in range(data_width-1,-1, -1):
        channel_srout.value = (data_value & (1<<x)) >> x 
        sleep(serdelay)
        channel_srclk.on()
        sleep(serdelay)
        channel_srclk.off()
        sleep(serdelay)

    channel_srout.off()
    
    sleep(0.1)

# pulse r_clock to transfer value from receive buffer to outputs
def set_output(channel_rclk):
 
    serdelay = 0.01

    channel_rclk.on()
    sleep(serdelay)
    channel_rclk.off()

# write section value; this is a 16 bit value
def output_section_value(channel_srout, channel_srclk, channel_rclk, value):
        
    reset(channel_srout, channel_srclk, channel_rclk)
    
    write_word(value, channel_srout,channel_srclk)
    set_output(channel_rclk)  

# write station power value; this is an 8 bit value
def output_station_power_value(channel_srout, channel_srclk, channel_rclk, value):
    
    reset(channel_srout, channel_srclk, channel_rclk)

    write_byte(value, channel_srout,channel_srclk)
    set_output(channel_rclk)  

# set output channels to initial state
def reset(channel_srout, channel_srclk, channel_rclk):

    channel_srout.off()
    channel_srclk.off()
    channel_rclk.off()

