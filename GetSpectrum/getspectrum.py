#!/usr/bin/env python
import numpy as N
import numpy.fft as FT
from optparse import OptionParser
import ConfigParser
from scipy.optimize import brentq,fmin,anneal
from exceptions import IndexError
import tables
import re,os


def write_parameter_file(filename):
    config = ConfigParser.RawConfigParser()
    config.add_section('Spectrum')
    cmd_opt_dict = vars(options)
    for i in cmd_opt_dict:
        config.set('Spectrum', i, cmd_opt_dict[i])
    cfgfile = open(filename,'w')
    config.write(cfgfile)
    cfgfile.close()
    return



typ = re.compile("'.*'")

try:
    import matplotlib.pyplot as P
    pyl = True
except:
    pyl = None

parser = OptionParser(version="%prog 0.5")

parser.add_option("--area", dest="normalize_area",
                  help="Normalize area under the spectrum", 
                  metavar="AREA",
                  action="store_true",
                  default=False)


parser.add_option("-b", "--batch", dest="batch",
                  help="No plots, batch processing", 
                  metavar="BATCH",
                  action="store_true",
                  default=False)

parser.add_option("--baseline",
                  type="int", 
                  dest="baseline", 
                  default=0,
                  metavar="N",
                  help="Apply baseline correction to the last N points")

parser.add_option("-c", "--start",
                  type="int", 
                  dest="start", 
                  default=-1,
                  help="Start point of FFT")



parser.add_option("-e", "--end",
                  type="int", 
                  dest="end", 
                  default=-1,
                  metavar="END",
                  help="Skip points past END")

parser.add_option("-f", "--file", dest="infilename",
                  help="Read data from INFILE, can be HDF5 file", 
                  metavar="INFILE")

parser.add_option("--filter",
                  type="float", 
                  dest="filter", 
                  default=0,
                  help="Low pass filter in nyquist frequency")


parser.add_option("-l", "--lb",
                  type="float", 
                  dest="lb", 
                  default=0,
                  help="Line broadening factor for windowing function")

parser.add_option("-m", "--method", dest="method",
                  help="Phasing method: maxent, maxent2 or simple", 
                  default = "simple",
                  metavar="METHOD")

parser.add_option("--mask", dest="mask",
                  help="Save only spectra from -280e3 to 280e3", 
                  metavar="MASK",
                  action="store_true",
                  default=False)
                  
                  
parser.add_option("--maximum", dest="normalize_maximum",
                  help="Normalize spectrum to maximum value", 
                  metavar="MAXIMUM",
                  action="store_true",
                  default=False)
                  
parser.add_option("-n", "--npoints",
                  type="int", 
                  dest="npoints", 
                  default=0,
                  help="Number of additional points to leave out (can be negative)")


parser.add_option("-o", "--out", dest="outfilename",
                  help="Write data to OUTFILE", 
                  metavar="OUTFILE")

parser.add_option("--write-parameter-file", "--wpf", dest="parameterfilename",
                  help="Write data to PARAMETERFILE", 
                  metavar="PARAMETERFILE")

parser.add_option("-p", "--phase",
                  type="float", 
                  dest="phase", 
                  default=None,
                  help="Phase")

parser.add_option("-r", "--read-parameter-file", dest="pfile",
                  help="Write data to PARAMETERFILE", 
                  metavar="PARAMETERFILE")

                  
parser.add_option("-s", "--swap", dest="swapchannels",
                  help="Swapping real and imaginary part. Usually ch0 is real and ch1 is imag", 
                  action="store_true",
                  default=False)

parser.add_option("--std", dest="standard",
                  help="Do not ask for data set in HDF5 files", 
                  action="store_true",
                  default=False)

                  
parser.add_option("-z", "--zero",
                  type="int", 
                  dest="zero", 
                  default=-1,
                  metavar='NUM',
                  help="Filling with NUM zeroes, if NUM=0 no zero filling, NUM < 0 find points for fast FFT")
                  

                  
(options, args) = parser.parse_args()


if options.pfile:
    config = ConfigParser.RawConfigParser()
    config.read(options.pfile)
    opts_from_file = config.options('Spectrum')
    cmd_opt_dict = vars(options)
    
    exclude_from_override = ['infilename', 'outfilename', 'pfile','parameterfilename','swapchannels','batch']
    
    opts_from_file_dict = {}
    for an_opt in cmd_opt_dict.keys():
        an_opt_val = config.get('Spectrum', an_opt)
        opts_from_file_dict[an_opt]=an_opt_val
    
    for an_opt in cmd_opt_dict.keys():
