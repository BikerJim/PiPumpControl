#!/usr/bin/env python3
import sqlite3
import os
import time 
import datetime
import numpy

# Setup Quick2Wire
import quick2wire.i2c as i2c
from quick2wire.gpio import pins, Out
from quick2wire.parts.pcf8591 import *

# Stuff for collecting online data
from urllib.request import Request 
from urllib.request import urlopen
from urllib.error import URLError
from urllib.error import HTTPError

# Custom module for drawing the graphs
from create_graphs import CreateGraphs

# setup the quick2wire  pins
power = pins.pin(3, direction=Out)

db_file = "/home/pi/python/waterer/weather_data.db"

def status_leds(state):
    disabled = pins.pin(0, direction=Out)
    enabled = pins.pin(7, direction=Out)
    dispath = str(disabled._pin_path())+"value"
    enpath = str(enabled._pin_path())+"value"
    for pinname, pinpath in {disabled:dispath,enabled:enpath}.items():
        if not os.path.isfile(pinpath):
            pinname.open()
        
    if state == 0:
        dis = 1
    else:
        dis = 0
    with open(enpath, "+w") as f:
        f.write(str(state)+"\n")
    with open(dispath, "+w") as f:
        f.write(str(dis)+"\n")

def get_settings():
    """
    Grab the settings from the settings table
    """
    db_conn = sqlite3.connect(db_file)
    c = db_conn.cursor()
    c.execute("select max(ID),MIN_RAIN,MIN_RAV,MIN_PREV,PERIOD,LENGTH from settings")
    settings = c.fetchone()
#    writelog("Settings got: "+str(settings))
    return settings

## Log Writer
def writelog(text):
    """
    Append a line to the logfile if there are any unusual activities
    used by the other methods when necessary
    """
    logfile = open("/home/pi/python/waterer/water.log","a")
    logfile.write(text+"\n")
    logfile.close()

## Check the sensors
def check_sensors(count):
#    writelog("check_sensors (inside) : "+str(count))
    st_no = 0
    total = 0
    with power:
        power.value = 1
        while st_no < count:
            with i2c.I2CMaster() as master:
                pcf = PCF8591(master, FOUR_SINGLE_ENDED)
                pin0 = pcf.read_single_ended(0) # Soil
                pin1 = pcf.read_single_ended(1) # Temp
                pin2 = pcf.read_single_ended(2) # Light
                soil = int(pin0)
                temp = int(((pin1*(4750.0/255.0))/100))
                light = int(pin2)
            total = total + soil
            st_no = st_no + 1
            time.sleep(1)
    average_soil = int(total/count)
#    writelog(str(average_soil)+str(temp)+str(light))
    return average_soil, temp, light

## check for weather
def check_forecast(min_rain):
    rainfall = [0,]
    durl = "http://gps.buienradar.nl/getrr.php?lat=52.36377&lon=4.85603"
    user_agent = "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"
    headers = {"User-Agent" : user_agent}
    request = Request(durl, None, headers)
    try:
        brdata = urlopen(request)
        response = brdata.read().decode('utf-8').strip()
        rainlist = response.split('\r\n')
#        writelog(str(time.ctime(int(time.time())))+": Connection succeeded")
        for entry in rainlist:
            rainevent, sep, raintime = entry.partition('|')
            try:
                rain = int(rainevent)
            except:
                rain = 0
            if rain >= min_rain:
                rainfall.append(rain)
    except URLError as e:
        if hasattr(e,'reason'):
            writelog(str(time.ctime(int(time.time())))+": Failed to reach server.")
            writelog(str(time.ctime(int(time.time())))+": Reason: %s" % e.reason)
            writelog(str(time.ctime(int(time.time())))+": Connection Failed")
        elif hasattr(e,'code'):
            writelog(str(time.ctime(int(time.time())))+": Server failed to fulfil request.")
            writelog(str(time.ctime(int(time.time())))+": Error code: %s" % e.code)
            writelog(str(time.ctime(int(time.time())))+": Connection Failed")
    except:
        writelog(str(time.ctime(int(time.time())))+": Some weirdness happened")
    
 #   writelog(str(rainfall))    
    return rainfall

## Create the database if it isnt already there
def create_db(dbfile):
    if os.path.isfile(db_file):
        pass
    else:
        db_conn = sqlite3.connect(db_file,detect_types=sqlite3.PARSE_DECLTYPES)
        c = db_conn.cursor()
        c.execute('''create table weather
	    (ID integer primary key not null,
	     DATETIME timestamp,
      	     RAINLIST text,
	     AVERAGE integer,
	     ROLL_AV integer,
             PREV_RAIN integer,
	     PUMP_STATUS integer);''')

        c.execute('''create table settings
            (ID integer primary key not null,
             MIN_RAIN integer,
             MIN_RAV integer,
             MIN_PREV integer,
             PERIOD integer,
             LENGTH integer);''')

        c.execute('''create table sensors
            (ID integer primary key not null,
	     DATETIME timestamp,
             SOIL integer,
             TEMP integer,
             LIGHT integer);''')

        c.execute("insert into settings (ID,MIN_RAIN,MIN_RAV,MIN_PREV,PERIOD,LENGTH) \
                   values (NULL,?,?,?,?,?)", (0,20,20,6,10));
        db_conn.commit()
        c.close()
        db_conn.close()

