#!/usr/bin/env python
#Developed for ETSZONE (etszone.com) by Diego Ongaro, 2005
#This file is in the public domain but please keep the above credits.

JABBER_USER_DIR = '/var/lib/jabber/dozor.fkp.physik.tu-darmstadt.de/' #needs a trailing slash
JABBER_USER_UID = 115   #numeric user-id
JABBER_USER_GID = 65534     #numeric group-id
JABBER_USER_MOD = 0600  #numeric mode

import base64, sha, time, os

def sha_hash(pw): 
	"""Returns a SHA hash of the given text."""
	return '{SHA}' + base64.encodestring(sha.new(pw).digest()).rstrip()

def get(label): #
	"""Returns user input (stdin), prompting user with given text."""
	return raw_input('%s: ' % label).strip()
	

user = get('username')

filename = '%s%s.xml' % (JABBER_USER_DIR, user)
if os.path.exists(filename):
	print 'ERROR: username exists'
	os.sys.exit(1)
else:
	pw = get('password')
	name = get('name')
	email = get('email')

	add_to_file = \
	"<xdb>" + \
		"<query xmlns='jabber:iq:last' last='%i' xdbns='jabber:iq:last'>Registered</query>" % time.time() + \
		"<crypt xmlns='jabber:iq:auth:crypt' xdbns='jabber:iq:auth:crypt'>%s</crypt>" % sha_hash(pw) + \
		"<query xmlns='jabber:iq:register' xdbns='jabber:iq:register'>" + \
			"<username>%s</username>" %user + \
			"<name>%s</name>" % name + \
			"<email>%s</email>" % email + \
		"</query>" + \
	"</xdb>"
	
	f = open(filename, 'w')
	f.write(add_to_file)
	f.close()
	os.chown(filename, JABBER_USER_UID, JABBER_USER_GID)
	os.chmod(filename, JABBER_USER_MOD)
