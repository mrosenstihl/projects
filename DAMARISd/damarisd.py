import tables as T
import numpy as N
import subprocess
import threading
import SimpleXMLRPCServer
import SocketServer
import time,xmlrpclib,httplib
import cPickle as pickle
import ConfigParser
import sys, os
import imp


# xmlrpc mit timeout

def Server(url, *args, **kwargs):
   t = TimeoutTransport()
   t.timeout = kwargs.get('timeout', 60)
   if 'timeout' in kwargs:
       del kwargs['timeout']
   kwargs['transport'] = t
   server = xmlrpclib.Server(url, *args, **kwargs)
   return server

class TimeoutTransport(xmlrpclib.Transport):

   def make_connection(self, host):
       conn = TimeoutHTTP(host)
       conn.set_timeout(self.timeout)
       return conn
       
class TimeoutHTTPConnection(httplib.HTTPConnection):

   def connect(self):
       httplib.HTTPConnection.connect(self)
       self.sock.settimeout(self.timeout)


class TimeoutHTTP(httplib.HTTP):
   _connection_class = TimeoutHTTPConnection

   def set_timeout(self, timeout):
       self._conn.timeout = timeout

# Create server
# SocketServer.ThreadingMixIn, 	SimpleXMLRPCServer.SimpleXMLRPCServer
#class ThreadingXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer): pass
class ThreadingXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer): pass
#class ThreadingXMLRPCServer(SocketServer.ThreadingTCPServer, SimpleXMLRPCServer.SimpleXMLRPCServer): pass


#class ThreadingXMLRPCServer(SocketServer.TCPServer, SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
#	def __init__(self, addr, requestHandler = SimpleXMLRPCServer.SimpleXMLRPCRequestHandler, logRequests = 0): 
#		self.logRequests = logRequests 
#		if sys.version_info[:2] < (2, 5): 
#			SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self) 
#		else: 
#			SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self, allow_none = False, encoding = None) 
#		SocketServer.ThreadingTCPServer.__init__(self, addr, requestHandler) 
#	pass

# The Damaris Logger Daemon
class DamarisLogger:
	def __init__(self, data_file, max_puts_before_flush,port):
		#print os.getcwd()
		self.hdf = T.openFile(data_file,'a')
		self.run_flag = True
		self.server = ThreadingXMLRPCServer(("localhost", port), logRequests=0)
		self.server.allow_reuse_address = True
		self.server.allow_none = True
		self.server.allow_introspection = True
		
		self.server.register_introspection_functions=True
		self.server.register_function(self.put_data)	
		self.server.register_function(self.get_data)
		self.server.register_function(self.put_external_data)
		self.server.register_function(self.unblock_client)
		self.server.register_function(self.block_client)
		self.server.register_function(self.occupied)
		self.server.register_function(self.quit)
		self.server.register_function(self.quit_client)
		self.server.register_function(self.status)
		self.server.register_function(self.register_client)
		self.server.register_function(self.unregister_client)
		self.server.register_function(self.quit_device)
		self.server.register_function(self.server_run)
		
		self.puts = 0
		self.total_puts = 0
		self.block_list = set()
		self.quit_list = set()
		self.quit_client_flag = False
		self.client_list = set()
		self.max_puts_before_flush = max_puts_before_flush
		self.lock = threading.Lock()

	def __del__(self):
		try:
			print "closing files ..."
			self.hdf.flush()
			self.hdf.close()
		except:
			print "Could not close files, sorry!"

	def register_client(self,device):
		self.client_list.add(device)
		return None

	def unregister_client(self,device):
		self.client_list.remove(device)
		return None
	
	def flushing(self):
		self.lock.acquire()
		if self.puts >= self.max_puts_before_flush:	
			self.hdf.flush()
			self.puts = 0
		self.lock.release()
		return None
			
	def server_run(self):
		return self.run_flag
		
	def quit(self):
		#self.run_flag = False
		self.quit_client_flag = True
		i = 0
		while (i < 10) and not len(self.client_list) == 0:
			i += 1
			print "Clients still running ...", self.client_list
			time.sleep(0.5)
		self.__del__()
		self.run_flag = False
		return None

	def status(self):
		self.flushing()
		return self.total_puts, list(self.client_list), list(self.block_list)

	def quit_device(self,device):
		"""
		Tell client 'device' to quit
		"""
		self.quit_list.add(device)
		return None
