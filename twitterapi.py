#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import twitter
from threading import *
from os import _exit
from time import sleep
import unicodedata

class twitt(Thread):
	def __init__(self, tags = None, *args, **kwargs):
		consumer_key = 'wBXgoew6UJ96o2QfqRNQw'
		consumer_secret = 'yyF8pRTym9iq8p9GOxoQWBW3cRwVOInB8orQJUBKGo'
		access_key = '20031095-7AbTJYc92UztxRIccQb8BosfYli5Ciu56IFbOboSM'
		access_secret = 'NeisC3qwHEvgs7GUgGmFDEdFlxzYOAPhgztbMYMM'

		self.encoding = 'iso-8859-15'

		self.args = args
		self.kwargs = kwargs

		#self.api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_key, access_token_secret=access_secret, input_encoding=encoding)
		self.searchapi = twitter.Twitter(domain="search.twitter.com").search

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

	#	statuses = self.api.GetPublicTimeline()
	#	print [s.user.name for s in statuses]

	#	statuses = self.api.GetUserTimeline(self.info.id)
	#	for status in statuses:
	#		print statuses