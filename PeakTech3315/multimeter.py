import serial

class PeakTech3315:
	__doc__="""
	Class for connecting to PeakTech 3315 multimeter.
	
	If reading fails for some reason, it retries maxfail times (see below)
	Timeout is timeout (see below).
	Almost every function is implemented except:
		option byte 1:  PMAX, PMIN, VAHZ
		option byte 2: APO(AutoPowerOff), Auto(Auto mode)

	Options:
		port_no: 	which port to use (0,1,2,3 ...) Default: 0
	
	Methods:
		read():   returns float
		read_string returns AC/DC value units as string

	Variable:
		overload:	what should be returned when multimeter is overload Default: 'overload'
		mode:           beep when read (1) or be quiet (0, Default)
		maxfail:	maximum retries befor throwing and error Default=70

	Example:
		import peakread
		a = peakread.PeakTech3315(port_no=0)
		a.mode = 1
		a.overload='Muuuh'
		a.read()
		a.read_string()
"""
	def __init__(self, port_no=0):
		self.pt = serial.Serial(port=port_no,baudrate=2400, bytesize=7,stopbits=1, rtscts=1, parity='N', timeout=0.2)
		# mode   0=quite, 1=beep when reading data
		self.mode = 0	
		self.value = None
		self.unit = None
		self.acdc = ''
		self.maxfail = 70
		
		# inital raw data set to 0
		self.raw = '0'*9

		# This are the bytes
		self.range = int(self.raw[0])
		self.digits = int(self.raw[1:5])
		self.function_byte = self.raw[5]
		self.status_byte = int(self.raw[6])
		self.option1_byte = self.raw[7]
		self.option2_byte = self.raw[8]
		
		self.overload = False
		# send overload_string if overload
		self.overload_string = 'overload'
		# function/range mapping, first value is 'multiplier', the second is maximum range number
		self.function_range = {	';':[4,4], # Volts
					'=':[7,1], # uAmpere
					'9':[5,1], # mAmpere
					'?':[0,0], # Ampere
					'3':[1,5], # Resitance
					'5':[0,0], # Continuity
					'1':[0,0], # Diode
					'2':[2,5], #  Frequency
					'6':[12,7], # Capcitance
					'4':[0,0], # Temperature
					'>':[0,0], # ADP0
					'<':[0,0], # ADP1
					'8':[0,0], # ADP2
					':':[0,0] }# ADP3}
		# units
		self.units_dict = {	';':'V',
				  	'=':"A",# uA
					'9':'A',# mA
					'?':'A',
					'3':'Ohm',
					'5':'V/Cont',
					'1':'V/Diode',
					'2':'Hz',
					'6':'F',
					'4':'Temp',
					'>':'ADP0',
					'<':'ADP1',
					'8':'ADP2',
					':':'ADP3'}

		self.FailedReads = 0
		self.reads = 0
		self.connection = "Port: %s\nBaudrate: %s\nParity: %s\nBytesize: %s\nStopbits: %s\nTimeout: %s\nRTSCTS: %s\n"%(
					self.pt.portstr,self.pt.baudrate,self.pt.parity, self.pt.bytesize, self.pt.stopbits, self.pt.timeout,self.pt.rtscts)

	def __isdigit(self,abyte):
		return re.match(self.isdigit, abyte)

	def __read_data(self):
		"""
		Method for reading data from multimeter 
		"""
		if self.mode == 1:
			# make some noise
			print "\a"
		if self.FailedReads > self.maxfail:
			# set it FailedReads back
			self.FailedReads = 0 
			raise "Failed %i times to read data"%self.maxfail, "Check configuration:\n\n%s"%(self.connection)
		# flush the input buffer of the serial line
		self.pt.flushInput()
		# set REQUEST_TO_SEND 
		self.pt.setRTS(0)
		# discard the first word, may be incomplete
		self.pt.readline()
		# reading data, set self.raw; stripping \r\n
		self.raw = self.pt.readline()
		# Error Handling (wrong data, NOT connection)
		try:	
			self.overload = False
			# This are the bytes
			self.range = int(self.raw[0])
			self.digits = int(self.raw[1:5])
			self.function_byte = self.raw[5]
			self.status_byte = ord(self.raw[6])
			if self.status_byte & 1<<0:
				self.overload = True
			self.option1_byte = ord(self.raw[7])
			self.option2_byte = ord(self.raw[8])
			# Test if function is valid
			self.function_range[self.function_byte]
		
			# unset REQUEST_TO_SEND to prevent multimeter filling the serial buffer
			self.pt.setRTS(1)
		except ValueError:
			#raise "ERROR: Reading failed","Range, digits or status not integer values: %s %s"%(self.raw[0],self.raw[1-5], self.raw[6])
			self.FailedReads += 1
			self.__read_data()
		except KeyError:
			#raise "ERROR: Reading failed", "Function is not known: %s"%(self.raw[5])
			self.FailedReads += 1
			self.__read_data()
		except IndexError:
			#raise "ERROR: Reading failed", "String not read, timeout?: %s"%(self.raw)
			self.FailedReads += 1
			self.__read_data()
		self.FailedReads = 0 
		self.reads += 1

	def __range(self):
		exponent = self.function_range[self.function_byte][0]
		max_val = self.function_range[self.function_byte][1]
		if self.range > max_val:
			raise "ERROR: %s range not possible"%(self.function_dict[self.function_byte]), (self.range, max_val)
		self.value = self.digits * 10.0**(int(self.range) - exponent)
		
	def __sign(self):
		if self.status_byte & 1<<2:
			self.value *= -1

	def __unit(self):
		if self.function_byte == '4': # *C,*F
			if self.status_byte & 1<<3:
				self.unit = '*C'	
			else:
				self.unit = '*F'
		elif self.function_byte == '2': # freq/rpm
			if self.status_byte & 1<<3:
				self.unit = 'RPM'	
			else: 
				self.unit = 'Hz'
		else:
			self.unit = self.units_dict[self.function_byte]
			

	def __acdc(self):
		
		DC = False
		AC = False
		if bool(self.option2_byte & 1 << 3):
			DC = True
			self.acdc = 'DC'
		if bool(self.option2_byte & 1 << 2):
			AC = True
			self.acdc = 'AC'
		if self.function_byte not in [';' , '=' , '9' , '?']:
			self.acdc = ''
		if AC == True and DC == True:
			raise "ERROR: Device in AC and DC mode"
	
	def __multup__(self, value):
		prefix = ['','m','u','n','p','f','a']
		i = 0
		while value != 0 :
			if value*1000 < 1000: 
				value *= 1000
				i += 1
			else:
				break
		return value, prefix[i]
		
	def __multdown__(self, value):
		prefix = ['','k','M','G','T','P','E']
		i = 0
		while value != 0:
			if value > 1e3: 
				value /= 1000.0
				i += 1
			else:
				break
		return value, prefix[i]
		

	def eng_format(self,value):
		if value > 1000.0:
			return self.__multdown__(value)		
		else:			
			return self.__multup__(value)		
		
	def battery_status(self):
		if self.status_byte & 1<<1:
			print "Battery low!"
		else: print "Battery OK"

	def read(self):
		self.__read_data()
		self.__range()
		self.__sign()
		self.__unit()
		self.__acdc()
		if not self.overload:
			return self.value
		else:
			return self.overload_string
			
	def read_string(self):
		self.__read_data()
		self.__range()
		self.__sign()
		self.__unit()
		self.__acdc()
		value, prefix = self.eng_format(self.value)
		if not self.overload:
			return "%2s %3.1f %s%s"%(self.acdc, value, prefix, self.unit)
		else:
			return self.overload_string

