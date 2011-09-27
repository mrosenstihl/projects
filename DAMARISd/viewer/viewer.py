import numpy as N
import xmlrpclib
import time
import cPickle
import matplotlib

s = "http://localhost:8001"

server = xmlrpclib.Server(s)
status = server.status()
device_list = status[1]



from pylab import *
from matplotlib.widgets import Button
import pylab
ax = subplot(111)
ax.get_figure().autofmt_xdate(rotation=40)
#subplots_adjust(top=0.8)
subplots_adjust(left=0.25)
t = [time.time(), time.time()+3600]
s = N.zeros(len(t))
l, = plot(epoch2num(t),s, 'b.-', lw=1)
major_formatter = matplotlib.dates.DateFormatter('%d/%m/%y %H:%M:%S')
minor_formatter = matplotlib.dates.DateFormatter('%d/%m/%y %H:%M:%S')
l.get_axes().axes.xaxis.set_major_formatter(major_formatter)
l.get_axes().axes.xaxis.set_minor_formatter(minor_formatter)
l.get_axes().autoscale_view()		


class DamarisdViewer:
	def __init__(self, alist):
		#print self.callback
		self.i = 0.0
		print alist
		for dev in alist:
			self.device = dev
			# self.dev = self.plotit
			setattr(self,dev,Plottit(dev).plotit)
			# self.dev.mydevice = dev
			#setattr(getattr(self,dev),'mydevice',dev)
			this_button =  dev+'_button'
			this_axis =  'ax_'+dev
			# self.myaxis = axes ...
			setattr(self,this_axis,axes([0.025, 0.9-self.i, 0.15, 0.08]))
			#exec("self.%s.autoscale_view()"%this_axis)
			# self.mybutton = Button(self.myaxis,'device')
			setattr(self,dev+'_button',Button(getattr(self,this_axis),dev))
			# self.dev_button.on_clicked(plotit)
			exec("self.%s.on_clicked(self.%s)"%(this_button,dev))
			#b = getattr(self,mybutton)
			#b.on_clicked(getattr(self,dev))			
			self.i += 0.1
		show()


class Plottit:
	def __init__(self,dev):
		self.device = dev
	def plotit(self,event):
		# read data from last 2 hours
		res = cPickle.loads(server.get_data(self.device, 0, time.time()))
		ydata = res[:,1]
		xdata = epoch2num(res[:,0])
		l.set_xdata(xdata)	
		l.set_ydata(ydata)
		ax.set_title(self.device)
		ax.set_xlim(xdata.min(),xdata.max())
		ax.set_ylim(ydata.min(),ydata.max())
		draw()

DamarisdViewer(device_list)