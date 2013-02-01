#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from helpers import *
from config import *
from logger import log
from threading import *

import asyncore
from threading import *
from time import sleep, strftime, localtime, time
from os import _exit
from socket import *

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

class main(Thread, asyncore.dispatcher):
	def __init__(self, _s = None):
		Thread.__init__(self)

		self._s = _s
		self.looper = None

		self.inbuffer = ''
		self.lockedbuffer = False
		self.lockedoutbuffer = False
		self.is_writable = False

		self.exit = False

		if _s:
			## If we got a socket, it means this is not the main socket
			asyncore.dispatcher.__init__(self, _s)
			self.sender = sender(self.send)
		else:
			## If main socket, a sender will not be possible
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

		# Parse data
		if 'get::history::irc::5' in self.inbuffer:
			ret = ''
			if 'logs' in core['pickle_ignore'] and 'irc' in core['pickle_ignore']['logs']:
				print 'The logs are here:',core['pickle_ignore']['logs']['irc']
				for obj in core['pickle_ignore']['logs']['irc'][-5:]:
					ret += obj[0] + ':' + obj[1] + ';'
				self.sender.send(ret[:-1] + '\n')
			else:
				print 'No logs...', core['pickle_ignore']
				self.sender.send(ret + '\n')
		else:
			print 'Parsed failed: ' + str(self.inbuffer)
			self.sender.send('')

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
		x = main(sock)
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

	def run(self):
		while not self.exit:
			if len(self.inbuffer) > 0:
				self.parse()
			sleep(0.01)