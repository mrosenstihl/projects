import xml.etree.ElementTree as ET
import time
def get_time(experiment):
    tree = ET.fromstring(experiment.write_xml_string()) # create XML tree representation
    time = 0
    for state in tree.getiterator(tag='state'):
        time += float(state.get('time'))
    return time

def Stim_experiment(run, tp, tm, pulse, phase, td):
    e=Experiment()
    e.set_description("run",run)
    e.set_description("tp",tp)
    e.set_description("tm",tm)
    e.set_description("pulse",pulse)
    e.set_description("phase",phase)
    e.set_description("td",td)
    
    #phase cycling removes all but first and second FID
    ph1=0
    ph2 = [0,180][run%2]
    ph3 = [0,180,180,0][run%4]
    e.set_description('rec',[0,0,2,2][run%4])
    #rec_phase = [0,90,180,270][run%4]
    # ----------------------------------------------------------------------
    dead_time = 15e-6  	# dead time (s)
    e.set_description("dead",dead_time)
    gate = 10e-6        # gate time (s)
    # ---------------------------------------------------------------------
    if pulse>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if tm < gate:
        raise Exception("--- Mixing time shorter than gate time!!! ---")
    if tp < gate:
        raise Exception("--- Evolution time shorter than gate time!!! ---")
    if tp < dead_time:
        raise Exception("--- STE is within receiver dead time ---")
    # ---------------------------------------------------------------------
    e.wait(1e-3)    
    e.set_phase(ph1)    
    e.wait(td-0.5e-6-gate)    

    # Stimulated-Echo ------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)        # RF pulse 1       
    e.set_phase(ph2)                   
    e.wait(tp-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse, value=1+2)         # RF pulse 2 
    e.set_phase(ph3)                    
    e.wait(tm-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse, value=1+2)         # RF pulse 3
    # ---------------------------------------------------------------------    
                         
    e.set_phase(phase)    # receiver phase
    e.wait(dead_time-0.5e-6)  # dead time
    e.record(samples=1024*64, frequency=20e6, sensitivity=10)    # acquisition command
    return e
    

def experiment():
    accumulations = 4*16                # number of repetitions       
    tp            = 1e-3             # (s) evolution time: distance between first two pulses > 0.1e-3
    tm            = 10e-3            # (s) mixing time: distance between last two pulses > 0.1e-3
    phase         = 250              # receiver phase
    pulse         = 1.4e-6           # (s) pulse length
    td            = 0.21*5                # (s) delay between sequences > 5*T1)
    tp_range = [100e-6,200e-6,300e-6]
    tm_range = list(log_range(200e-6,td,24))
    
    # Estimate measuring time
    mtime = 0
    for tp in tp_range:
        for tm in tm_range:
            run = 0
            ep = Stim_experiment(run, tp, tm, pulse, phase, td)
            mtime += get_time(ep)*accumulations
    print "* \n* Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    for tp in tp_range:
        for tm in tm_range:
            for run in xrange(accumulations):
                yield Stim_experiment(run, tp, tm, pulse, phase, td)
            synchronize()
        pass