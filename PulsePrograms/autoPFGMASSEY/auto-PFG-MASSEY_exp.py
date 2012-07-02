import numpy as N
class ParameterSet:
    """
    From 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308
    Alex Martelli
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def MASSEY(**parameter_set):
    e=Experiment()
    for key in parameter_set.keys():
        e.set_description(key,parameter_set[key])
    par = ParameterSet(**parameter_set)
    
    e.set_frequency(par.frequency,0) # needs 2 microseconds Phase

    ph1 = 0
    ph2 = 90
    rec_ph=120
    
    ############ PFG sequence #############
    e.set_phase(ph1)    	        # phase 1
    e.wait(par.repetition_time)
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi/2, value=3)	# gate+rf 2**0+2**1
    
    e.set_phase(ph2)                # Phase 2
    
    e.wait((par.tau-par.delta)/2-0.5e-6-3.8e-6)
    ########## sin**2 gradient ##########
    #for i in xrange(par.points):
    #    e.set_pfg(dac_value=int(par.dac*N.sin(i*N.pi/par.points)**2),length=par.delta/par.points, is_seq=1) # pfg 1
    #e.set_pfg(dac_value=0)
    e.set_pfg(dac_value=par.dac, length=par.delta, shape=('sin2',20e-6))
    
    e.wait((par.tau-par.delta)/2-par.read_length-150e-6)
    e.set_pfg(dac_value=par.read_gradient, length=par.read_length)
    e.wait(150e-6)                  # keeping distance to pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi, value=3)   	# gate+rf 2**0+2**1
    
    e.set_phase(rec_ph)            	# rec phase
    e.wait((par.tau-par.delta)/2-0.5e-6-3.8e-6)
    
    ########## sin**2 gradient ##########
    #for i in xrange(par.points):
    #    e.set_pfg(dac_value=int(par.dac*N.sin(i*N.pi/par.points)**2),length=par.delta/par.points, is_seq=1) # pfg 1
    #e.set_pfg(dac_value=0)
    e.set_pfg(dac_value=par.dac, length=par.delta, shape=('sin2',20e-6))
    if par.echo_shift > (par.tau-par.delta)/2:
        raise
    #e.wait(1e-3)
    e.wait((par.tau-par.delta)/2-par.echo_shift)
    e.set_pfg(dac_value=par.read_gradient,length=5e-6, is_seq=1)
    e.record(par.samples, par.samplerate, par.sensitivity)
    e.set_pfg(dac_value=0)
    return e
    
def experiment():
    starttime = 1e-3
    endtime = 7e-3
    points = 5
    T1= 0.0002
    rep_time = 5*T1
    tips =log_range(starttime,endtime,points)
    timepoints = [i for i in tips]
    timepoints = [3e-3]#[10e-3]
    dac_values = N.arange(0, 300001, 30000)
    no_akku=1
    bvt = 285
    tmp=279
    print "Estimated time (h):", len(timepoints)*len(dac_values)*no_akku*rep_time/3600.0
    
    for tp in timepoints:  # timepoints
        # First we need the Echo position WITHOUT PFGs
        for akku in xrange(no_akku): # Accumulations
                yield MASSEY( 
                    pi = 3.4e-6,
                    gate = 5e-6,
                    frequency   = 300.03385e6,
                    samplerate = 0.20e6,
                    sensitivity = 0.2,
                    samples = 8*1024,
                    tau		=   tp, 
                    repetition_time = rep_time,
                    delta = 2e-3,
                    points = 40,
                    dac = 0,
                    read_gradient = 0,
                    read_length=0.2e-3,
                    akku	= akku,
                    no_akku = no_akku,
                    echo_shift = 0.35e-3,
                    bvt_temp=bvt,
                    temperature=tmp,
                    spectrum = "original")
        synchronize()           # making sure that the echo position is indeed determined and saved
        # Doing now exactly one phase cycle to find the current echo position for each applied gradient
        for dv in dac_values:
            synchronize()
            for akku in xrange(16): # Accumulations
                yield MASSEY( 
                    pi = 3.4e-6,
                    gate = 5e-6,
                    frequency   = 300.03385e6,
                    samplerate = 0.20e6,
                    sensitivity = 0.2,
                    samples = 8*1024,
                    tau		=   tp, 
                    repetition_time = rep_time,
                    delta = 2e-3,
                    points = 40,
                    dac = int(dv),
                    read_gradient =int(50e-3/6.7e-5),
                    read_length=0.4e-3,
                    akku	= akku,
                    no_akku = 16,
                    echo_shift = 0.35e-3,
                    bvt_temp=bvt,
                    temperature=tmp,
                    spectrum = "test")
            synchronize()
            # Read in the correction data
            correction = pickle.read('.correction_data')
            for akku in xrange(no_akku): # Accumulations
                yield MASSEY( 
                    pi = 3.4e-6,
                    gate = 5e-6,
                    frequency   = 300.03385e6,
                    samplerate = 0.20e6,
                    sensitivity = 0.2,
                    samples = 8*1024,
                    tau		=   tp, 
                    repetition_time = rep_time,
                    delta = 2e-3,
                    points = 40,
                    dac = int(dv),
                    read_gradient =int(50e-3/6.7e-5),
                    read_length=0.2e-3+correction,
                    akku	= akku,
                    no_akku = no_akku,
                    echo_shift = 0.35e-3,
                    bvt_temp=bvt,
                    temperature=tmp,
                    spectrum = "final")