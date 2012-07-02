
def fid_experiment(run):
    e=Experiment()

    e.set_description("run",run)
    
    pulse90   = 2.1e-6             # s
    
    pulse180  = 4.2e-6       # s
    
    td        = 1.3*5                 # repetition time

    phase  = 155         #receiver phase
    
    tau        =300e-6           # s CPMG interpulse delay; > 100e-6 
    
    rec_time   = 4e-6            # s <= tau-15e-6
    
    sampl_freq = 20e6
    
    no_echoes  = 4000       # number of echoes 
    
    no_points  = 64              # measured points in the accumulated signal
    
    
    # ---------------------------------------------------------------------
    e.set_description("tau",tau)
    e.set_description("no_echoes", no_echoes+1)
    e.set_description("pulse180",pulse180)
    if pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")  
    if tau <5e-6:
        raise Exception("--- Echo time shorter than gate time!!! ---")
    # ---------------------------------------------------------------------

    e.set_phase(0)
    e.wait(td-5e-6-0.5e-6)
    
    # first pulse  ----------------------------------------------------------------
    e.ttl_pulse(length=5e-6, value=1)            # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)         # RF pulse 
    # -----------------------------------------------------------------------------
    e.set_phase([90, 90, 270, 270][run%4])
    e.wait(tau-5e-6-0.5e-6)                      # e.set_phase introduces 0.5e-6 delay 

    # first 180 pulse and recording -----------------------------------------------
    e.ttl_pulse(length=5e-6, value=1)             # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)       # RF pulse            
            
    e.set_phase(phase+[0,180,0,180][run%4])
    e.wait(tau-0.5e-6-rec_time/2)                   

    e.record(samples=no_points, frequency=sampl_freq, timelength=rec_time, sensitivity=10) # this is rec_time long

    # -----------------------------------------------------------------------------
    e.loop_start(no_echoes)
    
    e.set_phase([90.0, 90.0, 270.0, 270.0][run%4])            
    e.wait(tau-0.5e-6-5e-6-rec_time/2)
        
    e.ttl_pulse(length=5e-6, value=1)             # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)       # RF pulse            
            
    e.set_phase(phase+[0,180,0,180][run%4])
    e.wait(tau-0.5e-6-rec_time/2)                   

    e.record(samples=no_points, frequency=sampl_freq, timelength=rec_time, sensitivity=5) # this is rec_time long
    
    e.loop_end()


    return e
    

def experiment():
    accumulations=4
    for run in xrange(accumulations):
        yield fid_experiment(run)
        pass