#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import os
from threading import *
from time import time, strftime, sleep

def humantime(t):
	scale = ['sec', 'min', 'hours']
	i = 0
	while t >= 60:
		t = t/60
		i += 1
	return str(int(t)), scale[i]

def sysfunc(command):
	ret = ''
	for l in os.popen(command, 'r'):
		ret += l
	return ret

class clienthandle(Thread):
	def __init__(self, sock, addr, core):
		Thread.__init__(self)
		self.sock = sock
		self.addr = addr
		self.core = core
		self.responded = False

	def lookup(self):
		if self.addr[0] in self.core['pickle']['known']:
			return self.core['pickle']['known'][self.addr[0]]
		else:
			return self.addr[0]

	def send(self, what):
		self.sock.send(what)
		self.sock.close()
		self.responded = True
		print 'Responded:',len(what),'bytes'

	def power(self, cmd):
		if cmd[1] == 'overview':
			ret = ''
			good, bad = [], []
			reported = []
			for powerissues in reversed(self.core['pickle']['powerissues']):
				print powerissues
				hall, row, status = powerissues
				status = {True : '1', False : '0'}[self.core['pickle']['rows'][hall][row]['power']]
				if status == '1':
					if hall + ':' + str(row) + ':' + status in good:
						i = 0
						for item in good:
							if item == str(hall + ':' + str(row) + ':' + status):
								del good[i]
							i += 1
					good.append(hall + ':' + str(row) + ':' + status)
				else:
					bad.append(hall + ':' + str(row) + ':' + status)
			if len(bad) > 0:
				separator = ';'
			else:
				separator = ''
			if len(bad) > 0 or len(good) > 0:
				ret += ';'.join(bad) + separator + ';'.join(good[-7:])
			else:
				ret = 'Everything is good in this world!'
			self.send(ret)


		elif cmd[1] == 'report':
			hall, row, seat = cmd[2].split(';',2)
			i = 0
			while self.core['pickle']['flags']['dblock']:
				if i >= 100:
					print '!! Attention, waiting for database lock...'
				sleep(0.1)
				i += 1

			self.core['pickle']['powerissues'].append((hall, int(row), 0))
			self.core['pickle']['rows'][hall][int(row)]['power'] = False


		elif cmd[1] == 'complete':
			hall, row, seat = cmd[2].split(';',2)
			i = 0
			while self.core['pickle']['flags']['dblock']:
				if i >= 100:
					print '!! Attention, waiting for database lock...'
				sleep(0.1)
				i += 1

			while self.core['pickle']['powerissues'].count((str(hall), int(row), 0)) > 0:
				i = 0
				for item in self.core['pickle']['powerissues']:
					if item == (str(hall), int(row), 0):
						del self.core['pickle']['powerissues'][i]
						self.core['pickle']['powerissues'].append((str(hall), int(row), 1))
					i += 1 
			self.core['pickle']['rows'][hall][int(row)]['power'] = True


	def pc(self, cmd):
		ret = ''
		if cmd[1] == 'get' and len(cmd) >= 3 and cmd[2] == 'quickies':
			if len(cmd) == 4 and cmd[3].isdigit and int(cmd[3]) in self.core['pickle']['quickpicks']:
				for key, val in self.core['pickle']['quickpicks'][int(cmd[3])].items():
					ret += key + ':' + val + ';'
			else:
				for quickienr, quickietext in self.core['pickle']['quickpicks'].items():
					ret += str(quickienr) + ':' + quickietext['title'] + ';'
			self.send(ret)
		elif cmd[1] == 'get' and cmd[2] == 'statistics':
			self.send(str(len(self.core['pickle']['supportcases'])))
		elif cmd[1] == 'report':
			title, who, _type, comment = cmd[2].split(';')
			if len(who) > 0 and len(_type) > 0 and len(title) > 0:
				self.core['pickle']['supportcases'].append((who, _type, title, comment, len(self.core['pickle']['supportcases'])+1))
			print self.core['pickle']['supportcases']
			self.send('Gotcha!')

	def twitt(self, cmd):
		if cmd[1] == 'get':
			if cmd[2] == 'tag':
				twittposts = self.core['pickle_ignore']['twitter'].returntag(cmd[3])
				if twittposts:
					ret = ''
					for twittpost in twittposts:
						ret += '[' + twittpost[0] + ']:<p style="display: inline-block; color: #C2C2C2; margin: 0px; padding: 0px;">' + twittpost[1] + '</p><br>'
					self.send(ret)
				else:
					self.send('No twitter feed for ' + cmd[3])

	def crew(self, cmd):
		ret = ''
		if cmd[1] == 'support':
			if cmd[2] == 'working':
				currentHour = int(strftime('%H'))
				for startHour, rest in self.core['pickle']['supportscheme'].items():
					endHour = int(rest['end'])
					startHour = int(startHour)
					if currentHour < startHour:
						currentHour += 24
					if endHour < startHour:
						endHour += 24

					if currentHour >= startHour and currentHour <= endHour:
						for worker in rest['tech']:
							ret += worker + ';'
				self.send(ret[:-1])
	def run(self):
		cmd = self.sock.recv(8192)
		print 'Recieved:',cmd

		if '::' in cmd:
			cmd = cmd.split('::')
			if cmd[0] == 'power':
				self.power(cmd)
			elif cmd[0] == 'pc':
				self.pc(cmd)
			elif cmd[0] == 'crew':
				self.crew(cmd)
			elif cmd[0] == 'twitter':
				self.twitt(cmd)
			elif cmd[0] == 'vote':
				self.vote(cmd)

		if not self.responded:
			self.sock.send('Unknown data sent to backend')
			self.sock.close()
		else:
			try:
				self.sock.close()
			except:
				pass

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