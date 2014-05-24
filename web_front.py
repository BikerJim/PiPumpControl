#!/usr/bin/python3

## The python / sqlite driven web front end
import tornado.ioloop
import tornado.web
import sqlite3
import datetime
import json

def _execute(query):
    """Function to execute queries against a local sqlite database"""
    dbPath = '/home/pi/python/waterer/weather_data.db'
    connection = sqlite3.connect(dbPath)
    cursorobj = connection.cursor()
    try:
            cursorobj.execute(query)
            result = cursorobj.fetchall()
            connection.commit()
    except Exception:
            raise
    connection.close()
    return result

def conv_rain(rain,bool):
    if rain == 0 and bool:
        return "Collect everything"
    elif rain == 0 and not bool:
        return "Always disable"
    elif rain == 1:
        return "Ignore Zeros"
    elif rain in range(1,20):
        return "Light rain (1-20)"
    elif rain in range(20,50):
        return "Medium rain (21-50)"
    elif rain in range(50,100):
        return "Heavy rain (51-100)"
    elif rain in range(100,255):
        return "Torrential rain (101-255)"
    else:
        return "Off the scale"


class MainHandler(tornado.web.RequestHandler):
    """ 
    In tornado we need a class which is our service handler
    """ 
    
    def get(self):
        """
        Get HTTP verb which our service returns a list of rows from
        database
        """
        dbpath = "/home/pi/python/waterer/weather_data.db"
        db_conn = sqlite3.connect(dbpath, detect_types=sqlite3.PARSE_COLNAMES)
        c = db_conn.cursor()
        date_now = datetime.datetime.now()
        range = datetime.timedelta(hours=1)
        new_time = date_now - range
        c.execute('SELECT DATETIME as "dt [timestamp]", RAINLIST, AVERAGE,ROLL_AV,PREV_RAIN,PUMP_STATUS FROM weather where DATETIME > ?', (new_time,))
        weather = c.fetchall()
        settings = _execute('SELECT * FROM settings')
        
        min_rain = settings[0][1]
        min_rav = settings[0][2]
        min_prev = settings[0][3]
        period = settings[0][4]
        length = settings[0][5]
        pump_status = weather[-1][5]
        prev_rain = weather[-1][4]
#        pump_status = weather
        self.render("index.html", 
                     data = weather,
                     min_rain = conv_rain(min_rain, True),
                     min_rav = conv_rain(min_rav, False),
                     min_prev = conv_rain(min_prev, False),
                     period = period,
                     length = length,
                     prev_rain = prev_rain,
                     pump_status = pump_status,
                    )
                    
class UpdateSettingsHandler(tornado.web.RequestHandler):
    def get(self):
        settings = _execute("SELECT max(ID), MIN_RAIN, MIN_RAV,MIN_PREV,PERIOD,LENGTH from settings")
        min_rain = settings[0][1]
        min_rav = settings[0][2]
        min_prev = settings[0][3]
        period = settings[0][4]
        length = settings[0][5]
        
        self.render("edit_settings.html",
                     min_rain = min_rain,
                     min_rav = min_rav,
                     min_prev = min_prev,
                     period = period,
                     length = length,
                   )

    def post(self):
        min_rain = int(self.get_argument("min_rain"))
        min_rav = int(self.get_argument("min_rav"))
        min_prev = int(self.get_argument("min_prev"))
        period = int(self.get_argument("period"))
        length = int(self.get_argument("length"))
        sql = "UPDATE settings SET MIN_RAIN=%s,MIN_RAV=%s,MIN_PREV=%s,PERIOD=%s,LENGTH=%s;" % (min_rain,min_rav,min_prev,period,length)
        _execute(sql)
        self.render("done.html",
                   min_rain = min_rain,
                   min_rav = min_rav,
                   min_prev = min_prev,
                   period = period,
                   length = length,
                   )

class DoneHandler(tornado.web.RequestHandler): 
    def get(self):
        self.render("settings_edited.html")

class BuienradarHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("br.html")

static_path = "/home/pi/python/waterer/static/"
application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/br/", BuienradarHandler),
    (r"/edit_settings/", UpdateSettingsHandler),
    (r"/done/", DoneHandler),
    (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path":""}),
    (r"/static/(.*)", tornado.web.StaticFileHandler,{'path':static_path}),
    ],debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
