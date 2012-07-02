import numpy as N
import scipy.signal
import numpy

def result():
    T1 = MeasurementResult("Saturation Recovery T1")
    T2        = MeasurementResult("Hahn Echo")
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print timesignal
            continue
	if timesignal.get_description('expname')=='satrec':
            
            dirname = 'satrec'
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

 
            data["%s/accumulation_%e"%(dirname,tm)]=accu
            #data["rotated Signal"]=timesignal
            sr = timesignal.get_sampling_rate()
            i_start,i_end = [int(start*sr),int(end*sr)]
            out = (accu.y[0][i_start:i_end]).mean()/accu.n
            out_err = (accu.y[0][-1024:]).std()/N.sqrt(i_end-i_start)/accu.n
            T1[tm] = AccumulatedValue(out,out_err)                                
            data["T1"] = T1

	if timesignal.get_description('expname')=='hahn':
            dirname = 'hahn'

    
            start = 0e-6        # part used for amplitude calculation   
            end  =  50e-6        #
            # ------------------------------------------------------------------------------
        
            
        
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
            
    
            T2[tau]=AccumulatedValue(out, out_err)
    
            data["T2"] = T2
            data["%s/hahn(tp=%.2g)"%(dirname,tau)]=accu
	if timesignal.get_description('expname')=='ste':
            dirname = 'ste'
	
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
            data["%s/STE(tp=%.2g)/STE(tm=%.2g)"%(dirname,tp,tm)]=accu
            sr = timesignal.get_sampling_rate()
            start = tp-dead-10e-6
            end = tp-dead+10e-6
            sig_real = accu.y[0][int(sr*start):int(sr*end)].mean()/accu.n
            sig_std = accu.y[0][-2048:].std()/accu.n/int(sr*(end-start))**0.5
            ste[tm]=AccumulatedValue(sig_real,sig_std)
            
            data["%s"%(ste_name)]=ste
            pass