#       print cmd_opt_dict.keys()
#       print opts_from_file_dict.keys()
        if not an_opt in exclude_from_override:
            print "(INFO) Overriding %s with %s"%(an_opt, opts_from_file_dict[an_opt])
            options.__dict__[an_opt] = opts_from_file_dict[an_opt]
            
            
    
    

print "\n(INFO) Reading in file %s ...\n"%(options.infilename)
attributes = {}
tau = 0
num_max = 0
if tables.isHDF5File(options.infilename):
    h = tables.openFile(options.infilename)
    table_list = [f for f in h.walkGroups(h.root.data_pool) if f._v_children.has_key('accu_data')]
    print "Found following accu_data objects:\n\n"
    for i,tb in enumerate(table_list):
        print "\tNumber:",i, tb
        for key in tb._v_attrs._v_attrnamesuser:
            val = tb._f_getAttr(key)
            print "\t\t",key, '\t',val
            if key.endswith('tau'):
                if float(tb._f_getAttr(key)) > float(tau):
                    #print "*** Was",tau
                    tau = val
                    #print "*** Now",tau

                    num_max = i
        print
    if len(table_list) > 1:
        if  options.standard:
            d=num_max
        else:
            d = raw_input('Which one?: [%i]'%num_max)
    else:
        d = 0
    
    if d == '':
        d = num_max
    else:
        d = int(d)
    
    print "Using Number %i ..."%d
    
    for attribute in table_list[d]._v_attrs._v_attrnamesuser:
        attributes[attribute] = table_list[d]._f_getAttr(attribute)

    timeline = table_list[d].accu_data.read()
    dwell = table_list[d].indices.col('dwelltime')
    x = N.arange(timeline.shape[0])*dwell
    rmean = timeline[:,0]
    if timeline.shape[1] > 2:
        imean = timeline[:,2]
    else:
        imean = timeline[:,1]

else:
    datafile = N.loadtxt(options.infilename)
    
    print "Data array has shape:",datafile.shape
    datasets = int(raw_input("How many datasets are there?: "))
    #num_sets = datafile.shape[0]/datasets 
    if datasets == 1:
        usethis=0
    else:
        usethis = int(raw_input("Which one to use (0 to %i)?: "%(datasets-1)))
    
    num = datafile.shape[0]/datasets 
    s = num*usethis
    e = num*(usethis+1)
    x = datafile[s:e,0]
    
    
    if datafile.shape[1] == 5:
        rmean = datafile[s:e,1]
        rsigma = datafile[s:e,2]
        imean = datafile[s:e,3]
        isignam = datafile[s:e,4]
    else:
        rmean = datafile[s:e,1]
        imean = datafile[s:e,2]
    dwell = x[1]-x[0]
    # not needed anymore
    del datafile


if options.swapchannels:
    temp = rmean[:]
    rmean = imean[:]
    imean = temp[:]
    del temp

# Speed up FFT by estimating a good number of points
def find_good_npoints(n):
    fft_len=1<<int(N.floor(N.log2(n)))
    if fft_len%2==0 and fft_len/2*3<=n:
        fft_len=fft_len/2*3 # 1.50
    if fft_len%512==0 and fft_len/512*729<=n:
        fft_len=fft_len/512*729 # 1.42
    if fft_len%64==0 and fft_len/64*81<=n:
        fft_len=fft_len/64*81 #1.26
    if fft_len%8==0 and fft_len/8*9<=n:
        fft_len=fft_len/8*9 # 1.125
    return fft_len

def filter(data, freq):
    import scipy.signal as S
    b,a = S.butter(7,freq)
    data.real = S.filtfilt(b,a,data.real)
    data.imag = S.filtfilt(b,a,data.imag)
    return data

# Data filtering
data = 1j*N.array(imean)+N.array(rmean)
if float(options.filter)  > 0:
    print "Filtering data ..."
    data = filter(data, options.filter)


extra_points=int(options.npoints)



if int(options.start) >= 0:
    r_start = int(options.start)
else:
    r_start = data.real.argmax()+extra_points

r_end = int(options.end)
print "Skipping %i points of data"%r_start
if r_start > len(data):
    raise IndexError,"More points left out than data points exist!"


usable_data = data[r_start:r_end]
options.start = r_start

if options.baseline > 0:
    usable_data -= data[-int(options.baseline):].mean()

n  = len(usable_data)

if options.zero > 0:
    fft_len=find_good_npoints(len(usable_data)+int(options.zero))
