import re, os,sys
import numpy as N
from tables import *
import scipy.odr
import pylab as P


conv = 6.36e-5
gamma = 2.67522e8

start = 50
stop = 250


def diffusion(p,x):
	sig = N.exp(-p[0]*x)+p[1]
	return sig

try :
	filename = sys.argv[1]
except IndexError:
	filename = 'pool/DAMARIS_data_pool.h5'
hdf = openFile(filename)
results = {}
for temp in [1]:
	for run in hdf.walkNodes('/data_pool'):
		print run._v_name
		if run._v_name.startswith('dict_Hahn'):
			dwell = run.indices.col('dwelltime')
			delta = float(run._v_attrs.description_delta)
			tau	  = float(run._v_attrs.description_tau)
			dac   = float(run._v_attrs.description_dac)
			# b Faktor
			bfac = (gamma*dac*delta*conv)**2*( (tau) / 4 + delta/12. + 5.*delta/16./N.pi**2)
			
			real,imag = run.accu_data[:,0],run.accu_data[:,2]
			mag = N.sqrt(real**2 + imag**2)
			
			# Signalamplitude
			sig = mag[start:stop].mean()-mag[-1024:].mean()
			sig_err= mag[-1024:].std()/N.sqrt((stop-start))
			
			try:
				results.append([bfac,sig,sig_err,delta,tau,dac])
			except:
				results = []
				results.append([bfac,sig,sig_err,delta,tau,dac])
	results = N.array(results)

	x = results[:,0]
	y = results[:,1]
	y_err = results[:,2]
	delta = results[:,3]
	tau = results[:,4]
	dac = results[:,5]

	# Create sets
	deltas = set(delta)
	taus = set(tau)

	results_d=[]
	# Select the single measurements sets (same tau,tm,delta) and normalize them to g==0
	mask = [y>5e-2]
	for de in deltas:
		for ta in taus:
			P.subplot(211)
			ind_de =   delta==de
			ind_ta =   tau==ta
			ind_dac0 = dac==0
			# This is a set
			ind = ind_de*ind_ta
			ind_norm = ind_de*ind_ta*ind_dac0
			y_err[ind] /= y[ind_norm]
			y[ind] /= y[ind_norm]
			x_err = x*0.05

			result_d =  N.polyfit(x[ind*(y>20e-2)],N.log(y[ind*(y>20e-2)]),1)
			P.semilogy(x[(y>5e-2)*ind], y[ind*(y>5e-2)],'o')
			P.semilogy(x[(y>20e-2)*ind], N.exp(N.polyval(result_d,x[ind*(y>20e-2)])),'-')

			results_d.append([ta,result_d[0]])
	results_d = N.array(results_d)
	N.savetxt('collagen_07h2o_diffusion.dat', results_d )
	P.subplot(212)
	P.loglog(results_d[:,0],-1*results_d[:,1],'o')
	P.show()
	
	#assume 5% error from calibration
	data = scipy.odr.Data(x=x[mask],y=y[mask],wd=y_err[mask])
	model = scipy.odr.Model(diffusion)
	odr = scipy.odr.ODR(data,model,beta0=[2e-13,0.1], ifixx=(1,))
	odr.run()
	print "ODR Result"
	odr.output.pprint()
	print "Polyfit"
	print N.polyfit(x[y>5e-2],N.log(y[y>5e-2]),1)

