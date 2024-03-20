import board
import digitalio
import time
import math
import keypad
import asyncio
import neopixel
import supervisor

# Control panel program

# colours
red = (0,255,0)
blue = (0,0,255)
yellow = (255,255,0)
green = (255,0,0)
off = (0,0,0)


async def flash_function():

    print("Starting flash")

    redLed = 0
    
    global track1state
    global track2state
    
    while True:
    
        # colours in GRB
    
        for led in range(5):
            if (led == redLed):
                pixels[led] = (0,255,0)
            else:
                pixels[led] = (0,0,255)
                
        pixels.show()
        
        redLed = redLed + 1
        if (redLed == 5):
            redLed = 0
    
        await asyncio.sleep(0.2)
        
        track1led.value = track1state
        #track1state = not track1state
    
        track2led.value = track2state
        #track2state = not track2state
        
        #led.value = True
        #switchled.value = True
        #time.sleep(0.5)
        #led.value = False
        #switchled.value = False
        #time.sleep(0.5)

async def buttons_test():
    
    print("Starting button test")
    
    button = digitalio.DigitalInOut(board.GP19)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP

    button2 = digitalio.DigitalInOut(board.GP20)
    button2.direction = digitalio.Direction.INPUT
    button2.pull = digitalio.Pull.UP
    
    while True:
        print("1:",button.value)
        print("2:",button2.value)
        await asyncio.sleep(0.1)
        

async def monitor_buttons_function():
    print("Starting buttons")
        
    # Controller 1 Next is GP20, C2 is GP19
    with keypad.Keys(
        [board.GP20, board.GP19], value_when_pressed=False, pull=True
    ) as keys:
        while True:
            key_event = keys.events.get()
            if key_event and key_event.pressed:
                if key_event.key_number == 0:
                    print("C1")
                if key_event.key_number == 1:
                    print("C2")
            await asyncio.sleep(0)
                 

async def flash_led_function():
    led = digitalio.DigitalInOut(board.GP25)
    led.direction = digitalio.Direction.OUTPUT
    
    while True:
        led.value = not led.value
        await asyncio.sleep(1)

                    
async def main():
    
    #flash_task = asyncio.create_task(
    #    flash_function())
    #monitor_buttons_task = asyncio.create_task(
    #    monitor_buttons_function())


    #buttons_test()
    #await monitor_buttons_function()
    await asyncio.gather(   set_indicators_from_input(),
                            monitor_buttons_function(),
                            flash_led_function())


async def set_indicators_from_input():
    
    print("Starting serial input")
    
    #TODO: totally forgot about these
    # Track 1 "next auto state" button light
    track1led = digitalio.DigitalInOut(board.GP18)
    track1led.direction = digitalio.Direction.OUTPUT
    
    # Track 2 "next auto state" button light
    track2led = digitalio.DigitalInOut(board.GP17)
    track2led.direction = digitalio.Direction.OUTPUT
    
    # State indicators
    num_pixels = 5
    
    pixels = neopixel.NeoPixel(board.GP16, num_pixels)
    pixels.brightness = 0.2
    
    led_station = 0
    led_track2_2 = 1
    led_track2_1 = 2
    led_track1_2 = 3
    led_track1_1 = 4
    
    while True:
        if (supervisor.runtime.serial_bytes_available):
            command = input();
            print("Received: ", command)
            components = command.split(",")
            print("Components: ", components)
            if (len(components) == 5):
                
                # decode message
                auto_step_1 = components[0];
                auto_next_step_ok_c1 = components[1];
                auto_step_2 = components[2];
                auto_next_step_ok_c2 = components[3];
                station_active = components[4]
              
                # state change button indicators
                track1led.value = True if auto_next_step_ok_c1 == 1 else False
                track2led.value = True if auto_next_step_ok_c2 == 1 else False
                
                # station controller is available when station section is off
                # (from the pov of c1/c2)
                if (station_active == 1):
                    pixels[led_station] = off
                else:
                    pixels[led_station] = yellow
            
                # state for controllers
                set_mode_for_controller(auto_step_1, led_track1_1, led_track1_2, pixels)
                set_mode_for_controller(auto_step_2, led_track2_1, led_track2_2, pixels)
                
                pixels.show()
    
        else:
            await asyncio.sleep(0.1)

        
# auto states
auto_unknown = -1
auto_0_off = 0
auto_1_station_outbound = 1
auto_2_station_inner = 2
auto_3_inner = 3
auto_4_inner_cx_outer = 4
auto_5_outer = 5
auto_6_outer_station = 6
auto_7_station_inbound = 7

def set_mode_for_controller(auto_step, led_1, led_2, pixels):
    
    if auto_step == auto_0_off:
        pixels[led_1] = off
        pixels[led_2] = off
    elif auto_step == auto_1_station_outbound:
        pixels[led_1] = green
        pixels[led_2] = off
    elif auto_step == auto_2_station_inner:
        pixels[led_1] = green
        pixels[led_2] = red
    elif auto_step == auto_3_inner:
        pixels[led_1] = red
        pixels[led_2] = red
    elif auto_step == auto_4_inner_cx_outer:
        pixels[led_1] = red
        pixels[led_2] = blue
    elif auto_step == auto_5_outer:
        pixels[led_1] = blue
        pixels[led_2] = blue
    elif auto_step == auto_6_outer_station:
        pixels[led_1] = blue
        pixels[led_2] = green
    elif auto_step == auto_7_station_inbound:
        pixels[led_1] = off
        pixels[led_2] = green
    else:
        pixels[led_1] = green
        pixels[led_2] = green
            
    
asyncio.run(main())
