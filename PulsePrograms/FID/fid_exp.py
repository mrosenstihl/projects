def fid_experiment(run,sens):
    e=Experiment()
    e.set_pfg(dac_value=0,is_seq=1)
    
    e.set_description("run",run)
    e.set_description("sens",sens)
    
    phase = -40-90              # receiver phase
    
    pulse = 1.6e-6           # (s) 90° pulse length
    
                           # (s) delay between sequences >5*T1 
    

    # ---------------------------------------------------------------------
    dead_time = 2e-6  # (s)   
    # ---------------------------------------------------------------------
    
    
    # t_rep
    e.wait(1e-3)
    # sat rec, leaving gate on
    for t_sat in N.logspace(N.log10(2e-6),N.log(1e-3),18)[::-1]:
        e.ttl_pulse(length=t_sat, value=1)              # gate high-power ampli on
    #    print t_sat
        e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    
    if pulse>10e-6:
        raise Exception("--- Pulse too long!!! ---")
    # ---------------------------------------------------------------------  
    td = 1
    e.set_phase(0)    
    e.wait(td-0.5e-6)    

    # measuring pulse ----------------------------------------------------------------
    e.ttl_pulse(length=5e-6, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    # ---------------------------------------------------------------------    
  

    e.set_phase(phase+[0,90,180,270][run%4])         # receiver phase cycling
    #e.wait(dead_time-0.5e-6)                                        # dead time

    e.record(samples=1024*64, frequency=20e6, sensitivity=sens)     # acquisition command
    
    return e
    

def experiment():
    accumulations=4*100
    for sens in [10]:                          # number of repetitions
        for run in xrange(accumulations):
            #run = 0
            yield fid_experiment(run,sens)