import sys
from time import time, sleep
from threading import *
from pickle import dump
from os.path import isfile, isdir
from shutil import copy2 as copy
from os import remove, makedirs

class garbageman(Thread):
	def __init__(self, core):
		Thread.__init__(self)
		if not isdir('./db_backups'):
			makedirs('./db_backups')
		self.core = core

	def run(self):
		if not 'backupcounter' in self.core['pickle']:
			self.core['pickle']['backupcounter'] = 0
		while 1:
			#core['pickle_ignore']['queue'].notify()

			if isfile('./dh_database.db'):
				self.core['pickle']['backupcounter'] = (self.core['pickle']['backupcounter'] + 1)%10
				if isfile('dh_database.'+str(self.core['pickle']['backupcounter'])):
					remove('dh_database.'+str(self.core['pickle']['backupcounter']))
				copy('dh_database.db', './db_backups/dh_database.'+str(self.core['pickle']['backupcounter']))

			self.core['pickle']['flags']['dblock'] = True
			f = open('./dh_database.db', 'wb')
			dump(self.core['pickle'], f)
			f.close()
			sys.stdout.flush()
			self.core['pickle']['flags']['dblock'] = False
			sleep(5)
