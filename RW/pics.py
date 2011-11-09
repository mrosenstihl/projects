import matplotlib
matplotlib.use('cairo')
import matplotlib.pyplot as P
import numpy as N

for i in xrange(0,10000,10):
	print i
	a = N.loadtxt('data/dist_step%05i.dat'%i)
	P.figure()
	P.plot(a[:,0],a[:,2])
	P.ylim(0,1e4)
	P.savefig('pics/step%05i.png'%i, dpi=72)
