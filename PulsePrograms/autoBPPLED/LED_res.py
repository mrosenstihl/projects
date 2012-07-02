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
    Receiver phase must advance with each step by 90.
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

def result():
    meas = MeasurementResult('Test')
    for res in results:
        if not isinstance(res, ADC_Result):
            print "ERROR: ", res
            continue
        descriptions = res.get_description_dictionary()
        # rebuild the dictionary because __init__ can't take unicode keys
        temp_description={}
        for key in descriptions:
            temp_description[str(key)] = descriptions[key]
        descriptions=temp_description
        desc = ParameterSet(**descriptions)
        data["Timesignal"]=res
        if int(desc.run)%int(desc.accu_length) == 0:
            accu=Accumulation()
        cyclops(res,int(desc.cyclops),accu)
        me = N.mean(((accu.y[0]**2+accu.y[1]**2)**0.5)[20:100])
        
        meas[int(desc.dac)] = AccumulatedValue(me)
        data['Test']=meas
        data["Accu %.1e/dac_%s"%(float(desc.tmix),desc.dac)]=accu
        data["Accu %.1e/mag_dac_%s"%(float(desc.tmix),desc.dac)]=(accu+0).magnitude()