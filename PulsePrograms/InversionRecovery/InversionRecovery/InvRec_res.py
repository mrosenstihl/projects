import math
import scipy.signal
import numpy

def result():
    accu = Accumulation()
                
    for timesignal in results:
        if not isinstance(timesignal, ADC_Result):
            continue
        #data["Timesignal"]=timesignal+0        
        
        run = int(timesignal.get_description("run"))

        if (((run)%2)==0):
            accu += timesignal
            #data["Adjustsignal"]=timesignal
        elif (((run)%2)==1):
            accu -= timesignal
            #data["Adjustsignal"]=-timesignal

        data["Inv-recovery"]=accu                                  
    pass