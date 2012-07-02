def pulse_exp(pulse, run, accumulations, td):
    e=Experiment()
    e.set_description("pulse",pulse)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    #e.set_frequency(300.03385e6,0)
    phase =40                # receiver phase
                   # (s) delay between sequences >5*T1  
    gate = 10e-6    
    dead_time = 6e-6     # (s)   
    # -------------------------------------------------------------------
    if pulse>10e-6:
        raise Exception("--- Pulse too long!!! ---")
    
    e.wait(1e-3) 
    e.set_phase(0)  
    e.wait(td-0.5e-6-gate)
    
    # pulse ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)             # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)           # RF pulse 
    # ---------------------------------------------------------------------    

    rec = [0,2,1,3][run%4]
    e.set_description("rec",rec)
    rec_ph = 90*rec
    e.set_phase(phase+rec_ph)

    e.wait(dead_time-0.5e-6)                   # dead time

    e.record(samples=8192, frequency=10e6, sensitivity=10)
    
    return e

    
def experiment():
    startpoint              = 0.5e-6         # first used pulse length
    endpoint               = 6e-6         # last used pulse length
    points                   = 20               # number of pulse lengths    
    accumulations      = 4                 # number of repetitions (for a given pulse length) 
    td        = 1

    timepoints = lin_range(startpoint, endpoint, (endpoint-startpoint)/points)
    print timepoints
    for pl in timepoints:  # timepoints
        for run in xrange(accumulations): 
            yield pulse_exp(pulse=pl,
                            run=run,
                            accumulations=accumulations, 
                            td=td)
            pass