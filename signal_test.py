import time
import board
import busio
import smbus
import adafruit_pca9685
i2c = busio.I2C(board.SCL, board.SDA)

# This sets INVRT on the 9685 to drive the LEDs between the PWM
# output and 5v instead of 0v.
# This is bit 4 (16).
# Bit 2 is set by default ("totem pole mode") so 2^4 + 2^2 must be set (=20)
bus = smbus.SMBus(1)
#val = bus.read_i2c_block_data(66, 1, 1)
bus.write_i2c_block_data(68, 1, [20])

#print(val)


pca = adafruit_pca9685.PCA9685(i2c, address=68)
pca.frequency = 200

# Turn off both channels
pca.channels[4].duty_cycle = 0x0000
pca.channels[5].duty_cycle = 0x0000
pca.channels[6].duty_cycle = 0x0000
time.sleep(3)

# Alternate between green / red on channels 0/1
# 0xffff is full brightness, 0x0000 is off
while True:
    print("0")
    pca.channels[4].duty_cycle = 0x04ff
    pca.channels[5].duty_cycle = 0x0000
    pca.channels[6].duty_cycle = 0x0000
    time.sleep(1)
    print("1")
    pca.channels[4].duty_cycle = 0x0000
    pca.channels[5].duty_cycle = 0x04ff
    pca.channels[6].duty_cycle = 0x0000
    time.sleep(1)
    print("2")
    pca.channels[4].duty_cycle = 0x0000
    pca.channels[5].duty_cycle = 0x0000
    pca.channels[6].duty_cycle = 0x04ff
    time.sleep(1)
