from pylab import log,exp,arange,load

def InvRec_exp(pulse90, pulse180, tau, run, accumulations,td, phase):
    e=Experiment()    
    e.set_description("tau",tau)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    e.set_frequency(300.03385e6,0)
    # -------------------------------------------------------------------------------
    gate = 5e-6
    
    # --------------------------------------------------------------------------------
    if pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")
    if tau < gate:
        raise Exception("---Inv. Rec. time shorter than gate time!!! ---")
    # ---------------------------------------------------------------------
    
    e.wait(1e-3)
    phase180 = [0,180][run%2]
    e.set_phase(phase180)                   # phase cycle to remove fid from first pulse
    e.wait(td-0.5e-6)
    composite=False
    # Inversion Recovery --------------------------------------------------
    if not composite:
        e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
        e.ttl_pulse(length=pulse180, value=1+2)          # RF pulse
    else:
        # Start Composite 180 ---------------------------------------------------------------
        e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
        e.ttl_pulse(length=pulse90, value=1+2)          # RF pulse
        e.set_phase(phase180, ttls=1)                       
        #e.wait(1.5e-6)
        e.ttl_pulse(length=1.5e-6, value=1)                  # gate high-power ampli on
        e.ttl_pulse(length=pulse180, value=1+2)          # RF pulse
        e.set_phase(phase180+90, ttls=1)                       
        #e.wait(1.5e-6)
        e.ttl_pulse(length=1.5e-6, value=1)                  # gate high-power ampli on
        e.ttl_pulse(length=pulse90, value=1+2)          # RF pulse
        # End Composite -----------------------------------------------------------------
    e.set_phase([0,180,90,270][(run/2)%4])                       
    
    e.set_phase([0,180,90,270][(run/2)%4])                                                                                           
    e.wait(tau-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)            # RF pulse            
    # ---------------------------------------------------------------------    
    
    e.set_phase(phase)         # receiver phase
    e.wait(15e-6)                                                      # dead time 

    e.record(samples=1024*4, frequency=0.5e6, sensitivity=5)   # acquisition command

    return e

    
def experiment():
    startpoint           = 20e-6 # (s) > gate !!! first used Inv. Rec delay
    endpoint            = 10        # (s) last used Inv. Rec. delay
    points                = 21	        # number of Inv. Rec. delays
    accumulations      = 8    # number of repetitions (for a given Inv. Rec. delay)
    
    td        = 3.2 # (s) delay between sequences
    pulse90    = 2.44e-6                  # (s) pulse length
    phase = 45+90
    pulse180  =    5.3e-6               # (s) pulse length    
    temp=0
    T_sample = 288.0
    for tt in log_range(start=startpoint, stop=endpoint, stepno=points):
        temp=temp+tt        
    measuringt = (temp*accumulations+accumulations*points*td)/3600.0
    print "\n\n\tMeasuring time will be approx.", measuringt, "hours"
    for InvRec_delay in staggered_range(log_range(start=startpoint, stop=endpoint, stepno=points),3):
        for run in range(accumulations): 
            ep= InvRec_exp(pulse90, pulse180, tau=InvRec_delay,run=run,accumulations=accumulations,td=td, phase=phase)
            ep.set_description('T_sample',T_sample)
            yield ep
        pass