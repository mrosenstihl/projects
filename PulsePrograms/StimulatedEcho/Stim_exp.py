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
    accumulations = 4                # number of repetitions       
    tp            = 1e-3             # (s) evolution time: distance between first two pulses > 0.1e-3
    tm            = 10e-3            # (s) mixing time: distance between last two pulses > 0.1e-3
    phase         = 225              # receiver phase
    pulse         = 1.6e-6           # (s) pulse length
    td            = 4                # (s) delay between sequences > 5*T1) 
       
    for run in xrange(accumulations):
        yield Stim_experiment(run, tp, tm, pulse, phase, td)
        pass