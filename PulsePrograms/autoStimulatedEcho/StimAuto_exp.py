import PulsePrograms.pulsetools as T

def ste(**args):
    """
    Parameters to set:
    run,         # run
    pulse90,     
    tp,          # evolution time
    tm,          # mixing time
    phase,       # receiver phase
    gate,        # high power amplifier gating time
    dead_time,   # receiver dead time
    nsamples,    # number of samples (ADC)
    samplefreq,   sampling freq (ADC)
    sens,        # sensitivity (ADC)

    """
    e=Experiment()
    par = T.ParameterSet(e,args)
    #phase cycling removes all but first and second FID
    ph1=0
    ph2 = [0,180][par.run%2]
    ph3 = [0,180,180,0][par.run%4]
    e.set_description('rec',[0,0,2,2][par.run%4])
    #rec_phase = [0,90,180,270][run%4]
    # ----------------------------------------------------------------------
    if par.pulse90>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if par.tm < par.gate:
        raise Exception("--- Mixing time shorter than gate time!!! ---")
    if par.tp < par.gate:
        raise Exception("--- Evolution time shorter than gate time!!! ---")
    if par.tp < par.dead_time:
        raise Exception("--- STE is within receiver dead time ---")
    # ---------------------------------------------------------------------
    e.wait(1e-3)    
    e.set_phase(ph1)    
    e.wait(par.td-0.5e-6-par.gate)    

    # Stimulated-Echo ------------------------------------------------------
    e.ttl_pulse(length=par.gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=par.pulse90, value=1+2)        # RF pulse 1       
    e.set_phase(ph2)                   
    e.wait(par.tp-0.5e-6-par.gate90)
    e.ttl_pulse(length=par.gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=par.pulse90, value=1+2)         # RF pulse 2 
    e.set_phase(ph3)                    
    e.wait(par.tm-0.5e-6-par.gate)
    e.ttl_pulse(length=par.gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=par.pulse90, value=1+2)         # RF pulse 3
    # ---------------------------------------------------------------------    
                         
    e.set_phase(par.phase)    # receiver phase
    e.wait(par.dead_time-0.5e-6)  # dead time
    e.record(samples=par.nsamples, frequency=par.samplefreq, sensitivity=par.sens)    # acquisition command
    return e


def ste_experiment(tp_range, tm_range, accumulations, **kwds):
    mtime = 0
    for tp in tp_range:
        for tm in tm_range:
            e = ste(run=0,**kwds)
            mtime += T.get_scan_time(e)*accumulations
    print mtime
    for tp in tp_range:
        for tm in tm_range:
            for run in xrange(accumulations):
                e = ste(run=run,**kwds)
                yield e
            synchronize()

    

def experiment():
    accumulations = 4*16                # number of repetitions       
    tp            = 1e-3             # (s) evolution time: distance between first two pulses > 0.1e-3
    tm            = 10e-3            # (s) mixing time: distance between last two pulses > 0.1e-3
    phase         = 250              # receiver phase
    pulse         = 1.4e-6           # (s) pulse length
    td            = 0.21*5                # (s) delay between sequences > 5*T1)
    tp_range = [100e-6,200e-6,300e-6]
    tm_range = list(log_range(200e-6,td,24))
    
    # Estimate measuring time
    mtime = 0
    for tp in tp_range:
        for tm in tm_range:
            run = 0
            ep = Stim_experiment(run, tp, tm, pulse, phase, td)
            mtime += get_time(ep)*accumulations
    print "* \n* Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    for tp in tp_range:
        for tm in tm_range:
            for run in xrange(accumulations):
                yield Stim_experiment(run, tp, tm, pulse, phase, td)
            synchronize()
        pass
