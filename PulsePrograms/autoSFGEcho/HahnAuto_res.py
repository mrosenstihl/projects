import math
import scipy.signal
import numpy

def result():
    
    start = 0.5e-3 - 10e-5        # part used for amplitude calculation   
    end  = 0.5e-3 + 10e-5        #
    # ------------------------------------------------------------------------------
    
    

    tauold=None
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))+1
        accumulations = int(timesignal.get_description("accumulations"))
        gradient = float(timesignal.get_description("gradient"))
        dac = int(timesignal.get_description("dac"))
        delta = float(timesignal.get_description("delta"))
        tau = float(timesignal.get_description("tau"))
        if tauold != tau:
            print "new result"
            mag = MeasurementResult("Amplitude %.1e" % tau)
            tauold = tau
        print timesignal.get_description_dictionary()
        if run <= accumulations:
            if run == 1:
                accu = Accumulation(error=True)
            if (((run-1)%2)==0):
                accu += timesignal
            elif (((run-1)%2)==1):
                accu -= timesignal
            if run == accumulations:
                r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
                r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
                
                out = numpy.sqrt((accu.y[0]**2+accu.y[1]**2))[r_start:r_end].mean()
                out = accu.magnitude().y[0][r_start:r_end].mean() - accu.magnitude().y[0][-128:].mean()
                
                out_err=numpy.sqrt((accu.get_yerr(0)[r_start:r_end]**2).sum())/numpy.sqrt(r_end-r_start)
        
                #mag[tau] = out
                mag[dac]=AccumulatedValue(out, out_err, run)
                mag.write_to_csv("Amplitude_%.0fe-3_delta_%.1fms.dat" %(tau/1e-3, delta/1e-3))
                data["Amplitude %.2e" %tau] = mag
                data["Hahn-Echo %.2e %i"%(tau,dac)]=accu
    pass