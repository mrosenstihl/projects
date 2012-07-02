from numpy import linspace,arange

def Hahn_exp(pulse90, pulse180, gradient, delta, conv, tau, run, accumulations, td, rec_phase):
    e=Experiment()    
    e.set_description("tau",tau)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    e.set_description("gradient",gradient)
    e.set_description("delta",delta)
    
    e.set_description("conv",conv)
  
    phase_time = 0.5e-6
    gate = 5e-6
    dac = int(gradient/conv)
    e.set_description("dac",dac)
    
    # --------------------------------------------------------------------------------
    if pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180>10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")
    if tau < delta:
        raise Exception("--- Echo time shorter than gradient time!!! ---")
    # ---------------------------------------------------------------------
    e.set_phase(0)
    e.wait(td-phase_time)
    # preparation pulses
    num_prepulses = 10
    if num_prepulses > 0:
        e.loop_start (num_prepulses)
        e.ttl_pulse (length=1e-6, value=8) # scope trigger
        e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))
        e.wait (0.2e-3)
        e.loop_end ()
    e.wait(100e-3)
    
    # Hahn-echo ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)            # RF pulse 
    e.set_phase([90.0,90.0,270,270,180,180,0,0][run%8])        # phase cycle to remove fid from first & last pulse 
    
    e.wait( (tau-delta)/2 - pulse90/2 - phase_time )
    
    e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))

    e.wait( (tau-delta)/2 - pulse90/2 - gate )
    
                                                                                               
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)          # RF pulse            
    # ---------------------------------------------------------------------    
    
    e.set_phase(rec_phase+[0,180,0,180,180,0,180,0][run%8])    # receiver phase cycling
    
    e.wait( (tau-delta)/2 - pulse90/2 - phase_time )
    
    e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))

    e.wait( (tau-delta)/2 - pulse90/2 - 0.5e-3)
    

    print run
    e.record(samples=4*4096, frequency=1e6, sensitivity=2)
    return e

    
def experiment():

    pulse90 = 2.1e-6
    pulse180 = 4.2e-6
    conv = 63.6e-6
    delta_list=[2e-3,1e-3,3e-3,4.5e-3]
    td=1.3*3

    rec_phase = 100
    gradient_list = linspace(0,4,11)
    #tau_list=[12e-3,14e-3,16e-3,18e-3]
    tau_list = arange(10e-3,50e-3,4e-3)
    accumulations      = 8*4    # number of repetitions (for a given echo delay), 8 for full phase cycle
 
    for delta in delta_list:
        for tau in tau_list:
            for gradient in gradient_list:
                for run in xrange(accumulations): 
                    hahn = Hahn_exp(pulse90,
                        pulse180, 
                        gradient,
                        delta,
                        conv, 
                        tau, 
                        run, 
                        accumulations, 
                        td,
                        rec_phase)
                    yield hahn
        synchronize()
        pass