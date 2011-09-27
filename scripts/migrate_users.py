#!/usr/bin/env python
"""
This script is needed because we do not want to do NIS on our shared netwark.

TODO:
    Use adduser (with password?)
    Option to copy existing /home/$USER
    Option to migrate from one host to another host
    Fix permissions for all users
"""
from __future__ import with_statement
import tempfile
import os,sys
from optparse import OptionParser
from socket import gethostname
try:
    from paramiko import *
except:
    print "ERROR: Install paramiko: aptitude install python-paramiko"
    sys.exit(1)
# first, extract all the users from passwd file


FIRST_UID = 1000
LAST_UID = 29999



parser = OptionParser()
parser.add_option("-H", "--host", dest="host",
                  help="migrate user account to HOST", metavar="HOST")
parser.add_option("-d", "--debug",
                  action="store_true", dest="debug", default=False,
                  help="debug output, do not modify HOST")

(options, args) = parser.parse_args()


DEBUG = options.debug

if not options.host:
    parser.error("Hostname not given")

else:
    print "Migrate users to %s"%(options.host) 
    
# Make sure we are not updating dozor, or ourself
if ( options.host.lower().find(gethostname()) ) >= 0:
    print "ERROR: Won't update myself %s"%(gethostname())
    sys.exit(1)

if os.getuid() != 0:
    "ERROR: You need to be root!"

try:
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(options.host)
    client.close()

except (AuthenticationException, SSHException), e:
    print "ERROR:",e
    print """you need to add your ssh key to the remote host: 
    man ssh-copy-id 
    man ssh-keygen
    """
    sys.exit(1)

class UserData:
    def __init__(self, host=""):
        
        self.source_passwd = {}
        self.source_shadow = {}
        self.source_group = {}

        self.source_member = {}

        self.remote_passwd = {}
        self.remote_shadow = {}
        self.remote_group = {}
        

        self.get_passwd()
        self.get_remote_passwd(host)
        self.get_shadow()
        self.get_group()
        self.check_uid()

    def get_passwd(self):
        print "Load local /etc/passwd"
        f = open("/etc/passwd")
        passwd_dict = {}
        for line in f.readlines():
            login,passwd,uid,guid,comment,home,shell = line.strip().split(':')
            if FIRST_UID <= int(uid) <= LAST_UID:
                passwd_dict[login]=line.strip().split(':')
        f.close()
        self.source_passwd = passwd_dict


    def get_remote_passwd(self, host):
        print "Load remote /etc/passwd"
        client = SSHClient()
        client.load_system_host_keys()
        client.connect(host)
        command = "cat /etc/passwd"
        #print "%s: %s"%(host,command)
        stdin,stdout,stderr = client.exec_command(command)
        passwd_dict = {}
        for line in stdout.readlines():
            login,passwd,uid,guid,comment,home,shell = line.split(':')
            if FIRST_UID <= int(uid) <= LAST_UID:
                passwd_dict[login]=line.strip().split(':')
        self.remote_passwd = passwd_dict

    def get_shadow(self):
        print "Load local /etc/shadow"
        shadow_dict = {}
        for line in open('/etc/shadow'):
            shadow = line.strip().split(':')
            login = shadow[0]
            shadow_dict[ login ] =line.strip().split(':') 
        self.source_shadow = shadow_dict

    def get_group(self):
        print "Load local /etc/group"
        for line in open('/etc/group'):
            group,x,gid,members = line.strip().split(':')
            self.source_group[group] =line.strip().split(':') 
            if members:
                for user in self.source_passwd.keys():
                    if user in members.split(','):
                        if user in self.source_member.keys():
                            self.source_member[user].append(group)
                        else:
                            self.source_member[user] = [group]
    def check_uid(self):
        print "checking for matching UIDs ..."
        mismatch_found = False
        for user in sorted(self.source_passwd.keys()):
            uid = self.source_passwd[user][2]
            remote_users = self.remote_passwd.keys()
            for rm_user in sorted(remote_users):
                rm_uid = self.remote_passwd[rm_user][2]
                if uid != rm_uid and user==rm_user:
                    mismatch_found = True
                    print "ERROR: UID mismatch: %s (%s) -> %s (%s)"%(user,
                                uid, rm_user, rm_uid)
        if mismatch_found:
            raise ValueError, "UIDs do not match"
        else:
            print "... done"

def write_remote_passwd(host, users):
    print "Writing remote /etc/passwd"
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(host)
    
    command = "cp -v /etc/passwd /etc/passwd.backup"
    #print "%s: %s"%(host,command)
    stdin,stdout,stderr = client.exec_command(command)
    print "%s: %s"%(host,stdout.read())
    err = stderr.read()
    if err != "":
        print "%s: %s"%(host,err)


    sftp  = client.open_sftp()
    local = tempfile.mktemp(".%s"%host)
    sftp.get('/etc/passwd', local)
    to_write = [":".join(data.source_passwd[login])+"\n" for login in users]
    f = open(local, 'a')
    f.writelines(to_write)
    f.close()
    if not DEBUG:
        sftp.put( local, '/etc/passwd')
        os.remove( local )
    else:
        print "---passwd---"*3
        print open(local).read()


