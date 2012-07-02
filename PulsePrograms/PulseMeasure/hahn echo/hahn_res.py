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
    
    start = 93e-6              #  interval used to calculate the echo amplitude
    end  = 94e-6               # 
    
    # ----------------------------------------------------------------------------------------------
    
    mag = MeasurementResult("Real")
    sqrt = MeasurementResult("Amplitude")
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        #data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))+1
        accumulations = int(timesignal.get_description("accumulations"))

        pulse = float(timesignal.get_description("pulse"))
        
        if run <= accumulations:
            if run == 1:
                accu = Accumulation(error=True)
            if (((run)%2)==0):
                accu -= timesignal
            elif (((run)%2)==1):
                accu += timesignal

            r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
            r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
            
            magnetization=get_mean(accu, start, end)
            sqrt[pulse]+=math.sqrt(magnetization[0]**2+magnetization[1]**2)
            data["Amplitude"]=sqrt
        
            out = accu.y[0][r_start:r_end].mean()/(run)
            out_err=numpy.sqrt((accu.get_yerr(0)[r_start:r_end]**2).sum())/numpy.sqrt(r_end-r_start)
        
            mag[pulse]=AccumulatedValue(out, out_err, run)
            data["Real"]=mag
            
            data["accumulations %e"%(pulse)]=accu
    pass