elif options.zero == 0:
    fft_len=len(usable_data)#2**N.int(N.ceil(N.log2(len(usable_data)*16))) 
else:
    fft_len=find_good_npoints(len(usable_data))
    print "Finding good number of points for fast FFT: %i (was %i)"%(fft_len,len(usable_data))

print "Using only %.3f parts of signal"%(1.0/(float(len(usable_data))/fft_len))



def shannon(spectrum):
#   h = N.abs((spectrum.real[:-4]-8*spectrum.real[1:-3]+8*spectrum.real[3:-1]-2*spectrum.real[4:])/(12*dwell))
    # second derivative of real part of spectrum
    h = N.abs(N.diff(spectrum.real,2))
    h = h.compress(h>0)
    h/=h.sum()
    entrop = N.sum(-h*N.log(h))
    return entrop

def penalty(spectrum):
    r = spectrum.real
    r = r.compress(r<0)
    return N.dot(r,r)


def entropy(phi, spectrum, gamma):
    """
    Calculates the entropy of the spectrum (real part).
    p = phase
    gamma should be adjusted such that the penalty and entropy are in the same magnitude
    """
#   x = N.linspace(0,1,len(spectrum))
    Re = spectrum*N.exp(1j*phi)
    en_shannon = shannon(Re)+penalty(Re)*gamma
    return en_shannon

def entropy_order2(phi, spectrum, gamma):
    """
    Calculates the entropy of the spectrum (real part).
    phi = phase1, phase2
    gamma should be adjusted such that the penalty and entropy are in the same magnitude
    """
#   x = N.linspace(0,1,len(spectrum))
    Re = spectrum*N.exp(1j* ( phi[0]  + phi[1]*N.linspace(0,1,len(spectrum))))
    en_shannon = shannon(Re) + penalty(Re)*gamma
    return en_shannon



def trafs_window(data, LW=10):
        n = len(data)
        t = dwell * N.arange(n)
        AT = t.max()
        E = N.exp(-t*N.pi*LW)
        e = N.exp((t-AT)*N.pi*LW)
        apod = E
        apod = (E**2*(E+e)/(E**3+e**3))
        Ep = E[t>=(1/LW)]
        apod[t>=(1/LW)]=Ep
        if not options.batch:
            P.plot(apod)
            P.plot(usable_data.real/usable_data.real.max())
            P.plot(apod*usable_data.real/(apod*usable_data).real.max())
            P.legend()
            P.show()
        return data*apod

def trafr_window(data, LW=10):
        n = len(data)
        t = dwell * N.arange(n)
        AT = t.max()
        E = N.exp(-t*N.pi*LW)
        e = N.exp((t-AT)*N.pi*LW)
        apod = E[:]
        apod[ x<1/LW ] = E**2/(E**3+e**3)
        if not options.batch:
            P.plot(apod)
            P.plot(usable_data.real/usable_data.real.max())
            P.plot(apod*usable_data.real/(apod*usable_data).real.max())
            P.legend()
            P.show()
        return apod*data

def exp_window(data,LW):
        n = len(data)
        t = dwell * N.arange(n)
        apod = N.exp(-t*2*N.pi*LW)
        if not options.batch:
            P.plot(apod)
            P.plot(usable_data.real/usable_data.real.max(), label="Original")
            P.plot(apod*usable_data.real/(apod*usable_data).real.max(), label="Windowed")
            P.legend()
            P.show()
        return apod*data



# The simple approach
def phase(phi, signal_in):
    # signal is a part of the signal (imaginary)
    first_point = (signal_in[0]*N.exp(1j*phi)).imag
    #print first_point
    return first_point
    
def simple_phase(signal_in):
    # using bisect or ridder also possible but brentq is much faster, though
    phi_correction = brentq(phase, -N.pi/2, N.pi/2, args=(signal_in))
    return phi_correction


print "Phase given:",options.phase

if options.method == 'simple' and not options.phase:
    #phi = simple_phase(usable_data)
    phi = simple_phase(usable_data)


elif options.method == 'maxent2' and not options.phase:
    # phasing with entropy
    # starting point
    x0 = [12,-100]
    fastft = FT.fftshift(FT.fft(usable_data, fft_len))

    # Estimating gamma
#   print shannon(fastft),penalty(fastft)
    gamma = shannon(fastft)/penalty(fastft)
    print "Gamma estimmated to %.2e"%gamma
    
    phi = fmin(entropy_order2, x0, args=(fastft,gamma))
    #phi = anneal(entropy, x0, args=(fastft,gamma,dwell), 
  #                         lower = -N.pi/2, 
  #                         upper = N.pi/2,
  #                         learn_rate = 0.9,
 #                          maxiter = 1000,
