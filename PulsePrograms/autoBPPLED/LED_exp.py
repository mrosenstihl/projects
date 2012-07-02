class ParameterSet:
    """
    From 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308
    Alex Martelli
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def LED(**parameter_set):
    e=Experiment()
    for key in parameter_set.keys():
        e.set_description(str(key),parameter_set[key])
    par = ParameterSet(**parameter_set)

    # 7 Pulse
	# From D.H. Wu, A.D. Chen and C.S. Johnson, Jr.. J. Magn. Reson., Ser. A 115 (1995), p. 260
	# in this folder johnson.pdf

    ph1 = 0
    ph2 = 0    # pi pulse
    ph3 = [0,0,180,180][par.run%4]
    ph4 = [0,180,90,270][divmod(par.run%16,4)[0]] # 4x 0, 4x 180 , 4x 90, 4x 270
    ph5 = 0 # pi pulse
    ph6 = 90*[0,2,0,2,2,0,2,0,1,3,1,3,3,1,3,1][par.run%16]
    ph7 = [0,180,90,270][divmod(par.run%16,4)[0]]
    rec = 90*[0,2,2,0,2,0,0,2,3,1,1,3,1,3,3,1][par.run%16]
    cyclops_phase = [0,1,2,3][divmod(par.run,16)[0]]
    e.set_description('cyclops',cyclops_phase)
    rec += cyclops_phase*90
    rec += par.corr_phase
    
    
    
    e.set_frequency(par.frequency,0)
    e.wait(par.repetition_time)

    for i in xrange(6):
        e.set_pfg(dac_value=par.dac, length=par.t_pfg, shape=('sin2',100e-6))
        e.wait(1e-3)
    e.wait(100e-3)

        
    # Puls 1 (90)
    e.set_phase(ph1)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pih, value=3)

    # Gradient 1
    e.wait(par.tau/2-par.t_pfg/2)
    e.set_pfg(dac_value=par.dac, length=par.t_pfg, shape=('sin2',20e-6))
    e.wait(par.tau/2-par.t_pfg/2)
    
    # Puls 2 (180)
    e.set_phase(ph2)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pi, value=3)

    e.wait(par.tau/2-par.t_pfg/2)
    e.set_pfg(dac_value=-par.dac, length=par.t_pfg, shape=('sin2',20e-6))
    e.wait(par.tau/2-par.t_pfg/2)

    e.set_phase(ph3)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pih, value=3)

    e.wait(par.tmix-par.gate-par.pih-0.5e-6)

    e.set_phase(ph4)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pih, value=3)

    e.wait(par.tau/2-par.t_pfg/2)
    e.set_pfg(dac_value=par.dac, length=par.t_pfg, shape=('sin2',20e-6))
    e.wait(par.tau/2-par.t_pfg/2)

    e.set_phase(ph5)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pi, value=3)

    e.wait(par.tau/2-par.t_pfg/2)
    e.set_pfg(dac_value=-par.dac, length=par.t_pfg, shape=('sin2',20e-6))
    e.wait(par.tau/2-par.t_pfg/2)

    e.set_phase(ph6)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pih, value=3)
    
    e.wait(par.t_eddy)
    
    e.set_phase(ph7)
    e.ttl_pulse(length=par.gate, value=1)
    e.ttl_pulse(length=par.pih, value=3)
    
    e.set_phase(rec)
    e.wait(par.dead_time)
    e.record(samples=par.points, frequency=par.samplerate, sensitivity=par.sensitivity)
    return e

def experiment():
    tmix_list=log_range(10e-3,100e-3,15)
    tmix_list = [100e-3]
    grad=0.1
    grad_list = N.linspace(0,3,11)
    accus= 4#64*1
    conv  = 6.36e-5
    for tm in tmix_list:
        for grad in grad_list:
            for run in xrange(accus):
                yield LED(
        repetition_time=0.65*3,
        frequency=300.03385e6,
        pih=1.79e-6,
        pi=3.62e-6,
        gate=5e-6,
        tau=3e-3,
        grad=grad,
        dac = grad/conv,
        t_pfg=1.5e-3,
        tmix=tm,
        t_eddy=0.05e-3,
        points=1024*8,
        samplerate=0.5e6,
        sensitivity=1,
        dead_time=5e-6,
        run=run,
        corr_phase=5,
        accu_length=accus
        )