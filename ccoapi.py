#!/usr/bin/python
from threading import *
from getpass import getpass
from logger import log
from config import core
from oauth import OAuth
from helpers import *
from time import sleep
from random import randint

__date__ = '2013-01-07 15:10 CET'
__version__ = '0.0.1'
__author__ = 'Anton Hvornum - http://www.linkedin.com/profile/view?id=140957723'

class CCO(Thread):
	def __init__(self):
		Thread.__init__(self)
		log('Engine started', 'CCO')
		self.OAuth = OAuth('api.crew.dreamhack.se')
		self.start()
		self.thankyous = ['Aren\'t you just the best! :D\n\nYou\'ve scucessfully subscribed to Crew Corners mailinglist for new events!',
						'You can put a Trojan on my Hard Drive anytime because You\'ve scucessfully subscribed to Crew Corners mailinglist for new events!',
						'Are you Google? Because you have everything I\'m searching for and ontop of that, You\'ve scucessfully subscribed to Crew Corners mailinglist for new events!',
						'You got me stuck on Caps Lock, if you know what I mean. Oh and You\'ve scucessfully subscribed to Crew Corners mailinglist for new events!',
						'Your beauty rivals the graphics of Crysis... And You\'ve scucessfully subscribed to Crew Corners mailinglist for new events!',
						'You must be Windows 95 because you gots me so unstable that i\'ve accidenatly subscribed you to the Crew Corners mailing list!',
						'If you won\'t let me buy you a drink, at least let me fix your laptop and subscribe you to the Crew Corners mailinglist?',
						'Isn\'t your e-mail address beautifulgirl@mydreams.com? Oh well.. Here\'s a subscription to the CCO mailing list',
						'What\'s a nice girl like you doing in a chatroom like this? Oh subsciiiibing? ok.. In that case, you\'re subscribed to CCO mailinglist! ;)',
						'I think you could be an integral part of my project life cycle. Because you\'re in my Mailinglist for Crew Corner ;)',
						'I\'ll bet my hard drive is the biggest you\'ve ever seen!! I mean.. erm.. Subscription? sure CCO mailinglist here you go!',
						'Your homepage or mine? Oh mine? Sure.. in that case, you\'re on my list of mails to CCO',
						'Want to come see my HARD Disk? I promise it isn\'t 3.5 inches and it ain\'t floppy... But since I\'m shy we\'ll start off with a mialing list for CCO ok?',
						'How about we go home and you handle my exception? Oh shoot, no exceptions my my core :S But a addition to the mailing list has been done for you!']

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

			if 'email' in core['pickle_ignore']:
				
				if not 'mailinglist' in core['pickle']:
					core['pickle']['mailinglist'] = {}
				if not 'cco' in core['pickle']['mailinglist']:
					core['pickle']['mailinglist']['cco'] = []

				for person in core['pickle_ignore']['email'].getmailinglist():
					body = ''
					person, msg = person
					if len(person) <= 0 or '@' not in person: continue

					## generate a nicer subject and message body.
					if len(new) == 1: m, t = 'A new event', 'A new event on CC'
					else: m, t = 'New events', 'New events on CC'

					## Generate Eventlist
					l = ''
					for item in new: l += ' - ' + item + '\n'

					if person in core['pickle']['mailinglist']['cco']:
						continue
					else:
						core['pickle']['mailinglist']['cco'].append(person)
						if 'hello world' in msg.lower():
							body += 'You had me at "Hello World." <3\nYou\'re subscribed to the CCO mailing list for new events ;)'
						else:
							body += self.thankyous[randint(0, 1000)%len(self.thankyous)-1]
						#core['pickle_ignore']['email'].send(person, 'You are now on CCO new event mailinglist', body)
					
					if len(l) > 0:
						body += '\n\nNew events:\n' + l
					elif len(l) == 0 and len(body) > 0:
						body += '\n\n\n\nTo unsubscribe, send a e-mail (containing what ever) to: anton.doxid+unwatch@gmail.com!'

					if len(body) > 0:
						core['pickle_ignore']['email'].send(person, t, body)

			sleep(60)


if __name__ == '__main__':
	if not 'password' in core['pickle_ignore']:
		core['pickle_ignore']['password'] = getpass('Enter master password: \n')
	x = CCO()
	sleep(10)
	x._Thread__stop()