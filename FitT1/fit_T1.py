#!/usr/bin/env python
import numpy as N
import pylab as P
import tables
import sys,shutil
import time
from scipy.optimize import leastsq
import optparse
import scipy.odr as O
from matplotlib.widgets import SpanSelector


parser = optparse.OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="read HDF file", metavar="FILE", default = 'pool/DAMARIS_data_pool.h5')
parser.add_option("-i", "--image", dest="picfile",
                  help="save to IMAGE", metavar="IMAGE")
parser.add_option("-t", "--title", dest="title",
                  help="set title", metavar="TITLE")
parser.add_option("-w", "--write", dest="save",
                  help="save fit to file", metavar="TITLE", default="")
parser.add_option("-q", "--quiet",
                  action="store_true", dest="quiet", default=False,
                  help="don't show plot")
parser.add_option("-s", "--start",
                  dest="start", default=0,
                  type="int",
                  help="start of integration")
parser.add_option("-e", "--end",
                  dest="end", default=100,
                  type="int",
                  help="end of integration")
parser.add_option("-m", "--method", dest="method",
                  help="set the fit method: InvRec, SatRec, SatRecBase, SatRec2", metavar="TITLE", default="SatRec")

(options, args) = parser.parse_args()


runs = 100
class lims:
	pass

se = lims()


def onselect(xmin, xmax):
#     indmin, indmax = npy.searchsorted(x, (xmin, xmax))
#     indmax = min(len(x)-1, indmax)
# 
#     thisx = x[indmin:indmax]
#     thisy = y[indmin:indmax]
#     line2.set_data(thisx, thisy)
#     ax2.set_xlim(thisx[0], thisx[-1])
#     ax2.set_ylim(thisy.min(), thisy.max())
#     fig.canvas.draw()
	se.min = xmin
	se.max = xmax
#	print se.max,se.min
	pass

def get_perc(perc,an_array):
	n,l = an_array.shape
	#print n,l,N.diff(an_array[1:3,2])
	rank = perc*(n+1)
	k,d = int(rank), rank-int(rank)
	percs = []
	for i in xrange(l):
		an_array[:,i].sort()
		if 0 < k < n:
			perc = an_array[k,i] + d*N.diff(an_array[k:k+2,i])
		elif k == 0:
			perc = an_array[0,i]
		elif k == n:
			perc = an_array[-1,i]
		percs.append(perc)
	return N.array(percs).flatten()



def InvRec(p,x):
	amplitude, b, T1, beta = p
	return amplitude *( 1 - b * N.exp(-(x/T1)**beta))

def SatRec(p,x):
	amplitude, T1, beta = p
	return amplitude *( 1 - N.exp(-(x/T1)**beta))

def SatRecBase(p,x):
	amplitude, T1, beta, base = p
	return amplitude *( 1 - N.exp(-(x/T1)**beta))+base

def SatRec2(p,x):
    amplitude, T11, T12, r, beta1, beta2, base  = p
    return amplitude * (r * ( 1 - N.exp(-(x/T11)**beta1)  + (1-r)*(1-N.exp(-(x/T12)**beta2)))) + base
def Pesch(p,x):
    amplitude, T11, T12, base  = p
    p_p = 1217/(1217+663.)
    p_w = 1-p_p
    return amplitude * (p_w * ( 1 - N.exp(-(x/T11)))   + p_p*(1-N.exp(-(x/T12)))) + base


methods = {"InvRec":InvRec, 
			"SatRec":SatRec, 
			"SatRecBase":SatRecBase, 
			"SatRec2":SatRec2,
			"Pesch":Pesch}

#def func(p,x,y):
#	return fitfunc(p,x) - y


filename = options.filename
picfile  = options.picfile

if options.method not in methods:
	raise SyntaxError, "Must be one of:"%(methods.keys)

fitfunc  = methods[options.method]


if fitfunc == InvRec:
	meta = ['A', 'b', 'T1', 'beta']
