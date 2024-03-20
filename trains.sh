#!/bin/sh
### BEGIN INIT INFO
# Provides:          trains.sh
# Required-Start:    $remote_fs $syslog $network
# Required-Stop:     $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start trains daemon at boot time
# Description:       Enable trains service provided by daemon.
### END INIT INFO
sudo python3 /home/pi/Documents/RunTrains/runtrains.py & 
sudo python3 /home/pi/Documents/RunTrains/route_writer_app.py & 