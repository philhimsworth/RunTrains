import platform
import subprocess
from time import sleep
from gpiozero import LED

def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
    

def main():

    quickflash = 0.1
    slowflash = 2

    ping_test_host = '192.168.1.1'

    channel_flash = LED(24)

    # Startup flashes
    for x in range(1,10):
        channel_flash.on()
        sleep(quickflash)
        channel_flash.off()
        sleep(quickflash)

    # Continuous loop forever
    while True:
    
        # Ping router to test network access / keep network alive
        if ping(ping_test_host):
    
            # Network OK; short flash
            channel_flash.on()
            sleep(quickflash)

        else:
            # Network dead; slow flash
            channel_flash.on()
            sleep(slowflash)

        # Flash off
        channel_flash.off()
        sleep(slowflash)
 

if __name__ == '__main__':
    main()
