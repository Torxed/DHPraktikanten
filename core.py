#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import traceback
import twitterapi
import irc_core
import asyncore
from socket import *
from time import sleep
from os import _exit as exit
from os.path import isfile
from pickle import load

## ==== TODO
## * Replace the simple socket with a asyncronous socket! (irc.py got one)
## * Fix syntax everywhere, it's nasty!
## * Add proper OAUTH support for crew.dreamhack.se
## * Add IRC support? (irc.py is import friendly)
## * Consistency in the syntax, when recieving a command it should be x::y::z::list1;list2;list3
## * When accessing a db item, ANYTHING in core, access it through a get/set function
##   (the reason for this is to make sure that self.core['flags']['dblock'] is checked!)

__password__ = raw_input('Enter the master password: ')

#s = socket()
#
#while 1:
#	try:
#		s.bind(('127.0.0.1', 8421))
#		break
#	except:
#		sleep(1)
#		continue
#print 'Listening!'
#s.listen(4)

rows = {}
for hall in ('A', 'B', 'C', 'D'):
	for i in range(1, 77):
		if not hall in rows:
			rows[hall] = {}
		power = True
		rows[hall][i] = {'power' : power, 'issues' : []}
core = {'pickle' : {}}
if isfile('dh_database.db'):
	f = open('dh_database.db', 'rb')
	try:
		core['pickle'] = load(f)
		print 'Loaded a stored database!'
	except:
		print '!!! -> ERROR <- !!!'
		print '  can not load db'
		_exit(666)
	f.close()

if not 'rows' in core['pickle']:
	core['pickle']['rows'] = rows
if not 'prio' in core['pickle']:
	core['pickle']['prio'] = []
if not 'powerissues' in core['pickle']:
	core['pickle']['powerissues'] = []

if not 'flags' in core['pickle']:
	core['pickle']['flags'] = {'dblock' : False}

core['pickle']['quickpicks'] = {
	1 : {'title' : 'PC doesn\'t boot at all',
			'type' : 'hardware',
		},
	2 : {'title' : 'PC Boots but no image',
			'type' : 'hardware',
		},
	3 : {'title' : 'Cleaning (dusty PC)',
			'type' : 'hardware',
		},
	4 : {'title' : 'Software issue (game issue etc)',
			'type' : 'software',
		},
	5 : {'title' : 'Hardware issue (weird image}, computer creashes etc)',
			'type' : 'hardware',
		},
	6 : {'title' : 'Network issue (Bad or No connection at all)',
			'type' : 'software',
		},
	7 : {'title' : 'Upgrade or Change in PC parts (hardware)',
			'type' : 'hardware',
		},
	8 : {'title' : 'I have no idea what i\'m doing?!',
			'type' : 'software',
		},
	0 : {'title' : 'Other stuff',
			'type' : 'other',
		},
}

core['pickle']['supportscheme'] = {
	'00' : {'end' : '08', 'tech' : ('aSyx', 'MiniErrA')},
	'04' : {'end' : '12', 'tech' : ('ventris', 'vizze')},
	'08' : {'end' : '16', 'tech' : ('Backeman', 'MattiasLj', 'Triggerhappy')},
	'12' : {'end' : '20', 'tech' : ('Fughur', 'jalkmar', 'Käkben', 'level', 'Prozack')},
	'16' : {'end' : '00', 'tech' : ('DD_Rambo', 'Donkey', 'fozzie', 'SUMMALAJNEN')},
	'20' : {'end' : '04', 'tech' : ('DoXiD', 'Exxet', 'Jannibal', 'Miwca')}
}

core['pickle']['supportcases'] = []

core['pickle_ignore'] = {}
core['pickle_ignore']['twitter'] = twitterapi.twitt(['#DHSupport',])
core['pickle_ignore']['irc'] = irc_core.irc({'password' : __password__})
#core['pickle_ignore']['twitter'].post("I just fired up my twitter engine to take it for a spin!")

garbageman = __import__('cycle')
garbagehandle = garbageman.garbageman(core)
garbagehandle.start()

try:
	while 1:
		sleep(1)
except:
	pass
print 'Exiting'
#while 1:
#	try:
#		ns, na = s.accept()
#		clientmodule = __import__('clientmodule')
#		reload(clientmodule)
#		ch = clientmodule.clienthandle(ns, na, core)
#		ch.start()
#	except KeyboardInterrupt:
#		break
#	except Exception, e:
#		print e.message
#		print traceback.format_exc()
#		continue
#s.close()
exit(0)
