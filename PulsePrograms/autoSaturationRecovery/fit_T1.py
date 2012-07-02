#!/usr/bin/env python
import numpy as N
import pylab as P
import tables
import sys,shutil
import time
from scipy.optimize import leastsq
import optparse
import scipy.odr as O

parser = optparse.OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="read HDF file", metavar="FILE", default = 'pool/DAMARIS_data_pool.h5')
parser.add_option("-i", "--image", dest="picfile",
                  help="save to IMAGE", metavar="IMAGE")
parser.add_option("-t", "--title", dest="title",
                  help="set title", metavar="TITLE")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="quiet", default=False,
                  help="don't show plot")
(options, args) = parser.parse_args()


runs = 100
def InvRec(p,x):
	amplitude, b, T1, beta = p
	return amplitude *( 1 - b * N.exp(-(x/T1)**beta))

def SatRec(p,x):
	amplitude, T1, beta = p
	return amplitude *( 1 - N.exp(-(x/T1)**beta))

def func(p,x,y):
	return SatRec(p,x) - y

filename = options.filename
picfile=options.picfile


fitfunc = SatRec

if fitfunc == InvRec:
	meta = ['A', 'b', 'T1', 'beta']
if fitfunc == SatRec:
	meta = ['A', 'T1', 'beta']

try:
	h5 = tables.openFile(filename)
	start = 1.65e-6
	stop = 2e-6
	x = []
	y = []
	for data in h5.walkNodes('/data_pool','Array'):
		if data._v_parent._v_name.startswith('dict_acc'):
			x.append(float(data._v_parent._v_attrs.description_tm))
			sr = data._v_parent.indices.col('dwelltime')
			mag = data[int(start/sr):int(stop/sr),0].mean()
			y.append(mag)
	print  data._v_parent,x,y	
	x = N.array(x)
	y = N.array(y)
except:
	d = N.loadtxt(filename)
	x = d[:,0]
	y = d[:,1]
n = len(y)
if fitfunc == InvRec:
	p0 = [ abs(y).max()*2, 1.9, x[abs(y).argmin()]*N.log(2), 1]
if fitfunc ==  SatRec:
	p0 = [ abs(y).max(), x[abs(y/y.max()- 1/N.e).argmin()], 1]

print "Startparameter:",p0

odr_model = O.Model(fitfunc, meta=meta)
odr_data = O.Data(x,y)
odr = O.ODR(odr_data,odr_model, p0, ifixx=(0,))
odr.run()
p1 = odr.output.beta

f=open('T1_data','a')
print "\n***** Standard Fit:\n"
resultstring = ""
for i, var  in enumerate(meta):
	r =  "%5s: %10.2e +/- %.2e"%(var,odr.output.beta[i],odr.output.sd_beta[i])
	resultstring += r+"\n"
	f.write('%.2e %.2e '%(odr.output.beta[i],odr.output.sd_beta[i]))
try:
	f.write("%s\n"%(data._v_parent._v_attrs.description_T_sample))
except:
	pass
print resultstring
P.semilogx(x,y,'bo',label=options.title)
xr = N.logspace(N.log10(x.min()),N.log10(x.max()),1024)
P.semilogx(xr, fitfunc(p1,xr),'r-',label='Fit')
P.ylim(y.min()*1.2,y.max()*1.5)
P.xlabel('Time/s')
P.ylabel('Signal/a.u.')
P.text(0.05,0.6,resultstring,transform = P.gca().transAxes)
P.legend()
if not picfile == None:
	P.savefig(picfile)
if not options.quiet:
	P.show()