########  client controls ###############
	def quit_client(self, device):
		"""
		Should the client 'device' quit?
		"""
		if device in self.quit_list:
			self.quit_list.remove(device)
			return True
		if self.quit_client_flag:
			return self.quit_client_flag
	
	def occupied(self,device):
		if device in self.block_list:
			return True
		else:
			return False
			
	def block_client(self,device):
		self.block_list.add(device)
		return None
		
	def unblock_client(self,device):
		self.block_list.remove(device)
		return None
		
########################################


	def run(self):
		"""
		This function is starting the server and registering the needed functions
		"""
		print "Server up and running ..."
		while self.run_flag:
			self.server.handle_request()

	def put_external_data(self, device, command):
		"""
		Reads  data from an external (shell) command
		"""
		record_time = time.time()
		external = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		in_data = external.stdout.readline()
#		result = map(float, in_data.strip().split(' '))
#		Much faster!
		result = N.fromstring("".join(in_data), sep=' ')
		self.put_data(device, record_time, result)
		return 1

	def put_data(self, device, record_time, data):
		"""
		Put in data via an external program. The program should connect to the
		DAMARISd daemon and issue this command.
		record_time is a list of timestamps, from for example time.time().
		value is a cPickle.dumps(numpy.array), each row corresponds to a
		time stamp
		"""
		def make_EArray(device,cols):
			try:
				self.hdf.root._g_checkHasChild(device) # throws NoSuchNodeError if not existing	
				device_array = self.hdf.getNode('/',device)
			except T.exceptions.NoSuchNodeError:
				device_array = self.hdf.createEArray('/',device, 
									atom=T.Float64Atom(), 
									shape=(0,cols+1))
			return device_array
		
		# Check the type of record_time, we need one dimensional data
		if type(record_time) != list:
			# if a numpy array
			if type(record_time) == N.ndarray:
				if all(record_time.shape) > 1:
					# we need one dimensional time data, thus flatten
					record_time = record_time.flatten()
			# not a numpy array, make a list out of it
			#else:
			#	record_time = list(record_time)

		# Data comes from outside client via xmlrpclib
		if type(data) == str:
			data = pickle.loads(data)
		
		# rows, cols for creating the pytables array
		rows_cols = data.shape
		
		# is one dimension
		if len(rows_cols) == 1:
			rows = 1
			cols = rows_cols[0]
			
		# is two dimensinal
		if len(rows_cols) == 2:
			rows,cols = rows_cols
		else:
			# todo error handling
			pass
		device_array = make_EArray(device,cols)
		rows = N.empty((rows,cols+1))
		rows[:,0]=record_time
		rows[:,1:]=data
		try:
			device_array.append(rows)
		except:
			print "ERROR! Quitting client: %s"%device
			self.quit_device(device)
		# update puts, flush if necessary
		self.lock.acquire()
		self.total_puts += 1
		self.puts += 1
		self.lock.release()
		self.flushing()
		return None

	def search(self,anarray,value,start=None,stop=None):
		"""
		Binary search, needs ~ 23 iterations for 12e6 records
		"""
		Found = False	
		
		if start == None:
			start = 0
		if stop == None:
			stop = anarray.shape[0]
		bisect = (stop+start)/2
		current_point = anarray.read(start=bisect)[:,0]
	
		while not Found:
			if  value < current_point:
				stop = bisect-1
			elif value > current_point:
				start = bisect+1
				# can't go higher
				if start >= anarray.shape[0]:
					start=bisect
	
			bisect = (stop+start)/2 
			if bisect >= anarray.shape[0]:
				bisect = anarray.shape[0]
			if bisect < 0:
				bisect = 0
			current_point = anarray.read(start=bisect)[:,0]
			if start >= stop:
				Found = True
		return bisect

	def get_data(self, device, start_time, stop_time):
		self.hdf.flush()
		device_array = self.hdf.getNode('/',device)
		# select the values in timeframe
		# This is very inefficient
		#tmp = [ x[:] for x in device_array.iterrows() 
		#						if (start_time <= x[0] <= stop_time) ]
		#values_to_return = N.empty((len(tmp), len(tmp[0])))
		#for i,row in enumerate(tmp):
		#	values_to_return[i,:]=row

		# using binary search
		start_point = self.search(device_array,start_time)
		# don't search the whole thing again, start at start_point
		end_point = self.search(device_array,stop_time, start = start_point-1)
		#print start_point, end_point,device
		if start_point == end_point:
			values_to_return = device_array.read(start_point)
		else:
			values_to_return = device_array.read(start_point, end_point)
		return_object = pickle.dumps(values_to_return, protocol=0)
		return return_object




