import re, os,sys
import numpy as N
from tables import *
import scipy.odr as O

conv = 6.36e-5
gamma = 2.67522e8

start = 0.6e-3 
stop = 1.35e-3


def diffusion(p,x):
	sig = N.exp(-p[0]*x)
	return sig



hdf = openFile(sys.argv[1])
sigs = []

for run in hdf.walkNodes('/data_pool','Group'):
	#print run._v_name
	try:
		run._g_checkHasChild('accu_data')

		dwell = run.indices.col('dwelltime')
		delta = float(run._v_attrs.description_delta)
		tau	  = float(run._v_attrs.description_tau)
		tm    = float(run._v_attrs.description_tmix)
		dac   = float(run._v_attrs.description_dac)
		# b Faktor
		bfac = (gamma*dac*delta*conv)**2*( tm  + 3./2 * tau - delta/6. + 5.*delta/8./N.pi**2)
		
		real,imag = run.accu_data[:,0],run.accu_data[:,2]
		mag = N.sqrt(real**2 + imag**2)
		b  = int(start/dwell)
		e = int(stop/dwell)
		b = 450
		e = 550
		print  b,e
		# Signalamplitude
		sig = mag[b:e].mean()-mag[-512:].mean()
		sig_err= mag[-512:].std()/N.sqrt((stop-start))
		sigs.append([sig, sig_err, tm, dac, bfac])
	except:
		pass
print sigs
sigs = N.array(sigs)
dacs = set(sigs[:,-2])
tms = set(sigs[:,2])
ref_dac = min(dacs)
dacs.remove(ref_dac)

for tm in tms:
	tm_set = sigs[:,2] == tm
	ref_set =  sigs[:,-2] == ref_dac
	ref_sig = sigs[:,0][tm_set & ref_set ]
	sigs[:,:2] /= ref_sig

p = []
import pylab as P
P.subplot(211)
for dac in dacs:
	q_set = sigs[:,-2] == dac
	ref_sig = sigs[:,-2] == ref_dac
	x,y = sigs[:,-1][q_set], sigs[:,0][q_set]
	#P.figure()
	P.semilogy(x,y,'o')
	try:
		p.append([ -N.polyfit(x[y>0.05],N.log(y[y>0.05]),1)[0],gamma*dac*delta*conv])
	#	P.title("G=%.1f T/m"%(dac*conv))
	#	P.draw()
	except:
		pass
p = N.array(p)
P.subplot(212)
#P.semilogy(p[:,1]*1e-6,p[:,0],'o')
P.plot(p[:,1]*1e-6,p[:,0],'o')
#hannes = P.loadtxt('/home/markusro/PulsePrograms/13int/ergebnisse263aa',skiprows=7, usecols=(2,7))
#P.semilogy(hannes[:,0]*gamma*13.2*1e-6,hannes[:,1],'D')
#N.savetxt('hannes.dat', N.array([hannes[:,0]*gamma*13.2*1e-6,hannes[:,1]]).T)

P.xlabel('q in  1/um')
P.ylabel('D in $\mathsf{m^2/s}$')
P.draw()
#P.savefig('q_dep.ps')
P.show()
#data = scipy.odr.Data(x=x,y=y,wd=y_err)
#model = scipy.odr.Model(diffusion)
#odr = scipy.odr.ODR(data,model,beta0=[2e-13,0.1], ifixx=(1,))
#odr.run()
#print odr.output.beta
#print N.polyfit(x[y>5e-2],N.log(y[y>5e-2]),1)

