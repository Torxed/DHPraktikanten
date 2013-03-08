#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

## Import custom modules
from config import core
from queueing import *
from logger import *
import traceback
import twitterapi
import ircapi
#import skypeapi
import mailapi
import ccoapi
import backend

## Import Python specifics
import asyncore, base64
from getpass import getpass
from threading import enumerate
from shutil import copy2 as copy
from time import sleep, ctime
from os import getpid, remove, system, walk
from os import _exit as exit
from os.path import isfile, getmtime, abspath
from pickle import load
from Crypto.Cipher import AES
from helpers import *

# On Windows, hide all the .pyc files:
# (They give me the hibigeebies)
#system('attrib +H *.pyc /S')

## ==== TODO
## * Replace the simple socket with a asyncronous socket! (irc.py got one)
## * Fix syntax everywhere, it's nasty!
## * Add proper OAUTH support for crew.dreamhack.se
## * Add IRC support? (irc.py is import friendly)
## * Consistency in the syntax, when recieving a command it should be x::y::z::list1;list2;list3
## * When accessing a db item, ANYTHING in core, access it through a get/set function
##   (the reason for this is to make sure that self.core['flags']['dblock'] is checked!)

pidfile = '/var/tmp/praktikanten.pid'
#pidfile = './praktikanten.pid'

if isfile(pidfile):
	#log('Dreamhack Praktikanten is already running!', 'Core')
	fh = open(pidfile)
	thepid = fh.read()
	fh.close()
	thepid = int(thepid)
	if pid_exists(thepid):
		exit(1)
	else:
		log('Removed the PID file, dead session!', 'Core')
		remove(pidfile)

__password__ = getpass('Enter the master password: ')

log('Initiating')

for i in range(0, 2):
	if isfile('dh_database.db'):
		f = open('dh_database.db', 'rb')
		try:
			core['pickle'] = load(f)
			log('Loaded a stored database!')
		except:
			if i == 0:
				newest = None
				for root, dirs, files in walk('./db_backups/'):
					for f in files:
						absfpath = abspath(root + '/' + f)
						if not newest:
							newest = (absfpath, getmtime(absfpath))
						else:
							curftime = getmtime(absfpath)
							if curftime >= newest[1]:
								newest = (absfpath, curftime)
				if newest:
					copy(newest[0], './dh_database.db')
					log ('Loaded a backup database (' + newest[0][newest[0].rfind('/'):] + '), last modified: ' + ctime(newest[1]), 'Core')
			else:
				log('Can not load dh_database.db, backup and main is broken!', 'Core')
			exit(666)
		f.close()
		break

core['pickle_ignore']['password'] = __password__

## Decrypt loaded encrypted passwords
## (so that the modules can use it)
#core['email']['user'] = decrypt(core['email']['user'])
#core['email']['pass'] = decrypt(core['email']['pass'])

def parser(source, identifier, msg, respond = None):
	log('Parsing: ' + identifier + ' - ' + str(len(msg)), source)
	## Append everything sad from identifier into a conversation log.
	if not identifier in core['pickle']['conversation']:
		core['pickle']['conversation'][identifier] = ''
	if not identifier in core['pickle']['stored_conversations']:
		core['pickle']['stored_conversations'][identifier] = []
	core['pickle']['conversation'][identifier] = core['pickle']['conversation'][identifier] + msg + '\n'
	
	ret = msg

	for item in ('problem with', 'problem med', 'min dator startar inte'):
		if item in core['pickle']['conversation'][identifier].lower():

			if not identifier in core['pickle']['conversation']:
				break

			for t in ('hardware', 'hårdvara'):
				if t in core['pickle']['conversation'][identifier].lower():
					placeinqueue = core['pickle_ignore']['queue'].add(source, identifier, ('hardware', core['pickle']['conversation'][identifier]))
					core['pickle']['stored_conversations'][identifier].append(core['pickle']['conversation'][identifier])
					del core['pickle']['conversation'][identifier]
					ret = 'Ok your place in the queue is: ' + str(placeinqueue[0]) + '! The ETA is roughly ' + str(placeinqueue[1])
					break

			if not identifier in core['pickle']['conversation']:
				break

			for t in ('software', 'mjukvara'):
				if not identifier in core['pickle']['conversation']:
					break
				if t in core['pickle']['conversation'][identifier].lower():
					placeinqueue = core['pickle_ignore']['queue'].add(source, identifier, ('hardware', core['pickle']['conversation'][identifier]))
					core['pickle']['stored_conversations'][identifier].append(core['pickle']['conversation'][identifier])
					del core['pickle']['conversation'][identifier]
					ret = 'Ok your place in the queue is: ' + str(placeinqueue[0]) + '! The ETA is roughly ' + str(placeinqueue[1])
					break

			if ret == msg:
				ret = 'Which type of problem is this? (hardware or software): '
		if not identifier in core['pickle']['conversation']:
			break

	if respond and ret != msg:
		respond.send(ret)
	else:
		return True

core['pickle_ignore']['parser'] = parser
#core['pickle_ignore']['twitter'] = twitterapi.twitt(['#DHSupport',])
#core['pickle_ignore']['irc'] = ircapi.irc({'password' : __password__})
core['pickle_ignore']['backend'] = backend.main()
core['pickle_ignore']['queue'] = queue()
#core['pickle_ignore']['skype'] = skypeapi.Skype()
core['pickle_ignore']['email'] = mailapi.Mail()
core['pickle_ignore']['cco'] = ccoapi.CCO()

garbageman = __import__('cycle')
garbagehandle = garbageman.garbageman(core)
garbagehandle.start()

pid = getpid()
f = open(pidfile, 'wb')
f.write(str(pid))
f.close()

log('All instances started!')
core['pickle_ignore']['queue'].add('irc', 'DoXiD', ('hardware', 'DoXiD just has issues..'))
core['pickle_ignore']['queue'].add('irc', 'Yamakazi', ('software', 'Yamakazi can not play Dota2'))
core['pickle_ignore']['queue'].add('irc', 'Summalajnen', ('software', 'Summalajnen has some issues with CS'))

try:
	while 1:
		sleep(1)
except:
	pass
log('Exiting','Core')
remove(pidfile)

for t in enumerate():
	try:
		t._Thread__delete()
	except:
		pass

exit(0)