#                           dwell = 100)[0]

elif options.method == 'maxent' and not options.phase:
    # phasing with entropy
    # starting point
    x0 = simple_phase(usable_data)
    fastft = FT.fftshift(FT.fft(usable_data, fft_len))

    # Estimating gamma
#   print shannon(fastft),penalty(fastft)
    gamma = shannon(fastft)/penalty(fastft)
    print "Gamma estimmated to %.2e"%gamma
    
    phi = fmin(entropy, x0, args=(fastft,gamma))
#   phi = anneal(entropy, x0, args=(fastft,gamma,dwell), 
#                           lower = -N.pi/2, 
#                           upper = N.pi/2,
#                           learn_rate = 0.9,
#                           maxiter = 1000,
#                           dwell = 100)[0]


elif options.phase:
    phi = float(options.phase)*N.pi/180.0

try:    
    x = N.linspace(0,1,len(usable_data))
    # second order phase correction
    usable_data *= N.exp(1j*(phi[0] + x*phi[1]))
except:
    # first order phase correction
    usable_data *= N.exp(1j*phi)
    options.phase = phi

# Turn data by 180 if maximum < 0
if usable_data.real[0] < 0:
    usable_data*=N.exp(1j*N.pi)

print "Phasing data (%s):"%(options.method),(phi/N.pi*180.0)%360.0

# Data windowing
if float(options.lb) > 0:
    print "Windowing data", options.lb
    usable_data = exp_window(usable_data, float(options.lb))


print "FFT data ..."
fastft = FT.fftshift(FT.fft(usable_data, fft_len))
freqs = FT.fftshift(FT.fftfreq(fft_len,dwell))

# baseline correction of the spectrum
print "Baseline correction of the spectrum"
base = N.mean([fastft[-64:].mean(),fastft[:64].mean()])
fastft -= base

if str(options.normalize_maximum) == 'True':
    mask_max = ( -280e3 < freqs ) & ( freqs < 280e3 )
    print "Normalize to maximum intensity"
    fastft /= fastft.real[mask_max].max()

if str(options.normalize_area) == 'True':
    print "Normalize to area"
    fastft /= fastft.real.sum()

mask = N.ones(len(freqs), dtype='int')
if str(options.mask) == 'True':
    print "Spectrum from -280e3 to 280e3 kHz"
    mask = ( -280e3 < freqs ) & ( freqs < 280e3 ) 


if not options.batch:
    print "Trying to plot data ..."
    P.subplot(211)
    x = N.arange(len(usable_data))*dwell/1e-6
    P.plot(x,usable_data.real,'r',label="Real")
    P.plot(x,usable_data.imag,'b',label="Imag")
    P.xlabel('t/us')
    P.ylabel('Signal/a.u.')
    P.legend()
    P.subplot(212)
    if str(options.mask) == 'True':
        P.plot(freqs[mask]/1e3, fastft[mask])
    else:
        P.plot(freqs/1e3, fastft)
    null = (freqs == 0)
    P.plot(freqs[null], fastft[null], 'bo')
    
    P.xlabel('Frequency/kHz')
    P.ylabel('Signal/a.u.')
    #P.xlim(-280,280)
    P.show()


#print "Writing data to %s"%(options.outfilename)

if options.parameterfilename:
    write_parameter_file(options.parameterfilename)
    
if options.outfilename:
    print "Writing spectrum to %s"%(options.outfilename)
    out = open(options.outfilename,'w')
    # anarray[start:stop].sum()
    
    out.write("# FFT spectrum from file %s\n"%(options.infilename))
    
    if len(attributes.keys()) > 0:
        out.write("# %s\n"%(table_list[d]))
        field_length = 0
        for key in attributes.keys():
            if len(key) > field_length: field_length = len(key)
        for key in attributes.keys():
            out.write('# %-*s %-*s\n'%(field_length,key,field_length,attributes[key]))
    out.write('#t real imag\n')
    N.savetxt(out,N.array([freqs[mask],fastft.real[mask],fastft.imag[mask]]).T)
    #for i in xrange(fft_len):
    #   out.write('%e\t%e\t%e\n'%(freqs[i],fastft.real[i],fastft.imag[i]))  
    out.close()
    # save paramter file too
    parfile = os.path.splitext(options.outfilename)[0]+'.par'
    print "Writing parameters to %s"%(parfile)
    write_parameter_file(parfile)
print "done!"


