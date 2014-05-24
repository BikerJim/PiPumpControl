#!/usr/bin/python3
## A test script to try out the graphing module import matplotlib.pyplot as pyplot

class CreateGraphs():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    def __init__(self,rav_sp, past_sp,forecast,prev_rav,prev_rain,soil,temp,light,pngfile):
        self.rav_setpoint = rav_sp
        self.past_setpoint = past_sp
        self.forecast = forecast
        self.prev_rav = prev_rav
        self.prev_rain = prev_rain
        self.soil = soil
        self.temp = temp
        self.light = light
        self.pngfile = pngfile

    def doit(self):
        self.fig = self.plt.figure()
        fax = self.fig.add_subplot(3,1,1)
        ravx = self.fig.add_subplot(3,1,3)
        prevx = self.fig.add_subplot(3,1,3)
        sensx = self.fig.add_subplot(3,1,2)
        prev_period = len(self.prev_rain)

        ravx.axhline(self.past_setpoint,color='r', linewidth='.5')
        ravx.axhline(self.rav_setpoint,color='r', linestyle='--', linewidth='.5')

        fax.set_title('Next two hours')
        fax.set_xlabel('Time')
        fax.set_ylabel('Rain')
        fax.plot(self.forecast, linewidth='0.5')
        fax.axis([0,17,0,150])

        ravx.set_title('Last period ('+str(prev_period)+' checks)')
        ravx.set_ylabel('Rain')
        ravx.set_xlabel('Time')
        ravx.axis([0,int(prev_period),0,150])
        ravx.plot(self.prev_rain,marker='*', linestyle='--',  color='m')
        prevx.plot(self.prev_rav, color='k')
        
        sensx.set_title('Sensor readings, last '+str(prev_period)+' checks)')
        sensx.set_xlabel('Time')
        sensx.axis([0,int(prev_period),0,50])
        sensx.plot(self.soil, color='r', label="Moisture")
        sensx.plot(self.temp, color='k',linestyle='--', label="Temp")
        sensx.plot(self.light, color='y', label="Light")
        sensx.legend(framealpha=0.5)
        self.plt.tight_layout()
        self.fig.savefig(self.pngfile)

#pngpath = "/home/pi/python/waterer/static/test.png"
#forecast = [0, 60, 75, 78, 38, 75, 90, 89, 73, 77, 80, 84, 85, 74, 65, 69, 68, 29]
#roll_av = [30, 45, 58, 88, 35, 90, 50, 73, 77, 80, 84, 85, 74, 65, 69, 68, 29, 112]

#graph = create_graphs(150,80,forecast,roll_av,roll_av,pngpath)
#graph.doit()

