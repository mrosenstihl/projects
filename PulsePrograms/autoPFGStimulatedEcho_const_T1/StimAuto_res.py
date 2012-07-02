import math
import scipy.signal
import numpy
import os

from numpy import vstack, hstack, eye, ones, zeros, linalg, \
newaxis, r_, flipud, convolve, matrix, array
from scipy.signal import butter,lfilter

def lfilter_zi(b,a):
    #compute the zi state from the filter parameters. see [Gust96].

    #Based on:
    # [Gust96] Fredrik Gustafsson, Determining the initial states in forward-backward 
    # filtering, IEEE Transactions on Signal Processing, pp. 988--992, April 1996, 
    # Volume 44, Issue 4

    n=max(len(a),len(b))

    zin = (  eye(n-1) - hstack( (-a[1:n,newaxis],
                                 vstack((eye(n-2), zeros(n-2))))))

    zid=  b[1:n] - a[1:n]*b[0]

    zi_matrix=linalg.inv(zin)*(matrix(zid).transpose())
    zi_return=[]

    #convert the result into a regular array (not a matrix)
    for i in range(len(zi_matrix)):
      zi_return.append(float(zi_matrix[i][0]))

    return array(zi_return)




def filtfilt(b,a,x):
    #For now only accepting 1d arrays
    ntaps=max(len(a),len(b))
    edge=ntaps*3

    if x.ndim != 1:
        raise ValueError, "Filiflit is only accepting 1 dimension arrays."

    #x must be bigger than edge
    if x.size < edge:
        raise ValueError, "Input vector needs to be bigger than 3 * max(len(a),len(b)."

    if len(a) < ntaps:
        a=r_[a,zeros(len(b)-len(a))]

    if len(b) < ntaps:
        b=r_[b,zeros(len(a)-len(b))]

    zi=lfilter_zi(b,a)

    #Grow the signal to have edges for stabilizing 
    #the filter with inverted replicas of the signal
    s=r_[2*x[0]-x[edge:1:-1],x,2*x[-1]-x[-1:-edge:-1]]
    #in the case of one go we only need one of the extrems 
    # both are needed for filtfilt

    (y,zf)=lfilter(b,a,s,-1,zi*s[0])

    (y,zf)=lfilter(b,a,flipud(y),-1,zi*y[-1])

    return flipud(y[edge-1:-edge+1])



    


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
    
    start = 0.5e-3-0.2e-3          # part used for amplitude averaging   
    end   = 0.5e-3+0.2e-3          #
    #-----------------------------------------------------------------------------
    

    tau_curves = {}
    tau_curves_sqrt = {}
    tau_curves_log_sqrt = {}
    tau_curves_log = {}
    order = 3
    freq = 10e3
    sqrt = MeasurementResult("AmplitudeSQRT")
    
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        
        #data["Timesignal"]=timesignal+0        
        
        [b,a]=butter(order,freq/timesignal.get_sampling_rate())
        
        run = int(timesignal.get_description("run"))+1
        accumulations = int(timesignal.get_description("accumulations"))

        tm = float(timesignal.get_description("tm"))
        tau = float(timesignal.get_description("tau"))
        delta = float(timesignal.get_description("delta"))
        gradient = float(timesignal.get_description("gradient"))
        dac = int(timesignal.get_description("dac"))
        t_bvt = str(timesignal.get_description('T_BVT'))
        t_eur = str(timesignal.get_description('T_EURO'))
        #open(os.path.join(t_bvt,t_eur),'w').close()
        try:
            os.mkdir(t_bvt)
            open(os.path.join(t_bvt,t_eur),'w').close()	
            print "Created infofile %s"%t_eur
            
        except:
            #print "No directory created"
            pass
        
        filtered = timesignal+0
        filtered.y[0]=filtfilt(b,a,timesignal.y[0])
        filtered.y[1]=filtfilt(b,a,timesignal.y[1])
        data["Filtered"]=filtered
        #print run,accumulations
        if run <= accumulations:
            if run == 1:
                #print "Object"
                accu = Accumulation(error=True)
                accuf = Accumulation(error=True)
            if (((run-1)%2)==0):
                accu += timesignal
                accuf += filtered
            elif (((run-1)%2)==1):
                accu -= timesignal
                accuf -= filtered
            data["TS"] = timesignal
            data["Current accumulation"]=accu
            data["Current accumulation filtered"]=accuf
            
            if run == accumulations:
                r_start=max(0,int((start-timesignal.x[0])*timesignal.get_sampling_rate()))
                r_end=min(int((end-timesignal.x[0])*timesignal.get_sampling_rate()), len(timesignal))
        
                out = accuf.y[0][r_start:r_end].mean()/(run) - numpy.mean(accuf.y[0][-4096:])/run
                out_err=numpy.std(accuf.y[0][-1024:])/numpy.sqrt(r_end-r_start)
                
                
                sqrt = (numpy.sqrt(accuf.y[0][r_start:r_end]**2 + accuf.y[1][r_start:r_end]**2).mean() - numpy.sqrt(accuf.y[0][-4096:]**2 + accuf.y[1][-4096:]**2).mean())/run
#                magnetization=get_mean(accu, start, end)
#                sqrt = math.sqrt(magnetization[0]**2+magnetization[1]**2)
                
                if not tau_curves.has_key(tau):
                    tau_curves [tau] = {}
                    tau_curves_sqrt [tau] = {}
                #    tau_curves_log_sqrt [tau] = {}
                 #   tau_curves_log [tau] = {}
                    
                if not (tau_curves [tau]).has_key(tm):
                    tau_curves [tau] [tm]      = MeasurementResult("Real")
                    tau_curves_sqrt [tau] [tm] = MeasurementResult("Amplitude")
                    #tau_curves_log_sqrt [tau] [tm] = MeasurementResult("Amplitudelog")
                    #tau_curves_log [tau] [tm] = MeasurementResult("RealLog")
                    
                tau_curves [tau] [tm] [dac] = AccumulatedValue(out, out_err, run)
                tau_curves_sqrt [tau] [tm] [dac] = sqrt
                
                #tau_curves_log_sqrt [tau] [tm] [dac] = sqrt
                
                #tau_curves_log [tau] [tm] [dac] =  AccumulatedValue(out, out_err, run)
                
                data[("%s/Real_%.2fms_%.2fms"%(t_bvt, tau*1e3,tm*1e3)).replace('.','p')] = tau_curves[tau][tm]
                data[("%s/Amplitude_%.2fms_%.2fms"%(t_bvt, tau*1e3,tm*1e3)).replace('.','p')] = tau_curves_sqrt[tau][tm]
                #data["Real_Logx %.2e %.2e"%(tau,tm)] = tau_curves_log[tau][tm]
                #data["Amplitude_Logx %.2e %.2e"%(tau,tm)] = tau_curves_log_sqrt[tau][tm]
                (tau_curves_sqrt[tau][tm]).write_to_csv('%s/Amplitude_tau_%.2fms_tm_%.2fms_delta_%.2fms'%(t_bvt, tau/1e-3, tm/1e-3,delta/1e-3))
                (tau_curves[tau][tm]).write_to_csv('%s/Real_tau_%.2fms_tm_%.2fms_delta_%.2fms'%(t_bvt, tau/1e-3, tm/1e-3,delta/1e-3))
                data["%s/Accumulations_tau=%.2fms/t=%.2fms/grad=%i_delta=%.2fms"%(t_bvt, tau*1e3,tm*1e3,dac,delta*1e3)]=accu
    pass