def damarisd_daemon():
	s = "%s Starting server"%(time.ctime())
	print
	print len(s)*"#"
	print s
	print len(s)*"#"
	############ GENERAL CONFIGURATION PART ###################
	
	config = ConfigParser.ConfigParser()
	config.read('damarisd.config')
	devices = [sec for sec in config.sections()]# if sec!="general"]
	data_file = config.defaults()['data_file']
	max_puts_before_flush = int(config.defaults()['max_puts_before_flush'])
	port = int(config.defaults()['port'])
	
	# log the config
	for sec in config.sections():
		print "Device: %s"%sec
		for pair in sorted(config.items(sec)):
			keys,val = pair
			print "\t%s = %s"%pair
	############## SERVER PART ######################
	damarisd_server = DamarisLogger(data_file,max_puts_before_flush,port)
	daemon = threading.Thread(target = damarisd_server.run)
	daemon.setDaemon(True)
	daemon.start()
	# move this to background daemon.run()
	time.sleep(0.1)

	server = Server('http://localhost:%i'%port)

	
	######### CLIENT PART ############
	
	def shelldevice_thread(device, command,rate):
		Quit = False
		#server = xmlrpclib.Server('http://localhost:%i'%port)
		server.register_client(device)
		while not Quit:
			Quit = bool(server.quit_client(device))
			if server.occupied(device) == 0:
				server.put_external_data(device, command)
				time.sleep(rate)
		server.unregister_client(device)
	
	def pydevice_thread(device, module, arg_list):
		"""
		Python module interface.
		All the logic has to be in the client module.
		On start:
		a) server.register_client(device)
		b) server.put_data
		c) check server.occupied
		d) check server.quit_client flag
		
		On quitting:
		a) last transmission
		b) server.unregister_client(device)
		"""
		fm = imp.find_module(module)
		mod = imp.load_module(module, fm[0],fm[1],fm[2])
		mod.doit(server, device, arg_list)
		
	# start the device logger
	# distinguish between shell commands and python scripts
	################### CLIENT CONFIGURATION ###########################
	shelldevices = [dev for dev in devices if config.has_option(dev,'command')]
	pydevices    = [dev for dev in devices if config.has_option(dev,'module')]
	for device in shelldevices:
		command = 	config.get(device,'command')
		rate 	= 	config.getfloat(device,'rate')
		cmd = threading.Thread(target = shelldevice_thread, args = (device,command,rate))
		cmd.setName("Thread_%s"%device)
		cmd.setDaemon(True)
		cmd.start()

	for device in pydevices:
		module = 	config.get(device,'module')
		argument_list 	= 	eval(config.get(device,'args'))
		#print argument_list
		cmd = threading.Thread(target = pydevice_thread, args = (device,module,argument_list))
		cmd.setName("Thread_%s"%device)
		cmd.setDaemon(True)
		cmd.start()

		

	# endless loop
	run = True
#	server = xmlrpclib.Server('http://localhost:8002')
	while run:
		time.sleep(2)
		try:
			run = server.server_run()
		except:
			run = False
		pass

	

# DAMONIZE from chris python page

#!/usr/bin/env python


###########################################################################
# configure UID and GID of server
UID = 501
GID = 501


# configure these paths:

LOGFILE = '/Users/markusro/Projects/DAMARISd/damarisd.log'
PIDFILE = '/Users/markusro/Projects/DAMARISd/damarisd.pid'


# and let USERPROG be the main function of your project

USERPROG = damarisd_daemon

###########################################################################


#based on Juergen Hermanns http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012


class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()

def main():

    #change to data directory if needed
    os.chdir("/Users/markusro/Projects/DAMARISd")

    #redirect outputs to a logfile
    sys.stdout = sys.stderr = Log(open(LOGFILE, 'a+'))

    #ensure the that the daemon runs a normal user
    #os.setegid(GID)     #set group first "pydaemon"
    #os.seteuid(UID)     #set user "pydaemon"

    #start the user program here:

    USERPROG()


if __name__ == "__main__":
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")   #don't prevent unmounting....
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid
            open(PIDFILE,'w').write("%d"%pid)
            sys.exit(0)
            print "Daemon PID %d" % pid
    except OSError, e:
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # start the daemon main loop
    main()