## get last five averages and add the current one
## return the rolling average
def rolling_av(average):
    db = sqlite3.connect(db_file)
    c = db.cursor()
    now = datetime.datetime.now()
    period = datetime.timedelta(minutes=50)
    newtime = now - period
    c.execute("select * from weather where DATETIME > ?",(newtime,))
    dataset = c.fetchall()
    c.close()
    count = 0
    average = 0
    try:
        for row in dataset:
            count = count + 1
            average = average + row[3]
        rolling_average = average / count
    except:
        rolling_average = 0
    return int(rolling_average)

## Grab the data since a given time period and 
## calculate the average rolling average over that period
def previous_rain(period):
    db = sqlite3.connect(db_file)
    c = db.cursor()
    date_now = datetime.datetime.now()
    range = datetime.timedelta(hours=period)
    new_time = date_now - range
    c.execute("select * from weather where DATETIME > ?", (new_time,))
    prev_dataset = c.fetchall()
    c.close
    prev_average = []
    prev_rain_list = []
    if prev_dataset == []:
        prev_average = [0,0]
        prev_rain_list = [0,0]
    else:
        for row in prev_dataset:
            prev_rain_list.append(row[5])
            prev_average.append(row[4])
    prev_rain = int(numpy.mean(prev_average))
    return prev_rain, prev_average, prev_rain_list

def sensor_data(period):
	db = sqlite3.connect(db_file)
	c = db.cursor()
	date_now = datetime.datetime.now()
	range = datetime.timedelta(hours=period)
	new_time = date_now - range
	c.execute("select SOIL, TEMP, LIGHT from sensors where DATETIME > ?", (new_time,))
	prev_dataset = c.fetchall()
	c.close
	prev_soil = []
	prev_temp = []
	prev_light = []
	if prev_dataset == []:
		prev_soil = [0,0]
		prev_temp = [0,0]
		prev_light = [0,0]
	else:
		for row in prev_dataset:
			prev_soil.append(row[0])
			prev_temp.append(row[1])
			prev_light.append(row[2])
	return prev_soil, prev_temp, prev_light

## Insert the data
def write_data(rainlist, prev_period, min_rav, min_prev):
#    writelog("Write data; submitted: "+str(rainlist)+"\n"+str(prev_period)+"\n"+str(min_rav)+"\n"+str(min_prev))
    date = datetime.datetime.now()
    av_rain = int(numpy.mean(rainlist))
    roll_av = rolling_av(av_rain)
#    writelog("Write data; calculated: "+str(date)+"\n"+str(av_rain)+"\n"+str(roll_av))    
    db_conn = sqlite3.connect(db_file)
#    writelog("db_conn created")   
    prev = previous_rain(prev_period)[0]
#    writelog("Write data; prev_period: "+str(prev))
    sensors = check_sensors(10)
#    writelog("Write data; check_sensors: "+str(sensors))
    soil = sensors[0]
    temp = sensors[1]
    light = sensors[2]
#    writelog(str(roll_av)+str(soil)+str(temp)+str(light))
    if soil < 10:
        pump_status = 1
        status_leds(1)
    elif roll_av >= min_rav or prev >= min_prev:
        pump_status = 0
        status_leds(0)
    else:
        pump_status = 1
        status_leds(1)
#    writelog("Weather: "+str(date)+str(rainlist)+str(av_rain)+str(roll_av)+str(prev)+str(pump_status))
#    writelog("Sensors:"+str(date)+str(soil)+str(temp)+str(light))
    c = db_conn.cursor()
    c.execute("INSERT INTO WEATHER (ID,DATETIME,RAINLIST,AVERAGE,ROLL_AV,PREV_RAIN,PUMP_STATUS) \
	VALUES (NULL,?,?,?,?,?,?)", (date,str(rainlist),av_rain,roll_av,prev,pump_status));
    db_conn.commit()

    c.execute("INSERT INTO SENSORS (ID,DATETIME,SOIL,TEMP,LIGHT) \
	VALUES (NULL,?,?,?,?)", (date, soil, temp, light));
    db_conn.commit()

    db_conn.close()
#    writelog(str(time.ctime(int(time.time())))+": Data written")

def create_graphs(rainlist, settings):
    pngpath = "/home/pi/python/waterer/static/test.png"
    prev_setpoint = settings[3]
    fut_setpoint = settings[2]
    raindata = previous_rain(settings[4])
    s_data = sensor_data(settings[4])
    prev_rain_list = raindata[1]
    prev_avrain_list = raindata[2]
    soil = s_data[0]
    temp = s_data[1]
    light = s_data[2]
    graphs = CreateGraphs(prev_setpoint,
                 fut_setpoint,
                 rainlist,
                 prev_rain_list,
                 prev_avrain_list,
                 soil,
                 temp,
                 light,
                 pngpath
                )
    graphs.doit()

s = get_settings()
rainlist = check_forecast(s[1])
write_data(rainlist,s[4],s[2],s[3])
create_graphs(rainlist, s)
