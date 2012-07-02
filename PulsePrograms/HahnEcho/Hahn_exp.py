def Hahn_experiment(run):
    e=Experiment()
    e.set_description("run",run)
    
    tau=0.15e-3                   # (s) distance between pulses > 0.1e-3
    
    phase = 315
    
    pulse90    = 8.45e-7           # (s) pulse length
    
    pulse180  = 16.1e-7           # (s) pulse length
    
    td = 1                                 # (s) delay between sequences >5*T1
    gate =  5e-6
    # ---------------------------------------------------------------------
    dead_time = 15e-6  # (s)       
    # ---------------------------------------------------------------------    
    if pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")  
    if tau <gate:
        raise Exception("--- Echo time shorter than gate time!!! ---")
    # ---------------------------------------------------------------------
    e.wait(1e-3)    
    e.set_phase(0)    
    e.wait(td-0.5e-6)    

    # Hahn-Echo ------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)        # RF pulse     
    e.set_phase([90.0,90.0,270,270,180,180,0,0][run%8])      # phase cycle to remove fid from first & last pulse         
                                                                                               
    e.wait(tau-0.5e-6-gate) 
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse180, value=1+2)       # RF pulse 
      
    # ---------------------------------------------------------------------    
  
    e.set_phase(phase+[0,180,0,180,180,0,180,0][run%8])    # receiver phase cycling
    e.wait(dead_time-0.5e-6)                               # dead time
        
    #e.wait(90e-6)
    e.record(samples=16*1024, frequency=0.5e6, sensitivity=2)    # acquisition command
    
    return e
    

def experiment():
    accumulations=8*1             # number of repetitions
    
    for run in xrange(accumulations):
        yield Hahn_experiment(run)
        pass