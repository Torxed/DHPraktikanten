#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from time import sleep, strftime, localtime, time
from random import randint
from config import core
from logger import *

class IrcCallback():
	def __init__(self, sock, replychan, _who = ''):
		self.s = sock
		self.c = replychan
		self.w = _who

	def send(self, x):
		if len(self.w) > 0:
			self.w += ' '
		self.s('PRIVMSG ' + self.c + ' :' + self.w + x)

class ircparsers():
	def __init__(self, sender, conf, channels):
		self.conf = conf
		self.send = sender
		self.channels = channels

	def refstr(self, what):
		while len(what) > 0 and what[-1] in ('\r', '\n', ':', ' ', '	'):
			what = what[:-1]
		while len(what) > 0 and what[0] in ('\r', '\n', ':', ' ', '	'):	
			what = what[1:]
		return what

	def twittercallback(self, msg, *args, **kwargs):
		print args
		channel, who = args[0][0]
		self.send('PRIVMSG ' + channel + ' :' + msg)

	def MODE(self, data):
		_who, msgtype, channel, msg = data.split(' ', 3)
		_who, host = self.refstr(_who).split('!')
		channel = self.refstr(channel)
		if channel == self.conf['nickname']:
			return True

		mode, towho = msg.split(' ',1)
		if towho in self.channels[channel]['people']:
			if '+o' in mode:
				mode = '@'
			elif '+v' in mode:
				mode = '+'
			else:
				mode = '-'
			self.channels[channel]['people'][towho] = mode

	def PRIVMSG(self, data):
		# :DoXiD!~na@c-9ac3e355.41-5-64736c11.cust.bredbandsbolaget.se PRIVMSG #DHSupport :Test
		_who, msgtype, channel, msg = data.split(' ', 3)
		_who, host = self.refstr(_who).split('!')
		channel = self.refstr(channel)
		msg = msg[1:]
		replychan = channel
		if channel == self.conf['nickname']:
			print _who + ': ' + msg
			replychan = _who
		elif channel in self.channels:
			self.channels[channel]['chatlog'].append((_who, msg))
			if channel not in ('#dreamhack', '#DHSupport'): #mute list
				print '['+channel+'] ' + _who + ': ' + msg

		if msg[:9] == '!roulette':
			if not 'gun' in self.conf or self.conf['gun'] == None:
				self.conf['gun'] = {'fired' : 0, 'pos' : randint(1,6), 'total' : 6, 'emptied' : None, 'bullet' : randint(1,6)}

			if self.conf['gun']['emptied'] and time() - self.conf['gun']['emptied'] > 3600:
				self.conf['gun'] = {'fired' : 0, 'pos' : randint(1,6), 'total' : 6, 'emptied' : None, 'bullet' : randint(1,6)}

			if not self.conf['gun']['emptied']:
				barrelbullet = self.conf['gun']['bullet']
				shotfired = self.conf['gun']['pos']
				self.conf['gun']['fired'] += 1
				self.conf['gun']['pos'] = (self.conf['gun']['pos'] + 1)%self.conf['gun']['total']+1

#				print self.conf['gun']

				if barrelbullet == shotfired:
					self.send('PRIVMSG ' + replychan + ' :*BANG!* ' + _who + ' is dead!')
					self.send('MODE ' + replychan + ' -v ' + _who)
					self.conf['gun']['emptied'] = time()
				else:
					clickmessages = ['*click*.. phew', '*click*! I don\t like where this is going..', '*click*, can i stop now?']
					self.send('PRIVMSG ' + replychan + ' :' + clickmessages[randint(0, len(clickmessages)-1)])

				if not self.conf['gun']['emptied'] and self.conf['gun']['fired'] >= self.conf['gun']['total']:
					self.send('PRIVMSG ' + replychan + ' :Gun emptied, nu bullet in the slug? :O')
					self.conf['gun']['emptied'] = time()
			else:
				if not 'informed' in self.conf['gun']:
					self.conf['gun']['informed'] = False
				if not self.conf['gun']['informed']:
					self.send('PRIVMSG ' + replychan + ' :Gun is still warm from a fresh kill, and i don\'t like killing people anyways... so..')
					self.conf['gun']['informed'] = True

		elif msg[:] == '!reloadthegun':
			self.conf['gun'] = {'fired' : 0, 'pos' : randint(1,6), 'total' : 6, 'emptied' : None, 'bullet' : randint(1,6)}
			self.send('PRIVMSG ' + replychan + ' :Locked and loaded!')
		else:
			x = core['pickle_ignore']['parser']('IRC', _who+'@'+self.conf['server'], msg, IrcCallback(self.send, replychan, _who))
			if x == True:
				pass
			elif x == None:
				pass
			else:
				self.send('PRIVMSG ' + replychan + ' :' + _who + ' ' + x)

		return None

	def NOTICE(self, data):
		return None

	def JOIN(self, data):
		_who, msgtype, channel = data.split(' ', 2)
		channel = self.refstr(channel)
		if not channel in self.channels:
			self.channels[channel] = {}
			self.channels[channel]['people'] = {}
			self.channels[channel]['chatlog'] = []
		if '!' in _who:
			_who, host = _who.split('!', 1)
			_who = self.refstr(_who)
			if not _who in self.channels[channel]['people']:
				if not '+' in _who[0] or not '@' in _who[0]:
					mode = '-'
				else:
					mode = _who[0]
				_who = _who.replace('@', '').replace('+','')
				self.channels[channel]['people'][_who] = mode
		return None
