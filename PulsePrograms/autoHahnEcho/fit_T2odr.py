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
picfile = sys.argv[2]
data = N.loadtxt(filename)
x = data[:,0]
y = data[:,1]

n = len(y)

p0 = [ N.abs(y).max(), x[(N.abs(y)/N.abs(y).max()-1/N.e).argmin()], 1]
print "Startparameter:",p0

odr_model = scipy.odr.Model(T2)
odr_data = scipy.odr.Data(x=x,y=y)
odr = scipy.odr.ODR(odr_data, odr_model, p0, ifixx=(1,))
odr.run()

#res,covvar,misc,info,success = leastsq(func, p0, args=(x,y), full_output=1)
#print "A: %.2f\nb: %.2f\n T1:%.2fs\nbeta: %.2f\n"%(amplitude, b, T1, beta)

fitresults = []
skipped = 0 
#p0 = list(res[:]+0)
print "Resampling ... "
t = time.time()
for i in xrange(runs):
	indices = N.random.randint(0,n,n)
	#print indices
	xnew,ynew = x[indices],y[indices]
	odr_data = scipy.odr.Data(x=x,y=y)
	odr = scipy.odr.ODR(odr_data, odr_model, p0, ifixx=(1,))
	odr.run()
	#run_res,run_success = leastsq(func,p0,args=(xnew,ynew), maxfev=150, warning=0)
	fitresults.append(odr.output.beta)
t -= time.time()
#print "\nUnsuccessful fits: %i out of %i (%.1f%%)"%(skipped, runs, skipped/float(runs)*100)
print "Time: %.1fs\n"%(-t)
fitresults = N.array(fitresults)
print "\n***** Boostrap/Resampling:\n"
print "A:   ",fitresults[:,0].mean(), "+/-",fitresults[:,0].std()/N.sqrt(runs-skipped)
print "T2:  ",fitresults[:,1].mean(), "+/-",fitresults[:,1].std()/N.sqrt(runs-skipped)
print "beta:",fitresults[:,2].mean(), "+/-",fitresults[:,2].std()/N.sqrt(runs-skipped)
if success == 1:
	print "\n***** Standard Fit:\n"
	amplitude, T1, beta = res
	residuals = func(res,x,y)
	errs = N.dot(residuals,residuals)/(len(x)-len(res))
	errs *= N.diagonal(covvar)
	errs = N.sqrt(errs)
	resultstring =  " A   : %8.2f +/- %4.2f \n T2  :%8.4f +/- %4.4f s\n beta: %8.2f +/- %4.2f\n"%(amplitude, errs[0], T1, errs[1], beta, errs[2])
	print resultstring
P.semilogx(x,y,'bo',label=filename)
xr = N.logspace(N.log10(x.min()),N.log10(x.max()),1024)
P.semilogx(xr, T2(res,xr),'r-',label='Fit')
P.ylim(y.min()*1.2,y.max()*1.5)
P.xlabel('Time/s')
P.ylabel('Signal/a.u.')
P.text(0.05,0.6,resultstring,transform = P.gca().transAxes)
P.legend()
P.savefig(picfile)
P.show()
