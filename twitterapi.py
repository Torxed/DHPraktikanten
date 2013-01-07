#!/usr/bin/python
# -*- coding: utf-8 -*-
import twitter
from config import core
from threading import *
from os import _exit, urandom
from time import sleep
import unicodedata

## Crypto from: http://www.voidspace.org.uk/python/modules.shtml#pycrypto
from Crypto.Cipher import AES
import base64

## Based on: https://github.com/sixohsix/twitter

def decrypt(what):
	BLOCK_SIZE = 32
	PADDING = '|'
	p = core['pickle_ignore']['password']
	DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
	pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
	cipher = AES.new(pad(p))
	decoded = DecodeAES(cipher, what)
	return decoded

class twitt(Thread):
	def __init__(self, tags = None, *args, **kwargs):
		self.consumer_key = decrypt(core['twitter']['consumer_key'])
		self.consumer_secret = decrypt(core['twitter']['consumer_secret'])
		self.access_key = decrypt(core['twitter']['access_key'])
		self.access_secret = decrypt(core['twitter']['access_secret'])

		self.OAuth_token = None
		self.OAuth_secret = None

		self.encoding = 'iso-8859-15'

		self.args = args
		self.kwargs = kwargs
		self.loggedin = None

		self.searchapi = twitter.Twitter(domain="search.twitter.com").search
		self.postapi = None

		#self.info = self.api.VerifyCredentials()
		#self.friends = self.api.GetFriends()
		self.tags = tags

		self.alive = True
		self.reportback = None
		self.initiatedreportback = False
		self.posts = {}
		self.searches = {}
		self.searched = {}
		# self.info['id']

		Thread.__init__(self)
		self.start()

		self.login()

	def login(self):
		self.loggedin = twitter.OAuth(self.access_key, self.access_secret, self.consumer_key, self.consumer_secret)
		self.OAuth_token = self.loggedin.token
		self.OAuth_secret = self.loggedin.token_secret

		self.postapi = twitter.Twitter(auth=twitter.OAuth(self.OAuth_token, self.OAuth_secret, self.consumer_key, self.consumer_secret))

	def refstr(self, what):
		while len(what) > 0 and what[-1] in ('\r', '\n', ':', ' ', '	', '{', '}', '"', "'"):
			what = what[:-1]
		while len(what) > 0 and what[0] in ('\r', '\n', ':', ' ', '	', '{', '}', '"', "'"):	
			what = what[1:]
		return what

#	def convertmap(self, data):
#		m = {}
#		data = str(data)
#		for item in data.split(','):
#			#item = self.refstr(item)
#			print [item]
#			key, val = item.split(':', 1)
#			key = self.refstr(key)
#			val = self.refstr(val)
#			m[key] = val
#		return m

	#def updateposts(self):
	#	for friend in self.friends:
	#		timeline = self.api.GetUserTimeline(friend.id)
	#		for post in timeline:
	#			if not post.id in self.posts:
	#				self.posts[post.id] = post
	#	return True

	def search(self, tag):
		i = 0
		for result in self.searchapi(q=tag)['results']:
		#for result in self.api.GetSearch(tag):
		#	#print ''
		#	#print result
			if not tag in self.searches:
				self.searches[tag] = []
			if not tag in self.searched:
				self.searched[tag] = []
			if not result['id'] in self.searched[tag]:
				self.searches[tag].append(result)
				self.searched[tag].append(result['id'])

				if self.reportback:
					if not self.initiatedreportback:
						i += 1
						if i >= 5: continue
					#result['text'] = unicodedata.normalize('NFKD', result['text']).encode('latin-1','replace')
					result['text'] = result['text'].encode('ascii', 'replace')

					self.reportback('(twitter) ' + str(result['from_user'] + ': ' + result['text']), self.args, self.kwargs)
		self.initiatedreportback = True
		return self.searched

	def post(self, what):
		if not self.postapi:
			self.login()

		self.postapi.statuses.update(status=what)

	def returntag(self, tag, ammount=5):
		searches = []
		if not tag in self.searches:
			return None
		for post in self.searches[tag][:ammount]:
			searches.append((post.user.screen_name,post.text))
		return searches

	def run(self):
		while self.alive:
			#self.updateposts()
			if self.tags:
				for tag in self.tags:
					if len(tag) <= 0: continue
					self.search(tag)
			sleep(3)
			#i = 0
			#for _id in sorted(self.posts, reverse=True):
			#	print self.posts[_id].name,':',self.posts[_id].text
			#	i += 1
			#	if i >= 5: break

if __name__ == "__main__":
	core['pickle_ignore']['password'] = raw_input('Enter your master password: ')
	t = twitt()
	print t.search('#DHSupport')
	t.alive = False