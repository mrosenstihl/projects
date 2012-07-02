
from pylab import log,exp,arange,load

def pulse_exp(pulse, run, accumulations):
    e=Experiment()
    e.set_description("pulse",pulse)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    
    tau=115e-6
    
    pulse180  = 15e-7            # (s) pulse length
    
    td        = 1                        # (s) time between pulse sequences> 5*T1 
        
    phase = 230                     # receiver phase
    
    # ---------------------------------------------------------------------
    dead_time = 15e-6     # (s) 
    # ---------------------------------------------------------------------
    if pulse>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")  
    if tau <0.1e-3:
        raise Exception("--- Echo time shorter than gate time!!! ---")            
    # ---------------------------------------------------------------------
    
    # -------------------------------------------------------------------
    e.wait(1e-3)
    e.set_phase(0)  
    e.wait(td-0.5e-6)
    
    # Hahn echo -----------------------------------------------------------
    e.ttl_pulse(length=100e-6, value=1)               # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)             # RF pulse 
    
    e.set_phase([90,90,270,270,180,180,0,0][run%8])               # phase cycle to remove fid from first & last pulse
                                                                                    
    e.wait(tau-0.5e-6-100e-6) 
    e.ttl_pulse(length=100e-6, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse180, value=1+2)       # RF pulse
    # ---------------------------------------------------------------------    
        
    e.set_phase(phase+[0,180,0,180,180,0,180,0][run%8])             # receiver phase cycling
    e.wait(dead_time-0.5e-6)                                # dead time
    e.wait(pulse)
    
    e.record(samples=4*4096, frequency=2e7, sensitivity=10)   # acquisition command

    return e

    
def experiment():
    startpoint              = 5.0e-7           # first used pulse length
    endpoint               = 11e-7             # last used pulse length
    points                   = 20                  # number of pulse lengths
    accumulations      = 8*1                 # number of repetitions (for a given pulse length)
    

    timepoints = arange(startpoint,endpoint,(endpoint-startpoint)/points)

    for p_delay in timepoints:  
        for run in range(accumulations): 
            yield pulse_exp(pulse=p_delay,run=run,accumulations=accumulations)
            pass
