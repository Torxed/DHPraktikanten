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
from time import sleep
from os import getpid, remove, system
from os import _exit as exit
from os.path import isfile
from pickle import load
from Crypto.Cipher import AES
from helpers import *

# On Windows, hide all the .pyc files:
# (They give me the hibigeebies)
system('attrib +H *.pyc /S')

## ==== TODO
## * Replace the simple socket with a asyncronous socket! (irc.py got one)
## * Fix syntax everywhere, it's nasty!
## * Add proper OAUTH support for crew.dreamhack.se
## * Add IRC support? (irc.py is import friendly)
## * Consistency in the syntax, when recieving a command it should be x::y::z::list1;list2;list3
## * When accessing a db item, ANYTHING in core, access it through a get/set function
##   (the reason for this is to make sure that self.core['flags']['dblock'] is checked!)

#pid = '/var/tmp/praktikanten.pid'
pidfile = './praktikanten.pid'

if isfile(pidfile):
	log('Dreamhack Praktikanten is already running!', 'Core')
	exit(1)
__password__ = getpass('Enter the master password: ')

log('Initiating')

if isfile('dh_database.db'):
	f = open('dh_database.db', 'rb')
	try:
		core['pickle'] = load(f)
		log('Loaded a stored database!')
	except:
		log('!!! -> ERROR <- !!\n  can not load db', 'Core')
		_exit(666)
	f.close()

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
#core['pickle_ignore']['email'] = mailapi.Mail()
#core['pickle_ignore']['cco'] = ccoapi.CCO()

garbageman = __import__('cycle')
garbagehandle = garbageman.garbageman(core)
garbagehandle.start()

pid = getpid()
f = open(pidfile, 'wb')
f.write(str(pid))
f.close()

log('All instances started!')

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