if __name__ == '__main__':
    print "WARNING! No production code! "*2
    import matplotlib
    matplotlib.use('TkAgg')
    matplotlib.interactive('True')
    import sys
    import time
    import pylab
    a = PeakTech3315()
    f = open('coleman.dat','w')
    start_time = time.time()
    start_time_str = time.strftime("%H:%M:%S", time.localtime(start_time))
    temp = []
    secs = []
    fig = pylab.figure()
    temp_plot = fig.add_subplot(111)
    temp_plot.set_xlabel('Elapsed Time/s since %s'%start_time_str)
    temp_plot.set_ylabel('Temperature/*C')
    temp_plot.set_title('PeakTech 3315')
    for i in xrange(int(sys.argv[1])):
        curr_time = time.time()-start_time
        b = a.read()
        # 
        if b != 'overload':
            temp.append(b)
        secs.append(curr_time)
        print time.strftime("%H:%M:%S", time.gmtime(curr_time)), b
        f.write('%s %f\n'%(curr_time, b))
        f.flush()
        if i%10 == 0:
            pylab.ioff()
            if i > 0:
                temp_plot.lines.pop(0)
            temp_plot.plot(secs,temp,'b-')
            pylab.ion()
            pylab.draw()
        #time.sleep(1)
    f.close()
