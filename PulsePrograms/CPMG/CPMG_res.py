import math
import scipy.signal
import numpy as N


def result():
    accu = Accumulation()
    cpmg =  MeasurementResult("CPMG")
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            continue
        #data["Timesignal"]=timesignal+0
        
        run = int(timesignal.get_description("run"))
        tau = float(timesignal.get_description("tau"))
        no_echoes = int(timesignal.get_description("no_echoes"))
        pulse180 = float(timesignal.get_description("pulse180"))
        
        
        if (((run)%2)==0):
            accu += timesignal
            for i in xrange(no_echoes):
                tmp_Res = timesignal.get_result_by_index(i)                    
                cpmg[(2*tau+pulse180)*(i+1)] += tmp_Res.y[0].mean()
        elif (((run)%2)==1):
            accu -= timesignal
            for i in xrange(no_echoes):
                tmp_Res = timesignal.get_result_by_index(i)
                cpmg[(2*tau+pulse180)*(i+1)] += -tmp_Res.y[0].mean()
        data["cpmg"]=cpmg
 
        
        #data["Accumulation"]=accu
        #for i in xrange(no_echoes):
            #tmp_Res = accu.get_accu_by_index(i)
            ##print tmp_Res
            #cpmg[(2*tau+pulse180)*(i+1)] += tmp_Res.y[0].mean()
        #data["cpmg"]=cpmg
        #print len(cpmg)
        if ((run%4)==1):
            nmr_file = open('rm_CPMG_%.2e.dat'%tau,'w')                    # <-
            cpmg.write_to_csv(nmr_file)                        # <-
            nmr_file.close()                                   # <-
            
    pass