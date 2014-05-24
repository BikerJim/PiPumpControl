#!/usr/bin/python3
## Script to run the pump every 12 hours, but first check the status of the pump
## in weather_data.db, if its 1 run the pump for specified amount of time.

import sqlite3
import time

from quick2wire.gpio import pins, Out

relay = pins.pin(1, direction=Out)
pump_led = pins.pin(5, direction=Out)

db_file = "/home/pi/python/waterer/weather_data.db"

## Log Writer
def writelog(text):
    """
    Append a line to the logfile if there are any unusual activities
    used by the other methods when necessary
    """
    logfile = open("/home/pi/python/waterer/water.log","a")
    logfile.write(text+"\n")
    logfile.close()

## Check the latest entry in the db, if the pump_status = 1 or 0
def pump_status():
    db_conn = sqlite3.connect(db_file)
    c = db_conn.cursor()
    c.execute("select max(ID), PUMP_STATUS from weather")
    pump_stat = c.fetchone()[1]
    c.close
    db_conn.close()
    return pump_stat

## Check the latest entry in the db, and return the length in seconds
def get_length():
    db_con = sqlite3.connect(db_file)
    c = db_con.cursor()
    c.execute("select LENGTH from settings where ID = 1")
    length = c.fetchone()[0]
    c.close()
    db_con.close()
    return length

## If its 1, run the pump, and flash the red led otherwise exit
def run_pump(length):
    if pump_status() == 1:
        count = 0
        pump_led.open()
        relay.open()
        relay.value = 1
        while count < length:
            pump_led.value = 1
            time.sleep(.5)
            pump_led.value = 0
            time.sleep(.5)
            count += 1
        relay.value = 0
        relay.close()
        pump_led.value = 0
        pump_led.close()
        writelog(str(time.ctime(int(time.time())))+": Ran pump for "+str(length)+" seconds")
    else:
        writelog(str(time.ctime(int(time.time())))+": Pump disabled")

run_pump(get_length())
