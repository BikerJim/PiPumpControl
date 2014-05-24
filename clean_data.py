#!/usr/bin/python3
## Deletes rows from the database older than specified time period (stp)
## Called by crontab once a week
## Stops db getting too big

import sqlite3
import datetime

stp = 7
db = "/home/pi/python/waterer/weather_data.db"

con = sqlite3.connect(db)
c = con.cursor()

now = datetime.datetime.now()
timedelta = datetime.timedelta(days=stp)
timepoint = now - timedelta

c.execute("delete from weather where DATETIME < ?", (timepoint,))
con.commit()

c.execute("delete from weather where DATETIME < ?", (timepoint,))
con.commit()

c.close()
con.close()
