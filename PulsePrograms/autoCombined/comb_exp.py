import xml.etree.ElementTree as ET
import time

def get_time(experiment):
    tree = ET.fromstring(experiment.write_xml_string()) # create XML tree representation
    time = 0
    for state in tree.getiterator(tag='state'):
        time += float(state.get('time'))
    return time

def fid_experiment(pulse,tm,run,phase):
    e=Experiment()
    #e.set_pfg(dac_value=0,is_seq=1)
    e.set_description("run",run)
    e.set_description("tm",tm)
    
    gate=10e-6

    # ---------------------------------------------------------------------
    dead_time = 6e-6  # (s)   
    # ---------------------------------------------------------------------
    
    # t_rep
    e.wait(1e-3)
    # sat rec, leaving gate on
    for i,t_sat in enumerate(N.logspace(N.log10(1e-6),N.log10(100e-3),32)[::-1]):
        e.ttl_pulse(length=t_sat, value=1)              # gate high-power ampli on
        e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    
    if pulse>10e-6:
        raise Exception("--- Pulse too long!!! ---")
    # ---------------------------------------------------------------------  
    e.set_phase(0)    
    e.wait(tm-0.5e-6-gate)    

    # measuring pulse ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1+4)              # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)            # RF pulse     
    # ---------------------------------------------------------------------    
    
    
    e.set_phase(phase+[0,90,180,270][run%4])         # receiver phase cycling
    e.set_description("rec",[0,1,2,3][run%4])
    e.wait(dead_time-0.5e-6)                                        # dead time
    e.record(samples=1024*8, frequency=20e6, sensitivity=10)     # acquisition command
    return e
    



def Hahn_exp(pulse90,pulse180,td, tau, run, accumulations):
    e=Experiment()    
    e.set_description("tau",tau)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    

    
    rec_phase = 63                          # receiver phase
    gate = 10e-6

    
    # --------------------------------------------------------------------------------
    if pulse90 > 10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if pulse180 > 10e-6:
        raise Exception("--- 180 Pulse too long!!! ---")
    if tau < gate:
        raise Exception("--- Echo time shorter than gate time!!! ---")
    # ---------------------------------------------------------------------
    
    e.wait(1e-3)
    phase90 = [0,180,90,270][(run/2)%4]
    phase180 = [90,270,90,270,0,180,0,180][run%8]
    
    e.set_phase(phase90)
    e.wait(td-0.5e-6)
    
    # Hahn-echo ----------------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)            # RF pulse 
    
    e.set_phase(phase180)        # phase cycle to remove fid from first & last pulse 
                                                                                               
    e.wait(tau-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)                  # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)          # RF pulse            
    # ---------------------------------------------------------------------    
    
    e.set_phase(rec_phase)    # receiver phase 

    e.wait(tau-0.5e-6-5e-6)                                           # dead time included

    e.record(samples=8*1024, frequency=10e6, sensitivity=10)
    return e

    

def Stim_experiment(run, tp, tm, pulse, phase, td):
    e=Experiment()
    e.set_description("run",run)
    e.set_description("tp",tp)
    e.set_description("tm",tm)
    e.set_description("pulse",pulse)
    e.set_description("phase",phase)
    e.set_description("td",td)
    
    #phase cycling removes all but first and second FID
    ph1=0
    ph2 = [0,180][run%2]
    ph3 = [0,180,180,0][run%4]
    e.set_description('rec',[0,0,2,2][run%4])
    #rec_phase = [0,90,180,270][run%4]
    # ----------------------------------------------------------------------
    dead_time = 15e-6  	# dead time (s)
    e.set_description("dead",dead_time)
    gate = 10e-6        # gate time (s)
    # ---------------------------------------------------------------------
    if pulse>10e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if tm < gate:
        raise Exception("--- Mixing time shorter than gate time!!! ---")
    if tp < gate:
        raise Exception("--- Evolution time shorter than gate time!!! ---")
    if tp < dead_time:
        raise Exception("--- STE is within receiver dead time ---")
    # ---------------------------------------------------------------------
    e.wait(1e-3)    
    e.set_phase(ph1)    
    e.wait(td-0.5e-6-gate)    

    # Stimulated-Echo ------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse, value=1+2)        # RF pulse 1       
    e.set_phase(ph2)                   
    e.wait(tp-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse, value=1+2)         # RF pulse 2 
    e.set_phase(ph3)                    
    e.wait(tm-0.5e-6-gate)
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse, value=1+2)         # RF pulse 3
    # ---------------------------------------------------------------------    
                         
    e.set_phase(phase)    # receiver phase
    e.wait(dead_time-0.5e-6)  # dead time
    e.record(samples=1024*64, frequency=20e6, sensitivity=10)    # acquisition command
    return e
# satrec



