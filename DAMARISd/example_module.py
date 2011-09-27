import numpy as N
import time

# these modules are mandatory
import xmlrpclib
import cPickle
	
def doit(server, device, args):
	"""
	args is a list of arguments from the configuration file
	
	 Example:
	
	 [python_mod]
	 module = test_mod
	 args = ['http://localhost:%s'%port,'python1']
	 
	 server and device are given by the server
	"""
	# First we need to register our client
	server.register_client(device)
	Quit = False
	while not Quit: # repeat until the server tells us to quit
		Quit = bool(server.quit_client(device)) # should this client quit?
		if not server.occupied(device): # should this client wait?
			# run your stuff here
			# here we create random data
			# pickle the data because xmlrpc accepts only strings,floats,bool,None or lists
			data = cPickle.dumps(N.random.randn(1),  protocol=0)
			# put the data
			server.put_data(device, time.time(), data)
			# wait 1 second
			time.sleep(1)
	# We quitted so we unregister our client
	server.unregister_client(device)
	print "Quitted: %s"%device
	
