import xml.etree.ElementTree as ET
import time
def get_time(experiment):
    tree = ET.fromstring(experiment.write_xml_string()) # create XML tree representation
    time = 0
    for state in tree.getiterator(tag='state'):
        time += float(state.get('time'))
    return time

def fid_experiment(pulse,tm,run,phase):
    e=Experiment()
    #e.set_pfg(dac_value=0,is_seq=1)
    e.set_description("run",run)
    e.set_description("tm",tm)
    
    gate=10e-6

    # ---------------------------------------------------------------------
    dead_time = 6e-6  # (s)   
    # ---------------------------------------------------------------------
    
    # t_rep
    e.wait(1e-3)
    # sat rec, leaving gate on
    for i,t_sat in enumerate(N.logspace(N.log10(1e-6),N.log10(100e-3),32)[::-1]):
        e.ttl_pulse(length=t_sat, value=1)              # gate high-power ampli on
        e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    
    if pulse>10e-6:
        raise Exception("--- Pulse too long!!! ---")
    # ---------------------------------------------------------------------  
    e.set_phase(0)    
    e.wait(tm-0.5e-6-gate)    

    # measuring pulse ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1+4)              # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    # ---------------------------------------------------------------------    
    
    
    e.set_phase(phase+[0,90,180,270][run%4])         # receiver phase cycling
    e.set_description("rec",[0,1,2,3][run%4])
    e.wait(dead_time-0.5e-6)                                        # dead time
    e.record(samples=1024*8, frequency=20e6, sensitivity=10)     # acquisition command
    return e
    

def experiment():

    pi90 = 1.4e-6
    phase=50
    accumulations=4*2
    
    change_accu_delay = 10
    reduced_accus = 4
    
    start = 20e-5
    stop = 10
    points = 24

    T_sample = 295.0
    T_set = 305
    sample = "dCPC-bk2"
    
    delays = staggered_range(log_range(start,stop,points),3)

    # estimate mesuring time
    mtime = 0
    for delay in delays:                          # number of repetitions
        if delay > change_accu_delay:
            accus = reduced_accus
        else:
            accus = accumulations
        run = 0 # do not loop over accus
        ep = fid_experiment(pulse = pi90,
                                tm=delay,
                                run=run,
                                phase=phase)
        ep.set_description('T_sample',T_sample)
        ep.set_description('T_set',T_set)
        ep.set_description('sample',sample)
        mtime += get_time(ep)*accus
    print "* \n* Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    # now do the real measurement
    for delay in delays:                          # number of repetitions
        if delay > change_accu_delay:
            accus = reduced_accus
        else:
            accus = accumulations
        for run in xrange(accus):
            ep = fid_experiment(pulse = pi90,
                                tm=delay,
                                run=run,
                                phase=phase)
            ep.set_description('T_sample',T_sample)
            ep.set_description('T_set',T_set)
            ep.set_description('sample',sample)
            yield ep