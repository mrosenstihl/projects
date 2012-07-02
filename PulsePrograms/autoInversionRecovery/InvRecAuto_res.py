import math
import scipy.signal
import numpy




def result():
    
    start = 40e-6             # part used for amplitude averaging   
    end  =  90e-6             #
    # ------------------------------------------------------------------------------
    
    mag        = MeasurementResult("IR_Amplitude")
    maglog   = MeasurementResult("IR_AmplitudeLogx")
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        data["Timesignal"]=timesignal +0       
        
        run = int(timesignal.get_description("run"))
        accumulations = int(timesignal.get_description("accumulations"))

        tau = float(timesignal.get_description("tau"))
        aq = ['x','y','-x','-y'][(run/2)%4]
        if run <= accumulations:
            if run == 0:
                accu = Accumulation(error=True)
            if (aq == 'x'):
                accu += timesignal
            elif (aq == 'y'):
                tmp = timesignal + 0
                tmp.y[0] = -1*timesignal.y[1]
                tmp.y[1] = timesignal.y[0]
                accu += tmp
            elif (aq == '-x'):
                accu -= timesignal
            elif (aq == '-y'):
                tmp = timesignal + 0
                tmp.y[0] = timesignal.y[1]
                tmp.y[1] = -1*timesignal.y[0]
                accu += tmp 

#            if run == accumulations:
            r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
            r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
            
            out = accu.y[0][r_start:r_end].mean()/(run+1)
            out_err=(accu.y[0][-128:]/(run+1)).std()/numpy.sqrt(r_end-r_start)
    
            #mag[tau] = out  
            mag[tau]=AccumulatedValue(out, out_err, run)
            maglog[tau]=out
            data["IR_Real"] = mag
            data["IR_RealLog"] = maglog
            data["Accumulations %e"%(tau)]=accu
    pass