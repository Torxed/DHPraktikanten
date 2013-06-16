#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from helpers import *
from config import *
from logger import log
from threading import *

import asyncore, hashlib
from threading import *
from time import sleep, strftime, localtime, time
from os import _exit
from socket import *
from base64 import b64encode, b64decode
from hashlib import sha1

def hash(what):
	m = sha1()
	m.update(what)
	return m.hexdigest()

class looper(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.start()
	def run(self):
		log('Iniating asyncore loop','Backend')
		asyncore.loop(0.1)
		log('Asyncore died','Backend')

class sender(Thread):
	def __init__(self, sock_send, source='Backend_sender'):
		Thread.__init__(self)

		self.s = sock_send
		self.bufferpos = 0
		self.buffer = {}
		self.source = source

		self.start()

	def send(self, what):
		if what[-1:] != '\n':
			what += '\n'
		self.buffer[len(self.buffer)] = what

	def writable(self):
		return (len(self.buffer) > self.bufferpos)

	def run(self):
		while 1:
			if self.writable():
				logout = str([self.buffer[self.bufferpos]])
				log('{OUT} ' + logout, self.source)
				self.s(self.buffer[self.bufferpos])
				self.bufferpos += 1
			sleep(0.1)

class main(Thread, asyncore.dispatcher):
	def __init__(self, _s = None, push_notifications={}, addr=None):
		Thread.__init__(self)

		self._s = _s
		self.looper = None

		self.inbuffer = ''
		self.lockedbuffer = False
		self.lockedoutbuffer = False
		self.is_writable = False

		self.exit = False
		self.push_notifications = push_notifications
		#self.addr = addr
		#print self.addr

		# self.push_notifications = {'sock' : None|'Nick'}

		if _s:
			## If we got a socket, it means this is not the main socket
			asyncore.dispatcher.__init__(self, _s)
			self.sender = sender(self.send)
			self.client = True
		else:
			## If main socket, a sender will not be possible
			self.client = False
			asyncore.dispatcher.__init__(self)
			self.create_socket(AF_INET, SOCK_STREAM)
			#if self.allow_reuse_address:
			#	self.set_resue_addr()

			log('Backend listening on '':6660', 'Backend')
			self.bind(('', 6660))
			self.listen(5)

			self.sender = None
			self.loop = looper()

		self.start()

	def parse(self):
		self.lockedbuffer = True
		user, data = None, ''

		if not self.inbuffer[-1] == '\n':
			rows = self.inbuffer[:self.inbuffer.rfind('\n')+1].split('\n')
		else:
			rows = self.inbuffer.split('\n')

		for row in rows:
			if len(row) <= 0: continue

			if '::' in self.inbuffer and self.inbuffer.count('%%') > 1:
				self.sender.send('-1%%error::encrypt your data\n')
				continue

			## Split at <username>%%<enc data>
			## convert the username to a sha256(b64enc(username))
			if '%%' in row:
				user, data = row.split('%%',1)
				if self.push_notifications[self.addr[0]]['nick'] == None:
					self.push_notifications[self.addr[0]]['nick'] = user
				## If we have a sha256(b64enc(username)) in our database core['backend']
				## then we try to decrypt the data with that users secret.
				if hashlib.sha256(b64encode(user)).digest() in core['backend']['accounts']:
					secret = core['backend']['accounts'][hashlib.sha256(b64encode(user)).digest()]
					data = decrypt(data, secret)
					log('{IN:DEC} "' + user + '" - ' + str(data), 'Backend:Parse')

			if not user or not '::' in data:
				self.sender.send('-1%%error::login\n')
				continue

			if '%%' in data:
				## All messages containing %% is a specific request for a specific task
				_id, data = data.split('%%',1)
				if '::' in data:
					params = data.split('::')
					if params[0] == 'update':
						if params[1] == 'queue':
							update = core['pickle_ignore']['queue'].accept_name(params[2])
							if update[0] != None:
								if not 'global_push' in core['pickle_ignore']:
									core['pickle_ignore']['global_push'] = {}
								if not 'queue' in core['pickle_ignore']['global_push']:
									core['pickle_ignore']['global_push']['queue'] = [3, '']
								
								core['pickle_ignore']['global_push']['queue'][1] = core['pickle_ignore']['global_push']['queue'][1].replace(str(update[0]) + ':unaccepted:'+update[1], str(update[0]) + ':accepted:'+update[1])
								#core['pickle_ignore']['global_push']['queue'][1] = core['pickle_ignore']['global_push']['queue'][1] + ';' + str(update[0]) + ':accepted:'+update[1]
								#if core['pickle_ignore']['global_push']['queue'][1][0] == ';':
								#	core['pickle_ignore']['global_push']['queue'][1] = core['pickle_ignore']['global_push']['queue'][1][1:]
							else:
								update = core['pickle_ignore']['queue'].complete_name(params[2])
								if update[0] != None:
									if not 'global_push' in core['pickle_ignore']:
										core['pickle_ignore']['global_push'] = {}
									if not 'queue' in core['pickle_ignore']['global_push']:
										core['pickle_ignore']['global_push']['queue'] = [3, '']
									
									core['pickle_ignore']['global_push']['queue'][1] = core['pickle_ignore']['global_push']['queue'][1].replace(str(update[0]) + ':accepted:'+update[1], str(update[0]) + ':done:'+update[1]) 
					elif params[0] == 'get':
						if params[1] == 'history':
							if params[2] == 'irc':
								print 'Building irc logs...'
								ret = ''
								if 'logs' in core['pickle_ignore'] and 'irc' in core['pickle_ignore']['logs']:
									print 'The logs are here:',core['pickle_ignore']['logs']['irc']
									for obj in core['pickle_ignore']['logs']['irc'][-5:]:
										ret += obj[0] + ':' + obj[1] + ';'
									self.sender.send(_id + '%%' + ret[:-1] + '\n')
								else:
									print 'No logs...', core['pickle_ignore']
									self.sender.send(_id + '%%' + ret + '\n')

				else:
					self.sender.send(_id + '%%' + '')
			else:
				_id = '3'

				params = data.split('::')
				if params[0] == 'register':
					self.sender.send(_id + '%%' + encrypt('queue::' + ';'.join(core['pickle_ignore']['queue']._get()) + '\n', secret))
			"""
			params = data.split('::')
			if params[0] == 'get':
				if params[1] == 'queue':
					self.sender.send(_id + '%%' + encrypt(';'.join(core['pickle_ignore']['queue']._get()) + '\n', secret))
				elif params[1] == 'version':
					self.sender.send(_id + '%%' + encrypt('1.0', secret))
				elif params[1] == 'status':
					self.sender.send(_id + '%%' + encrypt('Healthy', secret))
				else:
					ret = ''
					print 'Building irc logs...'
					if 'logs' in core['pickle_ignore'] and 'irc' in core['pickle_ignore']['logs']:
						print 'The logs are here:',core['pickle_ignore']['logs']['irc']
						for obj in core['pickle_ignore']['logs']['irc'][-5:]:
							ret += obj[0] + ':' + obj[1] + ';'
						self.sender.send(_id + '%%' + ret[:-1] + '\n')
					else:
						print 'No logs...', core['pickle_ignore']
						self.sender.send(_id + '%%' + ret + '\n')
			elif params[0] == 'update':
				if params[1] == 'queue':
					pass
			else:
				print 'Parsed failed: ' + str(self.data)
				self.sender.send(_id + '%%' + '')
			"""

		if not self.inbuffer[-1] == '\n' and '\n' in self.inbuffer:
			self.inbuffer = self.inbuffer[self.inbuffer.rfind('\n')+1:]
		else:
			self.inbuffer = ''
		self.lockedbuffer = False

	def readable(self):
		return True
	def handle_connect(self):
		pass
	def handle_accept(self):
		obj = self.accept()
		if obj:
			(conn_sock, client_address) = obj
			log('Iniating connection with: ' + str(client_address), 'Backend')
			if self.verify_request(conn_sock, client_address):
				self.process_request(conn_sock, client_address)
		else:
			log('Error accepting: ' + str(obj))
	def process_request(self, sock, addr):
		log('	Accepted: ' + str(addr), 'Backend')
		x = main(sock, self.push_notifications, addr[0])
		self.push_notifications[addr[0]] = {'sock' : x, 'nick' : None, 'sent' : {}}
	def verify_request(self, conn_sock, client_address):
		return True
	def handle_close(self):
		self.close()
	def handle_read(self):
		data = self.recv(8192)
		while self.lockedbuffer:
			sleep(0.01)
		self.inbuffer += data
	def writable(self):
		return True
	def handle_write(self):
		pass

	def push(self, ip):
		pass

	def run(self):
		static_messages = {'version' : (0, '1.0'),
							'status' : (1, 'Healthy')}

		#if params[1] == 'queue':
		#	self.sender.send(_id + '%%' + encrypt(';'.join(core['pickle_ignore']['queue']._get()) + '\n', secret))

		while not self.exit:
			if len(self.inbuffer) > 0:
				self.parse()
			if not self.client:
				for ip, vals in self.push_notifications.items():
					if vals['nick']:
						user = vals['nick']
						secret = core['backend']['accounts'][hashlib.sha256(b64encode(user)).digest()]

						for k,v in static_messages.items():
							if not k in vals['sent'] or hash(str(v)) != vals['sent'][k]:
								try:
									vals['sock'].sender.send(str(v[0]) + '%%' + encrypt(k + ':' + v[1], secret) + '\n')
									log(k + ':'+v[1], 'PUSH::'+user)
									self.push_notifications[ip]['sent'][k] = hash(str(v))
								except Exception, e:
									del self.push_notifications[ip]

						if 'global_push' in core['pickle_ignore']:
							for k,v in core['pickle_ignore']['global_push'].items():
								if not k in vals['sent'] or hash(str(v)) != vals['sent'][k]:
									try:
										self.push_notifications[ip]['sock'].sender.send(str(v[0]) + '%%' + encrypt(k + '::' + v[1], secret) + '\n')
										log(k + ':'+v[1], 'PUSH::'+user)
										self.push_notifications[ip]['sent'][k] = hash(str(v))
									except Exception, e:
										del self.push_notifications[ip]
				sleep(5)
			else:
				sleep(0.01)