from numpy import linspace,array
import warnings
import time
import subprocess # for executing bvt control program
import os

def Stim_exp(pulse90, pulse180, rec_phase, tm, tau, gradient, conv, delta, run, accumulations, t_rep, t_wait):
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
    if t_rep <= tm:
        raise Exception("t_rep must not be smaller than tm")
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
    e.set_phase(270)
    e.wait(t_rep)
    # Inversion Pulse ------------------------------------------------------
    e.ttl_pulse(length=gate, value=1)              # gate high-power ampli on
    e.ttl_pulse(length=pulse180, value=1+2)        # RF pulse  

    e.set_phase(0)
    e.wait(t_wait-phase_time-tm)
    
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

    e.record(samples=8*1024, frequency=0.2e6, sensitivity=5)    # acquisition command
    return e


def get_eurotemp():
    os.system('tail -100 /home/markusro/Desktop/eurotherm_data.dat > tmp')#.readlines()[-1].strip().split()[-1]
    f = open('tmp')
    temps,off = [],0
    for line in f:
        temps.append(float(line.strip().split()[-1]))
    t_eur = array(temps).mean()
    print "Temperature: ",t_eur,"K"
    return t_eur

def experiment():
    pulse90             = 2.05e-6
    pulse180            = 4.37e-6
    rec_phase           = 60                   # number of repetitions (for a given mixing time)
    accumulations       = 8#*16                   # number of accumulations should be multiple of 8
    gradient_range      = N.sqrt(linspace(0,(5)**2,32))     # gradient range in T/m (approx.)
    conv                = 6.39e-5               # conversion factor
    delta               = 0.5e-3                  # gradient length
    taurange            = [3e-3]                # used evolution times
    tm_range            = N.logspace(25e-3,1,15)#[0.25,]              # used mixing times
    t_rep               = 3*0.9                     # repetition time(s) 
    t_wait              = 1.1                   	# delay between inv pulse and STE sequence (s)
    temps               = [265]

    for i,temperature in enumerate(temps):
#        subprocess.call(['/home/markusro/PulsePrograms/bvt1000', str(int(temperature))])
        if i != 0:
            #raise ValueError
            print "Waiting ..."
#            time.sleep(30*60) # sleep for minutes after temperature change!
#        else:
#            pass
        try:
            t_eur = get_eurotemp()
        except:
            t_eur = '-'
            warnings.warn('Could not read Eurotherm data', Warning)
        for tau in taurange:
            for tm in tm_range:
                for gradient in gradient_range:
                    get_eurotemp()
                    for run in xrange(accumulations):	
                        stimecho = Stim_exp(
                            pulse90,
                            pulse180,
                            rec_phase, 
                            tm, 
                            tau, 
                            gradient,
                            conv,
                            delta, 
                            run, 
                            accumulations, 
                            t_rep,
                            t_wait)
                        stimecho.set_description('T_BVT','Collagen'+str(temperature)+'K')
                        stimecho.set_description('T_EURO',t_eur)
                        stimecho.set_description('Sample','Collagen')
                        yield stimecho
                    synchronize()
            pass