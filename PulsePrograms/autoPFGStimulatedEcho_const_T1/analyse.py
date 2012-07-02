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



hdf = openFile(sys.argv[1])
temperature_runs = [run for run in hdf.root.data_pool if run._v_name.startswith('dir_')]
results = {}

for temperature in temperature_runs:
	tbvt = temperature._v_name
	print tbvt
	for run in hdf.walkNodes(temperature):
		print run._v_name
		if run._v_name.startswith('dict_grad'):
			dwell = run.indices.col('dwelltime')
			delta = float(run._v_attrs.description_delta)
			tau	  = float(run._v_attrs.description_tau)
			tm    = float(run._v_attrs.description_tm)
			dac   = float(run._v_attrs.description_dac)
			# b Faktor
			bfac = (gamma*dac*delta*conv)**2*( (tau+tm) / 4 + delta/12. + 5.*delta/16./N.pi**2)
			
			real,imag = run.accu_data[:,0],run.accu_data[:,2]
			mag = N.sqrt(real**2 + imag**2)
			
			# Signalamplitude
			sig = mag[start:stop].mean()-mag[-1024:].mean()
			sig_err= mag[-1024:].std()/N.sqrt((stop-start))
			
			try:
				results[tbvt].append([bfac,sig,sig_err,delta,tau,tm,dac])
			except:
				results[tbvt] = []
				results[tbvt].append([bfac,sig,sig_err,delta,tau,tm,dac])
	results[tbvt] = N.array(results[tbvt])

	x = results[tbvt][:,0]
	y = results[tbvt][:,1]
	y_err = results[tbvt][:,2]
	delta = results[tbvt][:,3]
	tau = results[tbvt][:,4]
	tm = results[tbvt][:,5]
	dac = results[tbvt][:,6]

	# Create sets
	deltas = set(delta)
	taus = set(tau)
	tms = set(tm)

	P.subplot(211)
	# Select the single measurements sets (same tau,tm,delta) and normalize them to g==0
	mask = [y>5e-2]
	for de in deltas:
		for ta in taus:
			for t in tms:
				ind_de =   delta==de
				ind_ta =   tau==ta
				ind_t =    tm==t
				ind_dac0 = dac==0
				# This is a set
				ind = ind_de*ind_ta*ind_t
				ind_norm = ind_de*ind_ta*ind_t*ind_dac0
				y_err[ind] /= y[ind_norm]
				y[ind] /= y[ind_norm]
				x_err = x*0.05
	#assume 5% error from calibration
	data = scipy.odr.Data(x=x[mask],y=y[mask],wd=y_err[mask])
	model = scipy.odr.Model(diffusion)
	odr = scipy.odr.ODR(data,model,beta0=[2e-13,0.1], ifixx=(1,))
	odr.run()
	print "ODR Result"
	odr.output.pprint()
	print "Polyfit"
	print N.polyfit(x[y>5e-2],N.log(y[y>5e-2]),1)

	P.semilogy(x[mask],y[mask],'o')
	P.show()
