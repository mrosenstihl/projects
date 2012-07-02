#!/usr/bin/env python
import numpy as N
import pylab as P
import sys
import time
import scipy.odr


runs = 10000

def T2(p,x):
	amplitude, T2, beta = p
	return amplitude * N.exp(-(2*x/T2)**beta)

def InvRec(p,x):
	amplitude, b, T1, beta = p
	return amplitude *( 1 - b * N.exp(-(x/T1)**beta))

def func(p,x,y):
	return T2(p,x) - y

filename = sys.argv[1]
try:
	picfile = sys.argv[2]
except:
	picfile = None

data = N.loadtxt(filename)
x = data[:,0]
y = data[:,1]

n = len(y)

p0 = [ N.abs(y).max(), x[(N.abs(y)/y.max()-2/N.e).argmin()], 1]
print "Startparameter:",p0

odr_model = scipy.odr.Model(T2)
odr_data = scipy.odr.Data(x=x,y=y)
odr = scipy.odr.ODR(odr_data, odr_model, p0, ifixx=(0,))
odr.run()

#res,covvar,misc,info,success = leastsq(func, p0, args=(x,y), full_output=1)
#print "A: %.2f\nb: %.2f\n T1:%.2fs\nbeta: %.2f\n"%(amplitude, b, T1, beta)

amplitude, T1, beta = odr.output.beta
a_err, T1_err, beta_err = odr.output.sd_beta
resultstring =  " A   : %8.2f +/- %4.2f \n T2  :%8.2f +/- %4.2f ms\n beta: %8.2f +/- %4.2f\n"%(amplitude, a_err, T1*1e3, T1_err*1e3, beta, beta_err)
print resultstring
P.semilogx(x,y,'bo',label='Data')
xr = N.logspace(N.log10(x.min()),N.log10(x.max()),1024)
P.semilogx(xr, T2(odr.output.beta,xr),'r-',label='Fit')
P.ylim(y.min()*1.2,y.max()*1.5)
P.xlabel('Time(tau)/s')
P.ylabel('Signal/a.u.')
P.text(0.05,0.7,resultstring,transform = P.gca().transAxes)
P.legend()
if not picfile == None:
	P.savefig(picfile)
P.show()
