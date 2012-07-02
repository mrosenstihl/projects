#!/usr/bin/env python
try:
	import numpy as N
except ImportError:
	raise ImportError, "Numpy not found! http://numpy.scipy.org"
	
import optparse
from optparse import OptionParser

description = "Calculates a periodogram of unevenly sampled data based on Lombs algorithm. \
				Idea taken from Numerical Recipes. The input data file should be two columns: first column is time, second is the value.\
				Lines starting with '#' are treated as comments"
usage = "%prog -f INFILENAME -o OUTFILENAME"
epilog="Written in 2008. Send bugs to markus.rosenstihl@physik.tu-darmstadt.de"

parser = OptionParser(version="%prog Version 0.9rc1",usage=usage, epilog=epilog, description=description)
parser.add_option("-f", "--file", dest="infilename",
                  help="Read data from INFILE", 
                  metavar="INFILE")

parser.add_option("-o", "--out", dest="outfilename",
                  help="Write data to OUTFILE", 
                  metavar="OUTFILE")
                  
parser.add_option("--osample",
                  type="int", 
                  dest="ofac", 
                  default=4,
                  help="Over-sampling factor. [default: %default]")

parser.add_option("--hifac",
                  type="float", 
                  dest="hifac", 
                  default=1.5,
                  help="This factor describes how much to go over the 'theoretical' nyquist frequency (theoretical means here: N/2T). [default: %default]")

parser.add_option("--debug",
                  action="store_true", 
                  dest="debug", 
                  default=False,
                  help="Debug, for developement use only [default: %default]")

                  
(options, args) = parser.parse_args()

if not options.infilename and not options.debug:
	print "Input file missing! Type lomb.py -h for help"
	parser.print_usage()
	quit()

def getpeak(z,data):
	peak = 0
	last_position = 0
	peak_positions = []
	for i,value in enumerate(data[:,1]):
		if value > z and i > last_position:
			for j,value in enumerate(data[i:,1]):
				if value < z:
					peak += 1
					#print "Peak at",data[i+j,0]
					last_position = j+i
					peak_positions.append(data[last_position,0])
					break
	return peak, peak_positions

def getz(M,prob):
	return N.log(-1/((1-prob)**(1.0/M)-1))

def ampfreq(f):
	sinsum = N.dot(N.sin(4*N.pi*f*x), evec)
	cossum = N.dot(N.cos(4*N.pi*f*x), evec)
	tau = N.arctan2(sinsum, cossum)
	arg = 2*N.pi*f*(x-tau)
	n1 = N.dot(ycorr, N.cos(arg))**2
	n2 = N.dot(ycorr, N.sin(arg))**2
	d1 = N.cos(2*N.pi*f*x)
	d2 = N.sin(2*N.pi*f*x)
	p = 0.5/yvar*(n1/N.dot(d1,d1)+n2/N.dot(d2,d2))
	return p


if options.debug:
	import numpy.fft.fftpack as FT
	#over-sampling factor
	ofac = 4
	
	# how high to go in frequency
	# relativ to nyquist
	#hifac = f_high/f_nu
	# Number of frequencies np = ofac*hifac/2*N
	hifac = 1.5
	start = 0
	stop = 10
	length = 121
	#dwell = 0.5
	N.random.seed(1)
	freq1 = 0.1
	amp1 = 0.5
	freq2 = 0.2
	amp2 = 0.5
	freq3 = 0.9
	amp3 = 0.5
	ne_strength=0
	
	#print "Demo data:\n
	#Points: %{length}\n
	#Dwell:  %{dwell}\n"%{'lenth':length, 'dwell':dwell}
	print """Demo data:
	Freq 1: 0.1  0.5
	Freq 2: 0.25 0.2
	Freq 3: 0.9  0.3"""
	
	def artificial_data(x_data):
		return amp1*N.sin(2*N.pi*freq1*x_data)\
				+ amp2*N.sin(2*N.pi*freq2*x_data)\
				+ amp3*N.sin(2*N.pi*freq3*x_data)\
				+ ne
	
	ne = N.random.randn(length)*ne_strength
	x_data = N.linspace(start,stop,length)
	dwell = N.diff(x_data).mean()
	y_data = artificial_data(x_data)
	
	fty = FT.rfft(y_data)
	#ftx = FT.fftshift(FT.fftfreq(len(y),1.0))
	ftx = FT.fftfreq(len(x_data),dwell)[:len(fty)]
	nyquist = 0.5/dwell
	print "Nyquist",nyquist
	#print ftx, N.abs(fty)
	ft = N.empty((len(fty),2))
	ft[:,1] = N.abs(fty)/N.abs(fty).max()
	ft[:,0] = ftx

