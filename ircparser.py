#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from time import sleep, strftime, localtime, time
from random import randint

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

		if msg[:4] == '!rss':
			if not 'rss' in self.conf:
				self.conf['rss'] = {}
			if not replychan in self.conf['rss']:
				self.conf['rss'][replychan] = {'thread' : None, 'locked' : {'by' : None, 'delock' : 'operator'}}
			# rss('http://www.robertsspaceindustries.com/feed/')
			if not self.conf['rss'][replychan]['locked']['by']:
				if self.conf['rss'][replychan]['thread']:
					self.conf['rss'][replychan]['thread'].alive = False
					self.conf['rss'][replychan]['thread'] = None

				rss = __import__('rsser')
				reload(rss)
				rssfeed = msg.split(' ')[1:]
				if len(rssfeed) == 1:
					if rssfeed[0] == 'sc':
						rssfeed = ['http://www.robertsspaceindustries.com/feed/']
				h = rss.rss(rssfeed, (replychan, _who))
				h.callback = self.twittercallback
				self.conf['rss'][replychan]['thread'] = h

				self.send('PRIVMSG ' + replychan + ' :' + _who + ': Will report back any new feed items here!')
			else:
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': The rss is locked by ' + self.conf['rss'][replychan]['locked']['by'] + ' to ' +' '.join(self.conf['rss'][replychan]['thread'].tags))
		elif msg[:12] == '!lockrss':
			if not self.conf['rss'][replychan]['thread']:
				pass
			elif not self.conf['rss'][replychan]['locked']['by']:
				self.conf['rss'][replychan]['locked']['by'] = _who
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': twitterfeed is now locked for changes (+op or you can unlock it)!')
		elif msg[:14] == '!unlockrss':
			if not self.conf['rss'][replychan]['locked']['by']:
				pass
			elif _who == self.conf['rss'][replychan]['locked']['by'] or self.channels[channel]['people'][_who] in ('@', '+'):
				self.conf['rss'][replychan]['locked']['by'] = None
				self.send('rss ' + replychan + ' :' + _who + ': I have now unlocked the twitterfeed inviting changes to it!')
			else:
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': You have to be ' + str(self.conf['rss'][replychan]['locked']['by']) + ' or an +op to do this')
		elif msg[:10] == '!detrss':
			if 'rss' in self.conf and replychan in self.conf['rss'] and self.conf['rss'][replychan]['thread']:
				if self.conf['rss'][replychan]['locked']['by'] and (_who != self.conf['rss'][replychan]['locked']['by'] or self.channels[channel]['people'][_who] not in ('@', '+')):
					self.send('PRIVMSG ' + replychan + ' :' + _who + ': The twitterfeed can not be changed because it\'s locked by ' + self.conf['rss'][replychan]['locked']['by'])
				elif self.conf['rss'][replychan]['thread']:
					self.conf['rss'][replychan]['thread'].alive = False
					self.conf['rss'][replychan]['thread'] = None
					self.conf['rss'][replychan]['locked']['by'] = None
					self.send('PRIVMSG ' + replychan + ' :' + _who + ': Will stop reporting rss feeds here!')

		elif msg[:9] == '!roulette':
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
		elif msg[:8] == '!twitter':
			if not ' ' in msg:
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': You need to specify what #<tag(s)> you want me to report back here.. !twitter #tag1 [#tag2 [tag3] ...]')
			else:
				if not 'twitter' in self.conf:
					self.conf['twitter'] = {}
				if not replychan in self.conf['twitter']:
					self.conf['twitter'][replychan] = {'thread' : None, 'locked' : {'by' : None, 'delock' : 'opeartor'}}
				
				if not self.conf['twitter'][replychan]['locked']['by']:
					if self.conf['twitter'][replychan]['thread']:
						self.conf['twitter'][replychan]['thread'].alive = False
						self.conf['twitter'][replychan]['thread'] = None

					twitt = __import__('twitt')
					reload(twitt)
					h = twitt.twitt(msg.split(' ')[1:], (replychan, _who))
					h.reportback = self.twittercallback
					self.conf['twitter'][replychan]['thread'] = h

					self.send('PRIVMSG ' + replychan + ' :' + _who + ': Will report back any new tweets (besides these 5) here matching your tags!')
				else:
					self.send('PRIVMSG ' + replychan + ' :' + _who + ': The twitterfeed is locked by ' + self.conf['twitter'][replychan]['locked']['by'] + ' to ' +' '.join(self.conf['twitter'][replychan]['thread'].tags))
		elif msg[:12] == '!locktwitter':
			if not self.conf['twitter'][replychan]['thread']:
				pass
			elif not self.conf['twitter'][replychan]['locked']['by']:
				self.conf['twitter'][replychan]['locked']['by'] = _who
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': twitterfeed is now locked for changes (+op or you can unlock it)!')
		elif msg[:14] == '!unlocktwitter':
			if not self.conf['twitter'][replychan]['locked']['by']:
				pass
			elif _who == self.conf['twitter'][replychan]['locked']['by'] or self.channels[channel]['people'][_who] in ('@', '+'):
				self.conf['twitter'][replychan]['locked']['by'] = None
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': I have now unlocked the twitterfeed inviting changes to it!')
			else:
				self.send('PRIVMSG ' + replychan + ' :' + _who + ': You have to be ' + str(self.conf['twitter'][replychan]['locked']['by']) + ' or an +op to do this')
		elif msg[:10] == '!detwitter':
			if 'twitter' in self.conf and replychan in self.conf['twitter'] and self.conf['twitter'][replychan]['thread']:
				if self.conf['twitter'][replychan]['locked']['by'] and (_who != self.conf['twitter'][replychan]['locked']['by'] or self.channels[channel]['people'][_who] not in ('@', '+')):
					self.send('PRIVMSG ' + replychan + ' :' + _who + ': The twitterfeed can not be changed because it\'s locked by ' + self.conf['twitter'][replychan]['locked']['by'])
				elif self.conf['twitter'][replychan]['thread']:
					self.conf['twitter'][replychan]['thread'].alive = False
					self.conf['twitter'][replychan]['thread'] = None
					self.conf['twitter'][replychan]['locked']['by'] = None
					self.send('PRIVMSG ' + replychan + ' :' + _who + ': Will stop reporting twitter feeds here!')

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
