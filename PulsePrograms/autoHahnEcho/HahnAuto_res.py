import math
import scipy.signal
import numpy

def result():
    
    start = 0e-6        # part used for amplitude calculation   
    end  =  50e-6        #
    # ------------------------------------------------------------------------------
    
    mag        = MeasurementResult("Amplitude")

    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        #data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))
        accumulations = int(timesignal.get_description("accumulations"))
        tau = float(timesignal.get_description("tau"))
        T_set = timesignal.get_description("T_set")
        T_sample = timesignal.get_description("T_sample")
        sample = timesignal.get_description("sample")
        
        data["Timesignal"]=timesignal
        aq = ['x','-x','y','-y'][(run/2)%4]
        if run == 0:
            accu = Accumulation(error=False)
        if (aq == 'x'):
            accu += timesignal
        elif (aq == 'y'):
            tmp = timesignal + 0
            tmp.y = [timesignal.y[1], -timesignal.y[0]]
            accu += tmp
        elif (aq == '-x'):
            tmp = timesignal + 0
            tmp.y = [-timesignal.y[0], -timesignal.y[1]]
            accu += tmp
        elif (aq == '-y'):
            tmp = timesignal + 0
            tmp.y = [-timesignal.y[1], timesignal.y[0]]
            accu += tmp 

        r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
        r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
        
        out = accu.y[0][r_start:r_end].mean()/(run+1)
        out_err=(accu.get_yerr(0)[-1024:]).std()/(run+1)/numpy.sqrt(r_end-r_start)
        

        mag[tau]=AccumulatedValue(out, out_err)

        data["Real"] = mag
                
        data["HE_tp%.2e"%(tau)]=accu
        filename = "HE_%s_%iK_%.1fK.dat"%(sample,int(T_set),T_sample)
        # write data
        mag.write_to_csv(filename)
    pass