#	Save the evenly spaced data

	N.savetxt('test/data_evenly_spaced.dat', N.asarray([x_data,y_data]).T)
	N.savetxt('test/FFT_evenly_spaced.dat' , ft)
	
#	This is some unevenly spaced data
	
	x = N.asarray(sorted(N.random.uniform(x_data.min(), x_data.max(),length)))
	y = artificial_data(x)
	N.savetxt('test/data_unevenly_spaced.dat', N.asarray([x,y]).T)
	options.infilename = 'test/data_unevenly_spaced.dat'
	data = N.loadtxt(options.infilename)
	ofac = options.ofac
	hifac = options.hifac
	print "Over-sampling factor: %i"%ofac
	print "Highest frequency (in nyquist freq.): %.2f\n"%hifac
	x = data[:,0]
	y = data[:,2]

#	Normal FFT with unevely spaced data
	fty = FT.rfft(y)
	#ftx = FT.fftshift(FT.fftfreq(len(y),1.0))
	ftx = FT.fftfreq(len(x_data),dwell)[:len(fty)]
	ft = N.empty((len(fty),2))
	ft[:,1] = N.abs(fty)/N.abs(fty).max()
	ft[:,0] = ftx
	N.savetxt('test/FFT_unevenly_spaced.dat', ft)

	

if not options.debug:
	print "Reading data from '%s'..."%(options.infilename),
	try:
		data = N.loadtxt(options.infilename, delimiter=',')
		print "done"
	except IOError:
		raise IOError, "Inout file not found: %s"%(options.infilename)
	except ValueError:
		raise ValueError, "Malformed data in input file: %s"%(options.infilename)
	
	ofac = options.ofac
	hifac = options.hifac
	print "Over-sampling factor: %i"%ofac
	print "Highest frequency (in nyquist freq.): %.2f\n"%hifac
	x = data[:,0]
	y = data[:,2]

# number of different frequencies nout
nout = int(ofac*hifac*len(x)/2.0)

xdif = x.max()-x.min()

periodogram = N.empty((nout,2))
periodogram[:,0] = N.arange(nout)+1.0
periodogram[:,0] /= (ofac*xdif)

yvar = y.var()
ycorr = (y-y.mean())
evec = N.ones(len(x))

# Main loop over the frequencies to be evaluated
for i,freq in enumerate(periodogram[:,0]):
	periodogram[i,1]=ampfreq(freq)

# evaluate the statistical significance of the maximum
M = 2*nout/ofac
z = periodogram[:,1].max()
prob = N.exp(-z)*M
print 1-prob
if prob > 0.01:
	prob=1.0-(1.0-N.exp(-z))**M

for sig in [0.9, 0.5,0.1,0.05,0.01,0.005,0.001]:
	az = getz(M,sig)
	peaks, peak_positions = getpeak(az, periodogram)
	s = "".join(["\t\tPeak %i: %.3f\n"%(i,p) for i,p in enumerate(peak_positions)])
	print "%.3f significance level at %5.3f with  %2i peak(s)\n at:\n%s"%(1-sig, az/z, peaks, s)

print "Significance for highest peak: %f"%prob
	
# save the periodogram
if not options.outfilename:
	out = options.infilename.split('.')[0]
	out += ".lomb"
	print "Ouput file not given, using: %s"%out

else:
	out = options.outfilename
print "Writing data to '%s' ..."%(out),
# Normalize
periodogram[:,1] /= periodogram[:,1].max()
N.savetxt(out, periodogram)
print "done!\n"
