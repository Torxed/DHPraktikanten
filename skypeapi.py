#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import sys
import json
import os
try:
	import Skype4Py
except ImportError, e:
	sys.stderr.write("""
It seems you have not yet installed Skype4Py. Install by running:
sudo easy_install Skype4Py
or
sudo pip install Skype4Py
		""")
	exit(1)
from threading import *
from time import sleep
from config import *
from logger import *


class SkypeCallback():
	def __init__(self, sock, channel):
		self.s = sock
		self.c = channel

	def send(self, what):
		self.s.SendMessage(self.c, what)

class Skype(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.alive = True

		self.s = None

		self.start()

	def selfCallback(self, m, channel):
		self.s.SenMessage(channel[0], m)

	def on_message(self, message, status):
		if status in ('SENDING', 'SENT', 'RECEIVED'):
			sender = message.Sender
			NickName = sender.Handle
			SenderStatus = sender.OnlineStatus
			SenderMobile = sender.PhoneMobile
			SenderAliases = sender.Aliases
			SenderFullName = sender.FullName

			chat = message.Chat
			ChatRoom = chat.Name
			ChatMembers = chat.Members

			text = message.Body

			out = {
				'NickName' : NickName.encode('iso-8859-15', 'replace'),
				'SenderStatus' : SenderStatus.encode('iso-8859-15', 'replace'),
				'SenderMobile' : SenderMobile.encode('iso-8859-15', 'replace'),
				'SenderAliases' : SenderAliases,
				'SenderFullName' : SenderFullName.encode('iso-8859-15', 'replace'),
				'ChatRoom' : ChatRoom.encode('iso-8859-15', 'ignore'),
				'Text' : text.encode('iso-8859-15', 'replace'),
			}

			if status == 'RECEIVED':
				#sys.stdout.write('[Skype] From: ' + out['NickName'] + '\n' + '    < ' + out['Text'] + ' (' + out['ChatRoom'] + ')\n')
				towho = None
				if '/' in out['ChatRoom']:
					towholist = out['ChatRoom'].split('/',1)
					for to in towholist:
						if len(to) <= 0: continue

						while to[0] in ('#', '$'):
							to = to[1:]
						if ';' in to:
							to, trash = to.split(';',1)
						if ':' in to:
							origin, to=to.split(':',1)

						if to.lower() in ('torxed', 'dhpraktikanten'):
							continue
						towho = to
						break

				if towho:
					h = SkypeCallback(self.s, towho)
					if core['pickle_ignore']['parser']('Skype', towho+'@skype', out['Text'], h) == True:
						pass
				else:
					log('Couldn\'t understand who i sent to...\n', 'Skype')
			#elif status == 'SENT':
			#	towho = None
			#	if '/' in out['ChatRoom']:
			#		towho = out['ChatRoom'].split('/',1)[0]
			#		if towho[0] == '#':
			#			towho = towho[1:]
			#	if towho:
			#		sys.stdout.write('    > Answered ' + towho + '\n')
			#		sys.stdout.write('    ! Trying to delete ' + out['ChatRoom'] + ' - ' + out['Text'] + '\n')
			#		sys.stdout.write('      ' + core['outqueue'][towho] + '\n')
			#		if out in core['outqueue'][towho][out['ChatRoom']]:
			#			del core['outqueue'][towho][out['ChatRoom']][out['Text']]
			#		else:
			#			sys.stdout('      Already deleted?\n')
			#	else:
			#		sys.stdout.write('Couldn\'t understand who i sent to...\n')

			#sys.stdout.write(str(out) + '\n')
		elif status == 'READ':
			pass
		else:
			log('Unknown message','Skype')
	def run(self):
		while self.s == None:
			if sys.platform.startswith('linux'):
				self.s = Skype4Py.Skype(Transport=os.environ.get('HUBOT_SKYPE_TRANSPORT', 'x11'))
			else:
				self.s = Skype4Py.Skype()

			self.s.OnMessageStatus = self.on_message
			try:
				self.s.Attach()
				log('Engine started','Skype')
				break
			except:
				log(' {FAIL} Engine could not start','Skype')
				self.s = None
				sleep(60)
		while 1:
			sleep(0.1)

if __name__ == '__main__':
	__username__ = 'DHPraktikanten'
	__password__ = raw_input('Password: ')
	# ...