import math
import scipy.signal
import numpy


def result():
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            continue
        run 	= int(timesignal.get_description("run"))
        tp 	= float(timesignal.get_description("tp"))
        tm 	= float(timesignal.get_description("tm"))
        pulse 	= float(timesignal.get_description("pulse"))
        phase 	= float(timesignal.get_description("phase"))
        td 	= float(timesignal.get_description("td"))
        rec     = int(timesignal.get_description("rec"))
        dead	= float(timesignal.get_description("dead"))
        
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
        ste_name = "ReSTE(tp=%.2g)"%tp
        if ste_name not in data.keys():
            ste = MeasurementResult(ste_name)
        data["STE(tp=%.2g)/STE(tm=%.2g)"%(tp,tm)]=accu
        sr = timesignal.get_sampling_rate()
        start = tp-dead-10e-6
        end = tp-dead+10e-6
        sig_real = accu.y[0][int(sr*start):int(sr*end)].mean()/accu.n
        sig_std = accu.y[0][-2048:].std()/accu.n/(int(sr*end)-int(sr*start))**0.5
        ste[tm]=AccumulatedValue(sig_real,sig_std)
        
        data[ste_name]=ste
    pass