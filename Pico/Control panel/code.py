import board
import digitalio
import time
import asyncio

# IR sensor program

async def checksensor(input, id):
    
    # Set up input
    sensor = digitalio.DigitalInOut(input)
    sensor.direction = digitalio.Direction.INPUT
    sensor.pull = digitalio.Pull.DOWN

    # number of cycles with sensor unbroken to trigger
    OPEN_COUNT_TRIGGER = 10
    # number of cycles so far
    countOpen = 0
    # counting triggered?
    counting = False
    
    #print("Running:",input)
    
    while True:
        if sensor.value:
            if counting:
                # sensor open shortly after being blocked;
                # increment how long it has been open for
                countOpen = countOpen + 1
                if countOpen == OPEN_COUNT_TRIGGER:
                    # sensor has been open for long enough to trigger.
                    # stop counting and call trigger
                    counting = False
                    sensor_triggered(id)
        else:
            # sensor blocked; start counting (if not already)
            # and reset count
            counting = True
            countOpen = 0
            
        await asyncio.sleep(0.05)

def sensor_triggered(id):
    print("Trigger:",id)
    

async def main():
    sensor1_task = asyncio.create_task(checksensor(board.GP2, 1))
    sensor2_task = asyncio.create_task(checksensor(board.GP3, 2))
    
    await asyncio.gather(sensor1_task)


asyncio.run(main())
