#!/usr/bin/python
from threading import *
from getpass import getpass
from logger import log
from config import core
from oauth import OAuth
from helpers import *
from time import sleep

__date__ = '2013-01-07 15:10 CET'
__version__ = '0.0.1'
__author__ = 'Anton Hvornum - http://www.linkedin.com/profile/view?id=140957723'

class CCO(Thread):
	def __init__(self):
		Thread.__init__(self)
		log('Engine started', 'CCO')
		self.OAuth = OAuth('api.crew.dreamhack.se')
		self.start()

	def login(self):
		tokens = self.OAuth.get() # Defaults to requesting the tokens
		core['cco']['access_key'] = tokens['oauth_token']
		core['cco']['access_secret'] = tokens['oauth_token_secret']

	def run(self):
		if not 'CCO_events' in core['pickle']:
			core['pickle']['CCO_events'] = []

		if core['cco']['access_key'] == '':
			self.login()

		while 1:
			new = []
			log('Getting eventlist','CCO')
			for e in getEvents(self.OAuth.get('/1/event/get/all')):
				if not e in core['pickle']['CCO_events']:
					new.append(e)
					core['pickle']['CCO_events'].append(e)
					log('New event: ' + str(e),'CCO')

			if len(new) > 0:
				if len(new) == 1:
					m = 'A new event'
					t = 'A new event on CC'
				else:
					m = 'New events'
					t = 'New events on CC'
				l = ''
				for item in new:
					l += ' - ' + item + '\n'

				if 'email' in core['pickle_ignore']:
					for person in core['pickle_ignore']['email'].getmailinglist():
						if len(person) <= 0 or '@' not in person: continue

						#core['pickle_ignore']['email'].send(person, t, m + " has been created on CC, apply for your position now!\n\n" + l)

			sleep(60)


if __name__ == '__main__':
	if not 'password' in core['pickle_ignore']:
		core['pickle_ignore']['password'] = getpass('Enter master password: \n')
	x = CCO()
	sleep(10)
	x._Thread__stop()