if fitfunc == SatRec:
	meta = ['A', 'T1', 'beta']
if fitfunc == SatRecBase:
	meta = ['A', 'T1', 'beta','base']
if fitfunc == SatRec2:
    meta = ['A', 'T11','T12','r11', 'beta1', 'beta2', 'base']
if fitfunc == Pesch:
    meta = ['A', 'T11','T12','base']
try:
	h5 = tables.openFile(filename)
	start = 4.65e-6
	stop = 1e-5
	x = []
	y = []
	yamp = []
	tm_max = 0
	
	folder = '/data_pool/'
	folder_dict= {}
	i = 0
	for group in h5.walkGroups('/data_pool'):
		if group._v_name.startswith('dir'):
			folder_dict[i]=group._v_name
			print "[ %i ] %s"%(i,group._v_name)

			i+=1
	if len(folder_dict.keys()) > 1:
		folder += folder_dict[input('Select group: ')]
	else:
		pass
	tm_name = 'description_tm'
	
	for data in h5.walkNodes(folder,'CArray'):
		print data._v_parent._v_name
		if data._v_parent._v_name.lower().startswith('dict_acc'):
			if tm_name not in data._v_parent._v_attrs._v_attrnames:				
				for i,name in  enumerate(data._v_parent._v_attrs._v_attrnames):
					print "[ %i ] %s"%(i,name)
				tm_num = input('Which one is tm?: ')
				tm_name = data._v_parent._v_attrs._v_attrnames[tm_num]
			tm = float(data._v_parent._v_attrs[tm_name])
			if tm > tm_max:
				tm_max = tm
				data_max = data
	if not options.quiet:
		fig = P.figure()
		ax = fig.add_subplot(111)
		ax.hold(True)
		ax.plot(data_max[:,0],'r-',label='real')
		ax.plot(data_max[:,2],'b-',label='imag')
		ax.hold(False)
		ax.legend()		
	
		# set useblit True on gtkagg for enhanced performance
		span = SpanSelector(ax, onselect, 'horizontal', useblit=False,
						rectprops=dict(alpha=0.5, facecolor='red') )
		#print "Span selected",span
		P.show()
		#s,e = [int(i) for i in raw_input('Integrate between: ').split()]
		s,e = int(min(se.max,se.min)),int(max(se.max,se.min))
	if options.quiet:
		s = min(options.start,options.end)
		e = max(options.start,options.end)
	print "Span selected",s,e
	for i,data in enumerate(h5.walkNodes(folder,'CArray')):
		if data._v_parent._v_name.lower().startswith('dict_acc'):
#			if i==0: print data._v_parent._v_attrs._f_list()
			tm = float(data._v_parent._v_attrs[tm_name])
			x.append(tm)
			sr = data._v_parent.indices.col('dwelltime')
			mag = data[max(s,0):e,0].mean()
			amp  = (data[max(s,0):e,0].mean()**2+
					data[max(s,0):e,2].mean()**2)**0.5

# 			mag = data[int(start/sr):int(stop/sr),2].mean()
# 			amp  = (data[int(start/sr):int(stop/sr),0].mean()**2+
# 					data[int(start/sr):int(stop/sr),2].mean()**2)**0.5
			y.append(mag)
			yamp.append(amp)
#	print  data._v_parent,x,y
#	print y,type(y)
#	print N.max(y)
	print "Amps: %f Mag: %f"%(N.max(yamp),N.max(y))
	t = N.array(x)
	y = N.array(y)
	x = t
except IOError:
	d = N.loadtxt(filename)
	x = d[:,0]
	y = d[:,1]

n = len(y)



if fitfunc == InvRec:
	p0 = [ abs(y).max()*2, 1.9, x[abs(y).argmin()]*N.log(2), 1]
	ifixb = (1,1,1,1)
if fitfunc ==  SatRec:
	p0 = [ abs(y).max(), x[abs(y/y.max()- 1/N.e).argmin()], 1]
	ifixb = (1,1,1)
