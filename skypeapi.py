#!/usr/bin/python
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
from parser import skypeParser as p_skype

__username__ = 'DHPraktikanten'
__password__ = raw_input('Password: ')

class Skype(Thread):
	def __init__self(self, callback = None):
		Thread.__init__(self)
		self.alive = True
		self.callback = callback

		if sys.platform.startswith('linux'):
			self.s = Skype4Py.Skype(Transport=os.environ.get('HUBOT_SKYPE_TRANSPORT', 'x11'))
		else:
			self.s = Skype4Py.Skype()

		self.s.OnMessageStatus = self.on_message
		self.s.Attach()

		#while True:
		#	line = sys.stdin.readline()
		#	try:
		#		decoded = json.loads(line)
		#		c = s.Chat(decoded['room'])
		#		c.SendMessage(decoded['message'])
		#	except:
		#		continue
		self.start()

	def selfCallback(self, m, channel):
		self.s.SenMessage(channel[0], m)

	def on_message(message, status):
	#	print status
	#	print message
	#	if status == Skype4Py.cmsReceived or status == Skype4Py.cmsSent:
	#		json_string = json.dumps({
	#			'user': message.Sender.Handle,
	#			'message': message.Body,
	#			'room': message.Chat.Name,
	#		})
	#		sys.stdout.write(json_string + '\n')
	#		sys.stdout.flush()

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
				'NickName' : str(NickName).encode('utf-8', 'replace')),
				'SenderStatus' : str(SenderStatus).encode('utf-8', 'replace')),
				'SenderMobile' : str(SenderMobile).encode('utf-8', 'replace')),
				'SenderAliases' : str(SenderAliases).encode('utf-8', 'replace')),
				'SenderFullName' : str(SenderFullName).encode('utf-8', 'replace')),
				'ChatRoom' : str(ChatRoom).encode('utf-8', 'replace')),
				'Text' : str(text).encode('utf-8', 'replace')),
			}

			if status == 'RECEIVED':
				sys.stdout.write('From: ' + out['NickName'] + '\n' + '    < ' + out['Text'] + ' (' + out['ChatRoom'] + ')\n')
				if not out['NickName'] in core['outqueue']:
					core['outqueue'][out['NickName']] = {}
				if not out['ChatRoom'] in core['outqueue'][out['NickName']]:
					core['outqueue'][out['NickName']][out['ChatRoom']] = {}

				if callback and p_skype:
					core['outqueue'][out['NickName']][out['ChatRoom']][out['Text']] = False
					p = p_skype(out['NickName'], out['Text'])
					if p:
						self.callback(out['text'], (out['NickName'], out['NickName']))
				elif callback:
					p = self.selfCallback(out['Text'], (out['NickName'],))
			elif status == 'SENT':
				towho = None
				if '/' in out['ChatRoom']:
					towho = out['ChatRoom'].split('/',1)[0]
					if towho[0] == '#':
						towho = towho[1:]
				if towho:
					sys.stdout.write('    > Answered ' + towho + '\n')
					sys.stdout.write('    ! Trying to delete ' + out['ChatRoom'] + ' - ' + out['Text'] + '\n')
					sys.stdout.write('      ' + core['outqueue'][towho] + '\n')
					if out in core['outqueue'][towho][out['ChatRoom']]:
						del core['outqueue'][towho][out['ChatRoom']][out['Text']]
					else:
						sys.stdout('      Already deleted?\n')
				else:
					sys.stdout.write('Couldn\'t understand who i sent to...\n')

			#sys.stdout.write(str(out) + '\n')

	#		sys.stdout.write(str(dir(chat)) + '\n')
	#		sys.stdout.write(str(status) + '\n')
	#		sys.stdout.write(str(dir(message)) + '\n')
			sys.stdout.flush()
		elif status == 'READ':
			pass
		else:
			sys.stdout.write(str(status) + '\n')
			sys.stdout.write(str(message) + '\n')
			sys.stdout.flush()

	def run(self):
		while 1:
			sleep(0.1)
