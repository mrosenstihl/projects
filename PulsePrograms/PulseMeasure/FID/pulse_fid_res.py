import math
import scipy.signal
import numpy

def get_mean(timesignal, start, end):
    r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
    r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))

    channels=len(timesignal.y)
    means=[0.0,]*channels
    if r_start<r_end:
        for i in xrange(channels):
            signal_part=timesignal.get_ydata(i)[r_start:r_end]
            means[i]=signal_part.mean()
    return means

def result():
    
    mag = MeasurementResult("Real")
    sqrt = MeasurementResult("Amplitude")    
    
    start = 10e-6
    end  = 60e-6
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        # data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))
        rec = int(timesignal.get_description("rec"))

        accumulations = int(timesignal.get_description("accumulations"))

        pulse = float(timesignal.get_description("pulse"))
        if run==0: accu=Accumulation(error=False)
        if rec == 0:
            tmp = timesignal +0 
        elif rec == 3:
            tmp = timesignal+0
            tmp.y = [timesignal.y[1], -timesignal.y[0]]
        elif rec == 2:
            tmp = timesignal+0
            tmp.y = [-timesignal.y[0], -timesignal.y[1]]
        elif rec == 1:
            tmp = timesignal+0
            tmp.y = [-timesignal.y[1], timesignal.y[0]]
        accu += tmp

        sr = timesignal.get_sampling_rate()
        r_start=int(start*sr)
        r_end=min(int(end*sr), len(timesignal))
        r_start,r_end = sorted([r_start,r_end])
        magnetization=get_mean(accu, start, end)
        sqrt[pulse]=math.sqrt(magnetization[0]**2+magnetization[1]**2)
            
        data["Amplitude"]=sqrt
        
        out = accu.y[0][r_start:r_end].mean()
        out_err= accu.y[0][-1024:].std() #numpy.sqrt((accu.get_yerr(0)[r_start:r_end]**2).sum())/numpy.sqrt(r_end-r_start)/run
        
        mag[pulse]=AccumulatedValue(out, out_err/numpy.sqrt((r_end-r_start)), 1)
        data["Real"] = mag
            
        data["accumulations_%e"%(pulse)]=accu
   
    pass