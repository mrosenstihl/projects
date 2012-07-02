import xml.etree.ElementTree as ET
import time

def get_time(experiment):
    tree = ET.fromstring(experiment.write_xml_string()) # create XML tree representation
    time = 0
    for state in tree.getiterator(tag='state'):
        time += float(state.get('time'))
    return time

def Hahn_exp(pulse90,pulse180,td, tau, run, accumulations):
    e=Experiment()    
    e.set_description("tau",tau)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    

    
    rec_phase = 63                          # receiver phase
    gate = 10e-6

    
    # --------------------------------------------------------------------------------
    if pulse90 > 10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180 > 10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")
    if tau < gate:
        raise Exception("--- Echo time shorter than gate time!!! ---")
    # ---------------------------------------------------------------------
    
    e.wait(1e-3)
    phase90 = [0,180,90,270][(run/2)%4]
    phase180 = [90,270,90,270,0,180,0,180][run%8]
    
    e.set_phase(phase90)
    e.wait(td-0.5e-6)
    
    # Hahn-echo ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)            # RF pulse 
    
    e.set_phase(phase180)        # phase cycle to remove fid from first & last pulse 
                                                                                               
    e.wait(tau-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)          # RF pulse            
    # ---------------------------------------------------------------------    
    
    e.set_phase(rec_phase)    # receiver phase 

    e.wait(tau-0.5e-6-5e-6)                                           # dead time included

    e.record(samples=8*1024, frequency=10e6, sensitivity=10)
    return e

    
def experiment():
    pulse90    = 1.4e-6                # (s) pulse length    
    pulse180  = 2.8e-6               # (s) pulse length
    startpoint           = 30e-6 #  first used echo delay
    endpoint            = 10e-3 #8ms  # last used echo delay
    points                = 24        # number of echo delays
    accumulations      = 8*4    # number of repetitions (for a given echo delay), multiples of 8
    td        = 0.21*5                               # (s) delay between sequences > 5*T1

    T_set = 285.0
    T_sample = 273.0
    sample = "dCPC-bk2"
    
    mtime = 0
    # estimate experiment time
    for Hahn_delay in log_range(start=startpoint, stop=endpoint, stepno=points):
        run = 0 
        ep = Hahn_exp(pulse90,pulse180,td,tau=Hahn_delay,run=run,accumulations=accumulations)
        ep.set_description('T_set',T_set)
        ep.set_description('T_sample',T_sample)
        ep.set_description('sample',sample)
        mtime += get_time(ep)*accumulations
    print "* \n* Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    # start real experiment
    for Hahn_delay in log_range(start=startpoint, stop=endpoint, stepno=points):
        for run in xrange(accumulations): 
            ep = Hahn_exp(pulse90,pulse180,td,tau=Hahn_delay,run=run,accumulations=accumulations)
            ep.set_description('T_set',T_set)
            ep.set_description('T_sample',T_sample)
            ep.set_description('sample',sample)
            yield ep
            pass