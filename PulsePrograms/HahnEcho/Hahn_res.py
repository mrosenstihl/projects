import math
import scipy.signal
import numpy


def result():
    accu = Accumulation()
            
    #start = 0        # start point for the Fourier transform
    #end  = 1              # 

    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            continue
        #data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))

        if (((run)%2)==0):
            accu += timesignal
            #data["Adjustsignal"]=timesignal
        elif (((run)%2)==1):
            accu -= timesignal
            #data["Adjustsignal"]=-timesignal

        data["Hahn-Echo"]=accu 
                         
        #r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
        #r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
        #echo = accu + 0
        #echo.y[0] = accu.y[0][r_start:r_end]
        #echo.y[1] = accu.y[1][r_start:r_end]       
        #spectrum = FFT(echo).fft(zoom=(0,60e3))
        #data["Spectrum"]=spectrum
        #data["Spectrum"]=FFT(echo).fft()        
        #real = spectrum + 0
        #real.y[1]=0*real.y[1]
        #data["K1"] = real                               
    pass