if fitfunc ==  SatRecBase:
	p0 = [ abs(y).max(), x[abs(y/y.max()- 1/N.e).argmin()], 1, y.min()]
	ifixb = (1,1,1,1)

if fitfunc ==  SatRec2:
    p0 = [ abs(y).max(),0.9, x[abs(y/y.max()- 1/N.e).argmin()],x[abs(y/y.max()- 1/N.e).argmin()]*50 ,1, 0.7, 0]
    p0=[1.3e+03, 0.018, 1.18, 0.799, 1.03, 1.01, 0]
    ifixb = (1,1,1,1,1,1,0)

if fitfunc ==  Pesch:
	T1_est =  x[abs(y/y.max()- 1/N.e).argmin()]
	p0 = [ abs(y).max(), T1_est/3, T1_est, 0]
	ifixb = (1,1,1,1)



print "Startparameter:",p0

odr_model = O.Model(fitfunc, meta=meta)
odr_data = O.Data(x,y)
odr = O.ODR(odr_data,odr_model, p0, ifixx=(0,), ifixb=ifixb, maxit=400)
odr.run()
if not int(odr.output.info) in [1,2]: 
	print odr.output.pprint()
	#raise ValueError(odr.output.pprint())
result = odr.output.beta
result_sd = odr.output.sd_beta
#print x,y

###### bootstrap start
bootstrap_result = []
bsn = 100  # number of fits
for i in xrange(bsn):
	draw_random = N.random.randint(0,len(x),len(x))
	x_bootstrap = x[draw_random]
	y_bootstrap = y[draw_random]
	odr_bsdata = O.Data(x_bootstrap,y_bootstrap)
	# start value result
	odr = O.ODR(odr_bsdata, odr_model, result, ifixx=(0,))
	odr.run()
	if int(odr.output.info) in [1,2]:
		bootstrap_result.append(odr.output.beta)


bootstrap_result = N.array(bootstrap_result)#.sort()
rank_95 = get_perc(0.95, bootstrap_result)
rank_05 = get_perc(0.05, bootstrap_result)
mean_bs = bootstrap_result.mean(axis=0)
try:
	#print bootstrap_result
	print
	print "#"*10,"Bootstrap results 0.05, %i runs"%bsn,"#"*10
	print
	r = ""
	for i, var  in enumerate(meta):
		r +=  "%5s: %10.3g ( %.3g %.3g )\n"%(var,mean_bs[i],rank_95[i],rank_05[i])
	
	print r
	###### bootstrap end
except:
	pass


#print "Temperature:",data._v_parent._v_attrs.description_T_sample,"K"
resultstring = ""
for i, var  in enumerate(meta):
	r =  "%5s: %10.3g +/- %.3g"%(var,result[i],result_sd[i])
	resultstring += r+"\n"
if options.save:
	print "Write results to %s"%(options.save)
	f=open(options.save,'w')
	print "\n","*"*10,"Standard Fit:","*"*10,"\n"
	f.write('#')
	for var in meta:
		f.write('%s %s_sd '%(var,var))
	f.write('\n')
	try:
		f.write("\n#%s\n"%(data._v_parent._v_attrs.description_T_sample))
	except:
		pass
		
	for i, var  in enumerate(meta):
		f.write('%.3g %.3g '%(result[i],result_sd[i]))
	f.write('\n')
	f.close()
print resultstring

P.figure(figsize=(5,5))


P.semilogx(x,y,'bo',label=options.title)
xr = N.logspace(N.log10(x.min()),N.log10(x.max()),1024)
P.semilogx(xr, fitfunc(result,xr),'r-',label='Fit')
#P.ylim(y.min()*1.2,y.max()*1.5)
P.ylim(y.min()*1.05,y.max()*1.3)

P.xlabel('Time/s')
P.ylabel('Signal/a.u.')
P.text(0.05,0.6,resultstring,transform = P.gca().transAxes)
P.legend()
if not options.quiet:
	P.show()
if not picfile == None:
	P.savefig(picfile)

