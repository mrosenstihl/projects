from numpy import linspace,array
import warnings
import time
import subprocess # for executing bvt control program

import os, sys
sys.path.append('/home/markusro/Daten/Lysozyme_h03/PulsePrograms/autoInversionRecovery')
import eurotherm_mod


def Stim_exp(pulse90, rec_phase, tm, tau, gradient, conv, delta, run, accumulations, t_rep):
    e=Experiment()
    e.set_description("tm",tm)
    e.set_description("tau",tau)
    e.set_description("delta",delta)
    e.set_description("run", run)
    e.set_description("accumulations", accumulations)
    e.set_description("gradient",gradient)
    e.set_description("conv",conv)
#    e.set_description("t",t)
#    e.set_description("t",t)
    
    # ----------------------------------
    gate = 5e-6
    phase_time = 0.5e-6
    dac = gradient/conv
    e.set_description("dac",dac)
    # ----------------------------------
    # ----------------------------------------------------------------------
    #if accumulations%8 != 0:
    #    print "--- Warning: uncomplete phase cycle!! ---"
    if pulse90 > 20e-6:
        raise Exception("--- 90 Pulse too long!!! ---")
    if tm < gate:
        raise Exception("--- Mixing time shorter than gate time!!! ---")
    if tau < gate:
        raise Exception("--- Evolution time shorter than gate time!!! ---")
    if accumulations%8 != 0:
         warnings.warn('Accumulations should be multiple of 8: %i'%accumulations, Warning)
    # ---------------------------------------------------------------------
       # preparation pulses
    num_prepulses = 5
    if num_prepulses > 0:
        e.loop_start (num_prepulses)
        e.ttl_pulse (length=1e-6, value=8) # scope trigger
        e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))
        e.wait (0.2e-3)
        e.loop_end ()
    
    e.wait(1e-3)
    e.set_phase(0)
    e.wait(t_rep-phase_time)
    
    # Stimulated-Echo ------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse90, value=1+2)        # RF pulse  
       
    e.set_phase([90,90,270,270][run%4])             

    if dac == 0.0:
        #print "DAC is zero"
        e.wait(tau - pulse90/2 - gate)
    else:
        e.wait( (tau-delta)/2 - pulse90/2 - phase_time )
    
        e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))

        e.wait( (tau-delta)/2 - pulse90/2 - gate )
    
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse90, value=1+2)         # RF pulse 
    e.set_phase([90,90,90,90,270,270,270,270][run%8])                    
      
    e.wait(tm-phase_time-gate)
    e.ttl_pulse(length=gate, value=1)               # gate high-power ampli on         
    e.ttl_pulse(length=pulse90, value=1+2)         # RF pulse   
    # --------------------------------------------------------------------- 
    
    e.set_phase(rec_phase+[0,180,180,0,180,0,0,180][run%8])    # receiver phase cycling
    if dac == 0.0:
        e.wait(tau - pulse90/2)
    else:
        e.wait( (tau-delta)/2 - pulse90/2 - phase_time )
    
        e.set_pfg(dac_value=dac, length=delta, shape=('sin2',20e-6))

        e.wait( (tau-delta)/2 - pulse90/2)

<<<<<<< TREE
    e.record(samples=8*1024, frequency=1e6, sensitivity=2)    # acquisition command
=======
    e.record(samples=16*1024, frequency=1e6, sensitivity=2)    # acquisition command
>>>>>>> MERGE-SOURCE
    return e


def get_eurotemp():
    #os.system('tail -100 /home/markusro/Desktop/eurotherm_data.dat > tmp')#.readlines()[-1].strip().split()[-1]
    #f = open('tmp')
    #temps,off = [],0
    #for line in f:
    #    temps.append(float(line.strip().split()[-1]))
    t_eur = array(temps).mean()
    print "Temperature: ",t_eur,"K"
    return t_eur

def experiment():
    pulse90             = 2.1e-6
    rec_phase           = 0                   # number of repetitions (for a given mixing time)
    accumulations       = 8*2#*4*8                  # number of accumulations should be multiple of 8
    gradient_range      = N.linspace(0,10,21)# #0..16 OTPN.sqrtlinspace(0,(8)**2,20))     # gradient range in T/m (approx.)
    conv                = 6.39e-5               # conversion factor
    delta               = 0.65e-3                  # gradient length
    taurange            = [1.8e-3]                # used evolution times
#    tm_range            = N.logspace(N.log10(40e-3),N.log10(1),3) # OTP
#    tm_range            =  N.logspace(N.log10(12e-3),N.log10(100e-3),3) # used mixing times
    tm_range            =  [40e-3, 90e-3]#N.logspace(N.log10(20e-3),N.log10(300e-3),3) # used mixing times

    t_rep               = 1.1#35e-3*5                    # (s) delay between sequences
    temps               = [300]

    t_rep               = 4                    # (s) delay between sequences
    temps               = [288]
    T_man               = 288.0
    for i,temperature in enumerate(temps):
        #subprocess.call(['/home/markusro/PulsePrograms/bvt1000', str(int(temperature))])
        if i != 0:
            #raise ValueError
            print "Waiting ..."
#            time.sleep(30*60) # sleep for minutes after temperature change!
#        else:
#            pass
        #try:
        #    t_eur = get_eurotemp()
        #except:
       #     t_eur = '-'
        #    warnings.warn('Could not read Eurotherm data', Warning)
        for tau in taurange:
            for tm in tm_range:
                for gradient in gradient_range:
                    for run in xrange(accumulations):
                        try:
                            T_sample = eurotherm_mod.get_current_temperature()	
                        except:
                            T_sample = T_man
                        stimecho = Stim_exp(pulse90, 
                            rec_phase, 
                            tm, 
                            tau, 
                            gradient,
                            conv,
                            delta, 
                            run, 
                            accumulations, 
                            t_rep)
                        stimecho.set_description('T_BVT','Coll03'+str(temperature)+'K')
                        stimecho.set_description('T_EURO',T_sample)
                        stimecho.set_description('Sample','Coll03')
                        yield stimecho
                        synchronize()
            pass
