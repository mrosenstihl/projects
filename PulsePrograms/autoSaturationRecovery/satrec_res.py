import numpy as N

def result():
    accu = Accumulation()
    magnetization = MeasurementResult("Saturation Recovery T1")
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print timesignal
            continue
        #####################################################
        start = 4e-6     # interval used calculating signal #
        end  = 20e-6                                        #
        #####################################################
        
        run = int(timesignal.get_description("run"))
        rec = int(timesignal.get_description("rec"))
        tm = timesignal.get_description("tm")
        sample = timesignal.get_description("sample")
        T_sample = timesignal.get_description("T_sample")
        T_set = timesignal.get_description("T_set")
        
        data["Timesignal"]=timesignal+0
        if run == 0:
            accu = Accumulation(error=False)
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

 
        data["accumulation_%e"%tm]=accu
        #data["rotated Signal"]=timesignal
        sr = timesignal.get_sampling_rate()
        i_start,i_end = [int(start*sr),int(end*sr)]
        mag = (accu.y[0][i_start:i_end]).mean()/(run+1)
        err = (accu.y[0][-1024:]).std()/N.sqrt(i_end-i_start)/(run+1)
        magnetization[tm] = AccumulatedValue(mag,err)                                
        data["T1"] = magnetization
        filename = "SR_%s_%iK_%.1fK.dat"%(sample,int(T_set),T_sample)
        # write data
        magnetization.write_to_csv(filename)
    pass