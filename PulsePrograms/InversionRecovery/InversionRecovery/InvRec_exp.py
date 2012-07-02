def InvRec_experiment(run):
    e=Experiment()
    e.set_description("run",run)
    
    tau=24e-3                          # (s) time delay between pulses > 100e-6
        
    pulse90    = 1.78e-6                # (s) pulse length
    
    pulse180  = 3.62e-6           # (s) pulse length
    
    td = 2                               # (s) delay between sequences 
    
    phase = 133+195               # receiver phase
    
    # -------------------------------------------------------------------
    dead_time = 15e-6  # (s)       
    # ---------------------------------------------------------------------
    
    if pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")  
    if tau <0.1e-3:
        raise Exception("--- Inv. Rec. time shorter than gate time!!! ---")
            
    # ---------------------------------------------------------------------
    e.wait(1e-3)    
    e.set_phase([0.0, 0.0,180,180][run%4])	    # phase cycle to remove fid from first pulse    
    e.wait(td-0.5e-6)    

    # Inversion Recovery --------------------------------------------
    e.ttl_pulse(length=100e-6, value=1)                # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)        # RF pulse     
    e.set_phase(90)                                              
                                                                                    
    e.wait(tau-0.5e-6-100e-6) 
    e.ttl_pulse(length=100e-6, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse90, value=1+2)         # RF pulse 
      
    # ---------------------------------------------------------------------
    
    e.set_phase(phase+[90,270][run%2])         # receiver phase cycling
    e.wait(dead_time-0.5e-6)                               # dead time

    e.record(samples=4*4096, frequency=2e7, sensitivity=10)          # acquisition command
    
    return e
    

def experiment():
    accumulations=4*1                          # number of repetitions              
    
    for run in xrange(accumulations):
        yield InvRec_experiment(run)
        pass