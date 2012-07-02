import math
import scipy.signal
import numpy
from scipy.optimize import leastsq
import numpy as N

def lorenz(x,gamma,offs):
    return gamma/(numpy.pi*((x-offs)**2+gamma**2))
    
def gauss(x,sigma,offs):
    return 1/(sigma*numpy.sqrt(2*numpy.pi))*numpy.exp(-0.5*((x-offs)/sigma)**2)
    
def voigt(p,x):
    return numpy.convolve(gauss(x,p[0],p[2]),lorenz(x,p[1],p[2]),'same')
    
def result():
    accu = Accumulation()
    mag = MeasurementResult("Amplitude")
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print timesignal
            continue
            
        
        
        start = 25e-6     # interval used for FFT
        end  = 1             #
        
        run = int(timesignal.get_description("run"))
        sens = timesignal.get_description("sens")
        
        data["Timesignal %s"%sens]=timesignal+0
        if (((run)%4)==0):
            accu += timesignal
            data["Adjustsignal"]=timesignal
            #data["Adjustspectrum"]=FFT(timesignal).base_corr(0.1).fft(zoom=(0,100e3))
            #data["Adjustspectrumwide"]=FFT(timesignal).base_corr(0.1).fft()
        elif (((run)%4)==1):
            timesignal.y[1]*=-1
            timesignal.y=[timesignal.y[1],timesignal.y[0]] 
            accu += timesignal
            data["Adjustsignal"]=timesignal
            #data["Adjustspectrum"]=FFT(timesignal).base_corr(0.1).fft(zoom=(0,100e3))
            #data["Adjustspectrumwide"]=FFT(timesignal).base_corr(0.1).fft()
        elif (((run)%4)==2):
            accu -= timesignal
            data["Adjustsignal"]=-timesignal
            #data["Adjustspectrum"]=FFT(-timesignal).base_corr(0.1).fft(zoom=(0,100e3))
            #data["Adjustspectrumwide"]=FFT(-timesignal).base_corr(0.1).fft()
        elif (((run)%4)==3):
            timesignal.y[0]*=-1
            timesignal.y=[timesignal.y[1],timesignal.y[0]]
            accu += timesignal
            data["Adjustsignal"]=timesignal
            #data["Adjustspectrum"]=FFT(timesignal).base_corr(0.1).fft(zoom=(0,100e3))
            #data["Adjustspectrumwide"]=FFT(timesignal).base_corr(0.1).fft()
                          
        #r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
        #r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
                
        data["Accumulation %s"%sens]=accu
                
        echo = accu + 0
        #echo.y[0] = accu.y[0][r_start:r_end]
        #echo.y[1] = accu.y[1][r_start:r_end]       
        
        
        if (run+1) % 4 == 0:
            pass
            specmag = (accu+0).fft().magnitude()
            #success=0
            #p0 = [100.,100.,specmag.x[specmag.y[0].argmax()]]
            #p1, success = leastsq(lambda p,x: specmag.y[0]/specmag.y[0].max() - voigt(p,x)/voigt(p,x).max(), p0, specmag.x, maxfev=1200, warning=True)
            #numpy.savetxt( 'testy', voigt(p0,specmag.x)/voigt(p0,specmag.x).max() ) 
            #numpy.savetxt( 'testx', specmag.x ) 
            #pylab.show()
            #if success >= 0:
            #    p0 = p1
            #    err = lambda p,x: specmag.y[0]/specmag.y[0].max() - voigt(p,x)/voigt(p,x).max()
            #    specmag.y[1][:] = voigt(p1,specmag.x)/voigt(p1,specmag.x).max()*specmag.y[0].max()
            #    print p1,success, sum((err(p1, specmag.x))**2)
            data["AbsSpectrum %s"%sens]=specmag+0
            data["Spectrum"]=(accu+0).fft().clip(-2e3,2e3)+0
            noise = N.sqrt(accu.y[0][-256*1024:]**2 + accu.y[1][-256*1024:]**2).std()
            signal = N.sqrt(accu.y[0]**2 + accu.y[1]**2).max()
            print "Rauschen", noise
            print "Signal", signal, signal/noise
            print 
            
            accu = Accumulation()
                                        
    pass