def experiment():
    T_sample = 245.0
    T_set = 235.2
    sample = "dCPC-bk2"

    pulse90 = 1.4e-6
    pulse180  = 2.8e-6               # (s) pulse length
    td            = 0.19*5                # (s) delay between sequences > 5*T1) for hahn and ste
    
    # Saturation Recovery Parameters
    # do SatRec
    SatRec = False
    sr_start = 20e-5
    sr_stop = 10 ###
    sr_points = 26    
    sr_phase=60
    sr_accumulations= 4*2
    change_accu_delay = 10
    sr_reduced_accus = 4
    

    # Hahn Echo Parameters
    Hahn = False # do Hahn Echo 
    hahn_startpoint           = 30e-6 #  first used echo delay
    hahn_endpoint            = 10e-3 #8ms  # last used echo delay
    hahn_points                = 32        # number of echo delays
    hahn_accumulations      = 8*4    # number of repetitions (for a given echo delay), multiples of 8
    
    
    # STE Parameters
    STE = False	# do STE experiment 
    ste_phase         = 245              # receiver phase
    ste_tp_range = [100e-6,200e-6,300e-6]
    ste_tm_start = 200e-6
    ste_tm_stop = td
    ste_tm_points = 32
    ste_accumulations = 4*32                # number of repetitions       

    sr_delays = list(staggered_range(log_range(sr_start,sr_stop,sr_points),3))
    hahn_tp_range  = list(staggered_range(log_range(start=hahn_startpoint, stop=hahn_endpoint, stepno=hahn_points),3))
    ste_tm_range = list(staggered_range(log_range(ste_tm_start, ste_tm_stop, ste_tm_points),3))
    
    # estimate mesuring time
    mtime = 0
    for delay in sr_delays:                          # number of repetitions
        if delay > change_accu_delay:
            accus = sr_reduced_accus
        else:
            accus = sr_accumulations
        run = 0 # do not loop over accus
        ep = fid_experiment(pulse = pulse90,
                                tm=delay,
                                run=run,
                                phase=sr_phase)
        ep.set_description('T_sample',T_sample)
        ep.set_description('T_set',T_set)
        ep.set_description('sample',sample)
        ep.set_description('expname',"satrec")
        mtime += get_time(ep)*accus
    print "* \n* SatRec Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    # estimate experiment time
    
    for Hahn_delay in hahn_tp_range:
        run = 0 
        ep = Hahn_exp(pulse90,pulse180,td,tau=Hahn_delay,run=run,accumulations=hahn_accumulations)
        ep.set_description('T_set',T_set)
        ep.set_description('T_sample',T_sample)
        ep.set_description('sample',sample)
        ep.set_description('expname',"hahn")
        mtime += get_time(ep)*hahn_accumulations
    print "* \n* Hahn Echo Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "
    
    # Estimate measuring time
    for tp in ste_tp_range:
        for tm in ste_tm_range:
            run = 0
            ep = Stim_experiment(run, tp, tm, pulse90, ste_phase, td)
            mtime += get_time(ep)*ste_accumulations
    print "* \n* STE Experiment will be finnished at: %s\n*"%(time.ctime(time.time()+mtime))
    print "* Time: %.0fdays %.0f:%02.0f"%(mtime/(24*3600.), (mtime/3600)%24, (mtime/60)%60),"\n* "    
    
    
    #time.sleep(3600)
    # now do the real measurement
    # satrec
    if SatRec:
        for delay in sr_delays:                          # number of repetitions
            if delay > change_accu_delay:
                accus = sr_reduced_accus
            else:
                accus = sr_accumulations
            for run in xrange(accus):
                ep = fid_experiment(pulse = pulse90,
                                tm=delay,
                                run=run,
                                phase=sr_phase)
                ep.set_description('T_sample',T_sample)
                ep.set_description('T_set',T_set)
                ep.set_description('sample',sample)
                ep.set_description('expname',"satrec")
                yield ep
    
    # Hahn

    

    # start real experiment
    if Hahn:
        for Hahn_delay in hahn_tp_range:
            for run in xrange(hahn_accumulations): 
                ep = Hahn_exp(pulse90,pulse180,td,tau=Hahn_delay,run=run,accumulations=hahn_accumulations)
                ep.set_description('T_set',T_set)
                ep.set_description('T_sample',T_sample)
                ep.set_description('sample',sample)
                ep.set_description('expname',"hahn")
                yield ep
    

# STE
    
    if STE:
        for tp in ste_tp_range:
            for tm in ste_tm_range:
                for run in xrange(ste_accumulations):
                    ep = Stim_experiment(run, tp, tm, pulse90, ste_phase, td)
                    ep.set_description('T_set',T_set)
                    ep.set_description('T_sample',T_sample)
                    ep.set_description('sample',sample)
                    ep.set_description('expname',"ste")
                    yield ep
                synchronize()
                pass