import numpy as N
import time
class ParameterSet:
    """
    From 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308
    Alex Martelli
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def t2_exp(**parameter_set):
    e=Experiment()
    e.set_pfg(dac_value=0)
    
    for key in parameter_set.keys():
        e.set_description(str(key),parameter_set[key])
    par = ParameterSet(**parameter_set)
    e.set_frequency(par.frequency,0) # needs 2 microseconds Phase


    # cacnelled ein Echo nicht aus!!
    # Define the phases
    if False:
        ph1 = [3 ,3,1,1,0,0,2,2,1,1,3,3,2,2,0,0][ (par.akku%16) ]*90
        ph2 = ph1
        ph3 = ph1
        ph4 = ph1

        ph5 = [0,2,1,3,1,3,2,0,2,0,3,1,3,1,0,2][ (par.akku%16) ]*90
        rec_phase = [0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3][ (par.akku%16) ]
        #rec_phase = [0,1,2,3][ (par.akku/4%4) ]
        print ph1/90,rec_phase,ph5/90
        e.set_description("rec_phase",-rec_phase) # orig
        #rec_phase += [0,1,2,3][ (par.akku%4) ]
        #e.set_description("rec_phase",rec_phase)
        #rec_phase *= 90
        rec_phase=0
    
    # improved phase cycling from: P.Z. Sun, JMR 161(2003),pp. 168-173
    
    if False:  # not full cylcops , not changing x,y channels
        if not par.no_akku%8 == 0:
            raise ValueError,"no_akku must be multiple of 8"
        ph1 = 0
        ph2 = 90
        ph3 = [0,180,0,180,90,270,90,270][ (par.akku%8) ]
        ph4 = [0,0,180,180,90,90,270,270][ (par.akku%8) ]
        ph5 = 90
        #rec_phase = [0 ,180,180,0,0,180,180,0][ (par.akku%8) ]
        rec_phase = 0
        e.set_description("rec_phase",[0 ,2,2,0,0,2,2,0][ (par.akku%8) ])
    
    if True: # with cyclops, poor mans approach
        if not par.no_akku%32 == 0:
            raise ValueError,"no_akku must be multiple of 32"
        cyc = [0,90,180,270][par.akku%4]
        
        ph1 = 0
        ph2 = 90
        ph3 = [0,180,0,180,90,270,90,270][ (par.akku/4%8) ]
        ph4 = [0,0,180,180,90,90,270,270][ (par.akku/4%8) ]
        ph5 = 90
        rec_phase = [0 ,180,180,0,0,180,180,0][ (par.akku/4%8) ] + cyc
        print "%3i\t%3i\t%3i\t%3i\t%3i\t%3i"%(ph1/90, ph2/90, ph3/90,ph4/90,ph5/90,rec_phase/90)
        e.set_description("rec_phase",cyc/90)
        
    

    
    ############ 13 Interval PFG sequence #############
    e.set_phase(ph1)    	        # phase 1
    e.wait(par.repetition_time-par.tau)
    ### start of preparation PFG pulses ###

    if True:
        for i in xrange(6):
            e.wait(par.tau)
            e.set_pfg(dac_value=par.dac, length=par.delta, shape=('sin2',40e-6))
            e.set_pfg(dac_value=0, length=par.delta)
    e.wait(par.tau)
    
    ### end of preparation PFG pulses ### 

    # First RF pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi2, value=3)	# gate+rf 2**0+2**1
    
    # First PFG
    e.set_phase(ph2)    	        # phase 2
    e.wait((par.tau-par.delta)/2 - 0.5e-6)
    e.set_pfg(dac_value=-par.dac, length=par.delta, shape=('sin2',40e-6))
    e.wait((par.tau-par.delta)/2 - par.gate)

    # Second RF pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi, value=3)   	# gate+rf 2**0+2**1
    
    # Second PFG
    e.set_phase(ph3)    	        # phase 3
    e.wait((par.tau-par.delta)/2 - 0.5e-6)
    e.set_pfg(dac_value=par.dac, length=par.delta, shape=('sin2',40e-6))
    e.wait((par.tau-par.delta)/2 - par.gate)
    
    # Third RF pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi2, value=3)	# gate+rf 2**0+2**1

    # Mixing time
    e.set_phase(ph4)   	        # phase 4
    e.wait(par.tmix/2.)
    #e.wait(par.delta)
    #e.set_pfg(dac_value=300, length=5e-3, shape=('sin2',40e-6)) # homo spoil
    e.wait(par.tmix/2. - 5e-6)

    # Fourth RF pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi2, value=3)	# gate+rf 2**0+2**1

    # Third PFG
    e.set_phase(ph5)    	        # phase 5
    e.wait((par.tau-par.delta)/2. - 0.5e-6)

    e.set_pfg(dac_value=-par.dac, length=par.delta, shape=('sin2',40e-6))

    e.wait((par.tau-par.delta)/2. - par.gate)
    
    # Fith RF pulse
    e.ttl_pulse(par.gate, value=1) 	# gate 2**0
    e.ttl_pulse(par.pi, value=3)   	# gate+rf 2**0+2**1
    
    # Fourth PFG
    e.set_phase(rec_phase)            	# rec phase
    e.wait((par.tau - par.delta)/2 - 0.5e-6)

    e.set_pfg(dac_value=par.dac, length=par.delta, shape=('sin2',40e-6))

    #e.wait((par.tau - par.delta)/2 - 0.4e-3)
    #e.wait(0.5)

#    e.set_pfg(dac_value=100,is_seq=1)
    e.record(par.samples, par.samplerate, sensitivity=par.sensitivity)
    e.set_pfg(dac_value=0)
    return e
    
def experiment():
    
    ########### Wiederholrate der  Experimente
    T1= 1.2
    rep_time = 3*T1
    
    
    ############## RF Pulsabstand; tau
    timepoints = [2e-3]
    
    ##############  Mischzeiten, tm
    #mix_points = [20e-3,40e-3,60e-3,80e-3]
    #mix_points = log_range(10e-3,1*T1,12)
    mix_points = N.linspace(5e-3,80e-3,15)
    
    
    ############# Akkumulationen
    no_akku= 32

    
    ############### Konvertierungsfaktor dac > T/m
    conv = 6.36e-5
    
    
    ########### Gradientenwerte  delta,g

    delta = 0.3e-3 # Laenge des PFG Pulses
    
    gradients = N.linspace(5,6,2) # Gradientenstaerke
    gradients = N.hstack((0, gradients ))
    
    
    gradients = N.array([0,2,3,4,5,6,7,8,9,10])
    
    # Diese werden an das Experiment geschickt
    dac_values = gradients/conv
    #time.sleep(20*60)
    for dv in dac_values:
        for tp in timepoints:  # Pulse distance tp
            for tmix in mix_points: # Evolution time tmix
                synchronize()
                for akku in range(no_akku): # Accumulations
                    yield t2_exp( 
                    pi = 4.1e-6,
                    pi2=2.05e-6,
                    gate = 5e-6,
                    frequency   = 300.03385e6,
                    samplerate = 0.2e6,
                    sensitivity = 5,
                    samples = 4*1024,
                    tau         =   tp,
                    tmix  = tmix,
                    repetition_time = rep_time,
                    delta = delta,
                    dac = int(dv),
                    akku	= akku,
                    no_akku = no_akku,
                    bvt_temp=265,
                    temperature=290.4,
                    sample="Tetradecane")
