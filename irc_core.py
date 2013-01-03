#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import asyncore
from threading import *
from socket import *
from time import sleep, strftime, localtime, time
from os import _exit

def _map():
	return {}
def _array():
	return []

class irc(Thread, asyncore.dispatcher):
	def __init__(self, config):
		self.conf = config
		self.channels = {}
		self.messages = {}

		if not 'server' in config:
			print 'No server specified in config'
			return None
		if not 'port' in config:
			self.conf['port'] = 6667

		self.inbuffer = ''
		self.buffer = ''
		self.lockedbuffer = False
		self.is_writable = False

		self.MOTD = None
		self.exit = False

		self.ircparsers = __import__('ircparsers')

		asyncore.dispatcher.__init__(self)
		Thread.__init__(self)

		self.create_socket(AF_INET, SOCK_STREAM)
		try:
			self.connect((self.conf['server'], self.conf['port']))
		except:
			print 'Could not connect to',self.conf['server']
			return None

		self.buffer += 'NICK ' + self.conf['nickname'] + '\r\n'
		self.buffer += 'USER ' + self.conf['userid'] + ' ' + self.conf['server'] + ' ' + self.conf['nickname'] + ' :' + self.conf['fullname'] + '\r\n'

	def refstr(self, what):
		while len(what) > 0 and what[-1] in ('\r', '\n', ':', ' ', '	'):
			what = what[:-1]
		while len(what) > 0 and what[0] in ('\r', '\n', ':', ' ', '	'):	
			what = what[1:]
		return what

	def compare(self, obj, otherobj):
		return (str(obj).lower() == str(otherobj).lower()[:len(str(obj))])
	def _in(self, obj, otherobj):
		return (str(obj).lower() in str(otherobj).lower())

	def parse(self):
		if self.inbuffer[-2:] != '\r\n':
			return False
		self.lockedbuffer = True

		for row in self.inbuffer.split('\r\n'):
			#row = self.refstr(row)
			if len(row) <= 0: continue

			if self.compare('PING', row):
				self._send('PONG ' + row[5:])
				continue

			if 'no ident response' in row.lower():
				self.is_writable = True
			elif not self.MOTD:
				if not 'motd' in self.conf:
					self.conf['motd'] = ''
				self.conf['motd'] += row
				if self._in('End of /MOTD command', row):
					if self.conf['password']:
						if self.conf['server'] == 'se.irc.quakenet.org':
							self._send('PRIVMSG Q@CServe.quakenet.org :AUTH '+self.conf['nickname'] + ' ' + self.conf['password'])
						else:
							self._send('PRIVMSG NickServ :identify ' + self.conf['nickname'] + ' ' + self.conf['password'])
						for chan in self.conf['channels']:
							if len(chan) <= 0: continue

							self._send('JOIN ' + chan)
					#print ' * MOTD recieved!'
					self.MOTD = True
			elif self.MOTD:

				reload(self.ircparsers)
				ircparse = self.ircparsers.ircparsers(self._send, self.conf, self.channels)

				functions = {
					' JOIN ' : ircparse.JOIN,
					'  NOTICE ' : ircparse.NOTICE,
					' PRIVMSG ' : ircparse.PRIVMSG,
					' MODE ' : ircparse.MODE,
				}
				if ':' in row[0] and '@' in row.split(' ', 1)[0]:
					for msgtype in functions:
						if msgtype in row:
							functions[msgtype](row)
				else:
					row = self.refstr(row)
					who, code, row = row.split(' ', 2)
					if code == '353':
						_to, people = row.split(' :', 1)
						_to, chan = _to.split('=',1)
						_to = self.refstr(_to)
						chan = self.refstr(chan)
						people = self.refstr(people)
						for person in people.split(' '):
							if not person in self.channels[chan]:
								if person[0] not in ('@', '+'):
									mode = '-'
								else:
									mode = person[0]
								person = person[1:]
								self.channels[chan]['people'][person] = mode
					elif code == '366':
						_to, chan, row = row.split(' ',2)
						chan = self.refstr(chan)
						print len(self.channels[chan]['people']),'people in ' + chan

					else:
						pass
						#print 'Unknown starter command',[row]

		self.inbuffer = ''
		self.lockedbuffer = False

	def readable(self):
		return True
	def handle_connect(self):
		print 'Connected to', self.conf['server']
	def handle_close(self):
		self.close()
	def handle_read(self):
		data = self.recv(8192)
		while self.lockedbuffer:
			sleep(0.01)
		f = open('debug.raw', 'a')
		f.write(str([data]) + '\n')
		f.close()
		self.inbuffer += data
	def writable(self):
		return (len(self.buffer) > 0)
	def handle_write(self):
		while self.is_writable:
			sent = self.send(self.buffer)
			sleep(1)
			#print '>> ' + str([self.buffer[:sent]])
			self.buffer = self.buffer[sent:]
			if len(self.buffer) <= 0:
				self.is_writable = False
			sleep(0.01)
	def _send(self, what):
		self.buffer += what + '\r\n'
		self.is_writable = True
	def handle_error(self):
		print 'Error, closing socket!'
		self.close()

	def run(self):
		while not self.exit:
			if len(self.inbuffer) > 0:
				self.parse()
			sleep(0.01)
		self.close()

class commandline(Thread):
	def __init__(self, sock):
		Thread.__init__(self)
		self.socks = sock
		self.server = None

	def run(self):
		while 1:
			if self.server and self.server in self.socks:
				cmd = raw_input(self.socks[self.server]['name'] + ': ')
			else:
				cmd = raw_input('')
			if cmd == 'exit' or cmd == 'quit':
				for server in self.socks:
					self.socks[server]['sock'].exit = True
				break
			else:
				if cmd[0] == ':':
					if cmd[1] in self.socks:
						self.server = cmd[1]
				else:
					if self.server and self.server in self.socks:
						self.socks[self.server]['sock']._send(cmd)
					else:
						print ' <- Please select a server'

quakenet = irc({'server' : 'irc.se.quakenet.org', 'port' : 6667, 'nickname' : 'DHPraktikanten', 'userid' : 'DHPraktikanten', 'fullname' : 'Kaylee Frye', 'channels' : ['#dhsupport', '#dreamhack'], 'password' : __password__})
quakenet.start()

servers = {'q' : {'name' : 'QuakeNet', 'sock' : quakenet},
			'f' : {'name' : 'FreeNode', 'sock' : freenode}}

c = commandline(servers)
c.start()

asyncore.loop(0.1)
