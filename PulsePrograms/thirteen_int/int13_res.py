import os, time
import tables
import numpy as N

class ParameterSet:
    """
    From 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308
    Alex Martelli
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def cyclops(timesignal, r_phase, accumulation_object):
    """
    This is CYCLOPS phase cycling.
    Receiver phase must advance with each step by 90°.
    Real channel and Imaginary channel get subtracted/added to the Real/Imag channel
    of the current accumulation.
    """
    if r_phase%4 == 0:# in [0,4,8,12]
        ts = timesignal+0
        ts.y[0] = timesignal.y[0]
        ts.y[1] = timesignal.y[1]
        accumulation_object += ts

    if (r_phase-1)%4 == 0:#[1,5,9,13]:
        ts = timesignal+0
        ts.y[0] = -1*timesignal.y[1]
        ts.y[1] = timesignal.y[0]
        accumulation_object += ts

    if (r_phase-2)%4 == 0:#[2,6,10,14]
        ts = timesignal+0
        ts.y[0] = -1*timesignal.y[0]
        ts.y[1] = -1*timesignal.y[1]
        accumulation_object += ts

    if (r_phase-3)%4 == 0: #in [3,7,11,15]:
        ts = timesignal+0
        ts.y[0] = timesignal.y[1]
        ts.y[1] = -1*timesignal.y[0]
        accumulation_object += ts

def exorcycle(ts, pi_phase):
    """
    EXORCYCLE:
    pi pulse in a Hahn Echo experiment advances with 90°.
    x,-x add to the signal, y,-y get subtracted.
    Use this function BEFORE cyclops!
    Modifications are in-place.
    """
    if pi_phase%2==0:
        pass
    if (pi_phase-1)%2==0:
        ts.y[0] *= -1
        ts.y[1] *= -1
    
def b(G,tmix,delta1,delta,delta2):
    b_value = G**2*delta**2*(tmix +3./2*(delta1+delta2) +(4./3+5./(8*N.pi**2))*delta)
    return b_value
        
def result_hahn_pfg():
    start=0.4e-3
    stop=0.44e-3
    tau_dict={}
    tau_log_dict = {}
    amp = MeasurementResult('Amplitude vs. Gradientenstärke')
    #sample = "ME_charge2_sample3/MEc2_p3"
    #date = time.strftime("%d%m%y")
    #filename = "%s_%s"%(sample,date)
    i=1
    #file = filename+""
    #while True:
    #    if os.path.exists(file):
    #        file = "%s_%i.h5"%(filename,i)
    #        i += 1
    #    else:
    #       break
    #print "\n\nUsing following filename: \n\t\t\t%s\n\n"%file
    #hdf = tables.openFile(file, 'w')
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            print "No result: ",timesignal
            continue
        descriptions = timesignal.get_description_dictionary()
        # rebuild the dictionary because __init__ can't take unicode keys
        temp_description={}
        for key in descriptions:
            temp_description[str(key)] = descriptions[key]
        descriptions=temp_description
        desc = ParameterSet(**descriptions)
        
        if int(desc.akku) == 0:
            akku = Accumulation(error=True)
            
        mag_singleshot = timesignal +0
        
        cyclops(timesignal, int(desc.rec_phase), akku)
        #akku += timesignal
        
        dac_value = int(desc.dac)
        tau  = float(desc.tau)
        sr = timesignal.get_sampling_rate()
        if int(desc.akku) == int(desc.no_akku)-1:
            if dac_value >= 0:
                group_name = "dac_"+str(dac_value)
            else:
                group_name = "dac_neg_"+str(-dac_value)

            if not tau_dict.has_key(tau):
                tau_dict[tau] = MeasurementResult('Amplitude vs. Gradientenstaerke')
                tau_log_dict[tau] = MeasurementResult('logAmplitude vs. Gradientenstaerke')
            gamma  = 2.67522e8
            # set either on 1
            D = 1
            g_conv = 6.36e-5#7.12e-5
            delta = float(desc.delta)
            delta1 = (float(desc.tau)-delta)/2
            tmix = float(desc.tmix)
            
            st = int(start*sr)
            end = int(stop*sr)
            attn = b(G=g_conv*dac_value, tmix=tmix, delta1=delta1, delta=delta, delta2=delta1)
            
            # Status data
            print "Accumulation done (%s): \n  dac\ttmix\tdelta\ttau\n"%(time.asctime()),"  ", dac_value,tmix,delta,tau,'\n'
            tau_dict[tau][attn] =((akku.y[0]**2+akku.y[1]**2)**0.5)[st:end].mean()-((akku.y[0]**2+akku.y[1]**2)**0.5)[-2048:].mean()
            tau_log_dict[tau][attn] =N.log(((akku.y[0]**2+akku.y[1]**2)**0.5)[st:end].mean()-((akku.y[0]**2+akku.y[1]**2)**0.5)[-2048:].mean())
            print "  Temperatures"
            print "  ".join(open('/home/markusro/Desktop/eurotherm_data.dat').readlines()[-1000::250]),'\n'*2
            for k in tau_dict.keys():
                data["Ergebnis_%.2e"%k] = tau_dict[k]
                data["logErgebnis_%.2e"%k] = tau_log_dict[k]
            #hdf.flush()
        #ft = FFT(akku).fft()
        #data["FT"]=ft
        mag = akku +0
        mag.y[0] = (akku.y[0]**2+akku.y[1]**2)**0.5
        mag.y[1] *= 0
        tmix = float(desc.tmix)
        data["MagnitudeAkku %i/mix%.2e/tau%.2e"%(dac_value,tmix,tau)]=mag
        data["Akku %i/mix%.2e/tau%.2e"%(dac_value,tmix,tau)]=akku
        #mag_singleshot.y[0] = (timesignal.y[0]**2+timesignal.y[1]**2)**0.5
        #mag_singleshot.y[1]  *= 0
        #data["Mag %i %.2e %i"%(dac_value,tau,int(desc.akku))]=mag_singleshot
        # rauschen der letzten ms des signals
        start_noise = -int(1e-3*sr)
        #print "Rauschen",timesignal.y[0][start_noise:].std()
        #print "Level",timesignal.y[0][start_noise:].mean()

        data["TS"]=timesignal
    #hdf.close()
    pass

result=result_hahn_pfg