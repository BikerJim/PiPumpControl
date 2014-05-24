#!/usr/bin/python3
import sqlite3
import os

db_file = "/home/pi/python/waterer/weather_data.db"

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
	     PUMP_STATUS integer);''')

        c.execute('''create table settings
            (ID integer primary key not null,
             MIN_RAIN integer,
             MIN_RAV integer,
             MIN_PREV integer,
             PERIOD integer,
             LENGTH integer);''')

        c.execute("insert into settings (ID,MIN_RAIN,MIN_RAV,MIN_PREV,PERIOD,LENGTH) \
                   values (NULL,?,?,?,?,?)", (0,20,20,6,10));
        db_conn.commit()
        c.close()
        db_conn.close()

create_db(db_file)
