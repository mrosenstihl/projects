conv = 6.39e-5
tm=0
import re, os
tau_pattern = re.compile('Amplitude_.*_')
tau_num = re.compile('\d+e[+,-]?\d')

delta_pattern = re.compile('delta_\d\.\dms')
delta_num = re.compile('\d\.\d')
gamma = 2.67522e8
files = [afile for afile in os.listdir('.') if afile.endswith('dat')]
ds = []
for afile in files:
	print afile
	tau = float(re.search(tau_num,re.search(tau_pattern,afile).group()).group())
	delta = float(re.search(delta_num,re.search(delta_pattern,afile).group()).group())
	delta *= 1e-3
#	num = '%.0fe-3'%(tau/1e-3)
	
#	filename = 'Amplitude_%s_delta_1ms.dat'%num
	#filename = 'Amplitude_%s'%num
	#data = loadtxt(filename.replace('-0','-'))
	data = loadtxt(afile)
	x = data[:,0]
	y = data[:,1]
	xv = (gamma*x*delta*conv)**2*( (tau+tm) / 4 + delta/12. + 5.*delta/16./pi**2)
	y_val = y/y.max()
	res = polyfit(xv[y_val>5e-2],log(y_val)[y_val>5e-2],1)
	semilogy(xv,y_val, 'o-', label="%.0f ms %.0f ms"%(tau/1e-3, delta/1e-3))
	print res
	ds.append(res[0])
ylim(1e-3,1)
xlim(0,1.5e10)
legend()
