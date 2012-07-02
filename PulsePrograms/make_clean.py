#!/usr/bin/env python
import os

print "Cleaning directory %s"%(os.path.realpath('.'))
rubbish_filetypes = ('h5','hdf','.dat','.pyc', '.png', '.pdf', '.tar.gz')
rubbish_startnames = ('job','logdata','Amplitude','Real','spool','pool')
choosing = raw_input("Continue [yes/anykey_for_NO] ?")
if choosing == 'yes':
	print "Cleaning directory"
	for root,dir,files in os.walk('.'):
		if dir != ".bzr":
			print dir
			for  file in files:
				print file,
				if file.endswith(rubbish_filetypes) or file.startswith(rubbish_startnames):
					delete_file  = os.path.join(root,file)
					os.remove(delete_file)
					print "...delete"
				else:
					print "...skipped"

print "finnished"
		