def write_remote_group(host, users):
    print "Writing remote /etc/group"
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(host, timeout=1)
    
    command = "cp -v /etc/group /etc/group.backup"
    #print "%s: %s"%(host,command)
    stdin,stdout,stderr = client.exec_command(command)
    print "%s: %s"%(host,stdout.read())
    err = stderr.read()
    if err != "":
        print "%s: %s"%(host,err)

    local = tempfile.mktemp(".%s"%host)
    sftp  = client.open_sftp()
    sftp.get('/etc/group',local ) 
    to_write = [":".join(data.source_group[login])+"\n" for login in users]
    f = open(local, 'a')
    f.writelines(to_write)
    f.close()
    if not DEBUG:
        sftp.put( local, '/etc/group')
        os.remove( local )
    else:
        print "---group---"*3
        print open(local).read()
    for login in users:
        if login in data.source_member.keys():
            groups = data.source_member[login]
            #ishell = client.invoke_shell()
            # TODO use a interactive shell, do not open new connections
            for group in groups:
                command = "adduser %s %s"%(login, group)
                #print "%s: %s"%(host,command)
                stdin,stdout,stderr = client.exec_command(command)
                print "%s: %s"%(host,stdout.read())
                err = stderr.read()
                if err != "":
                    print "%s: %s"%(host,err)

def write_remote_shadow(host, users):
    print "Writing remote /etc/shadow"
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(host)
    
    command = "cp -v /etc/shadow /etc/shadow.backup"
    #print "%s: %s"%(host,command)
    stdin,stdout,stderr = client.exec_command(command)
    print "%s: %s"%(host,stdout.read())
    err = stderr.read()
    if err != "":
        print "%s: %s"%(host,err)

    sftp  = client.open_sftp()
    local = tempfile.mktemp(".%s"%host)
    sftp.get('/etc/shadow', local)
    to_write = [":".join(data.source_shadow[login])+"\n" for login in users]
    f = open(local, 'a')
    f.writelines(to_write)
    f.close()
    if not DEBUG:
        sftp.put( local, '/etc/shadow')
        os.remove( local )
    else:
        print "---shadow---"*3
        print open(local).read()


def create_homes(host, users):
    print "Create remote /home/USER"
    for user in users:
        client = SSHClient()
        client.load_system_host_keys()
        client.connect(host)
        
        command = "mkdir -v --mode=755 /home/%s"%user
        #print "%s: %s"%(host,command)
        stdin,stdout,stderr = client.exec_command(command)
        print "%s: %s"%(host,stdout.read())
        err = stderr.read()
        if err != "":
            print "%s: %s"%(host,err)

        command = "chown -v %s:%s /home/%s"%(user,user,user)
        #print "%s: %s"%(host,command)
        stdin,stdout,stderr = client.exec_command(command)
        print "%s: %s"%(host,stdout.read())
        err = stderr.read()
        if err != "":
            print "%s: %s"%(host, err)

data = UserData(options.host)
users = sorted(data.source_passwd.keys())

user_add = []
user_ignore = ['cluster-admin','ianus', 'heckmann', 'stephan']
user_exist_remote = []

for user in users:
    if user not in data.remote_passwd.keys(): # user not on remote system
        if user in data.source_shadow.keys(): # user has a local shadow passwd
            if user not in user_ignore: # user to be ignored
                user_add.append(user)
        else:
            user_ignore.append(user)
    else:
        user_exist_remote.append(user)
        user_ignore.append(user)


header = "| %16s | %6s | %3s | %3s |"%("User","Remote","Add", "Ign")
print "+"*len(header)
print header
print "+"*len(header)
for user in users:
    rm = ""
    add = ""
    ign = ""
    if user in user_add:
        add = "#"
    if user in user_exist_remote:
        rm ="#"
    if user in user_ignore:
        ign ="#"
    print "| %16s | %6s | %3s | %3s |"%(user,rm,add, ign)
    # following requires Python 2.6
    #row =  "{20s} | {6s} | {^3s} | {3s}".format(user,rm,add, ign)
    #print row
print "+"*len(header)

if user_add is not []:
    update = raw_input("Do you want to proceed for %s? [y/N]"%(options.host))
    if update.lower() == "y":
        write_remote_passwd(options.host,user_add)
        write_remote_group(options.host,user_add)
        write_remote_shadow(options.host,user_add)
        create_homes(options.host,user_add)
    else:
        print "Doing nothing. Bye!"



