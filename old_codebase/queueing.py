from time import time, sleep, localtime, strftime
from logger import *

def humantime(t):
	l = ['sec', 'min', 'hour', 'day']
	lc = [60, 60, 60, 24]
	i = 0
	while t > lc[i]:
		t = t/lc[i]
		i += 1
	return t,l[i]

class queue():
	def __init__(self):

		# - Queue -
		self.q = {
			#0 : {
			#	'source' : 'skype',
			#	'identifier' : 'Torxed',
			#	'task' : ('software', 'I need to reinstall my pc'),
			#	'times'    : {'reg' : time()-(60*10), 'finished' : time()-(60*5), 'accepted' : time()-(60*10)},
			#},
			#1 : {
			#	'source' : 'skype',
			#	'identifier' : 'Torxed',
			#	'task' : ('software', 'I need to reinstall my pc'),
			#	'times' : {'reg' : time(), 'finished' : None, 'accepted' : time()},
			#},
			#2 : {
			#	'source' : 'skype',
			#	'identifier' : 'Torxed',
			#	'task' : ('software', 'I need to reinstall my pc'),
			#	'times' : {'reg' : time(), 'finished' : None, 'accepted' : None},
			#},
			#3 : {
			#	'source' : 'skype',
			#	'identifier' : 'Nelly',
			#	'task' : ('software', 'I need to reinstall my pc'),
			#	'times' : {'reg' : time(), 'finished' : None, 'accepted' : None},
			#},
		}

		# - Settings -
		self.settings = {'queuepos' : -1, 'notifypercentage' : 80} # -1 = first run and queue item #0 will be returned
		log('Engine started','Queue')

	def accept_name(self, name):
		print 'Trying to accept',name
		print self.q
		for _id in self.q:
			if ((name == self.q[_id]['identifier'] or ('@' in self.q[_id]['identifier'] and name == self.q[_id]['identifier'].split('@',1)[0]))) and not self.q[_id]['times']['accepted']:
				self.q[_id]['times']['accepted'] = time()
				return _id, self.q[_id]['identifier']
		return None, None
	def complete_name(self, name):
		for _id in self.q:
			if ((name == self.q[_id]['identifier'] or ('@' in self.q[_id]['identifier'] and name == self.q[_id]['identifier'].split('@',1)[0]))) and not self.q[_id]['times']['finished']:
				self.q[_id]['times']['finished'] = time()
				return _id, self.q[_id]['identifier']
		return None, None

	def queuetime(self, which=None):
		cats = {}
		cattimes = {}
		for _id in range(0, self.settings['queuepos']+1):
			start = self.q[_id]['times']['accepted']
			end = self.q[_id]['times']['finished']
			cat = self.q[_id]['task'][0]
			if not end:
				continue
			if not cat in cats:
				cats[cat] = []

			totaltime = end - start
			cats[cat].append(totaltime)
		for cat in cats:
			times = 0
			for t in cats[cat]:
				times += t
			cattimes[cat] = times/len(cats[cat])
		if which:
			return cattimes[which]
		else:
			return cattimes

	def add(self, source, identifier, task, working=5):
		queuepos = self.get_queuepos()
		self.q[queuepos] = {
			'source' : source,
			'identifier' : identifier,
			'task' : task,
			'times' : {'reg' : time(), 'finished' : None, 'accepted' : None},
		}
		times = self.queuetime()
		if len(times) == 0 and queuepos < working:
			return queuepos, '~2 min (start walking towards Support@D-Hallen)'
		else:
			return (queuepos, ''.join(humantime(times[task[0]])))

	def notify(self, workers=2):
		times = self.queuetime()
		notify = []

		## First we calculate the ammount of busy workers
		working = 0
		for w in range(self.settings['queuepos']-workers, self.settings['queuepos']+1):
			if w <= 0: continue
			case = self.q[w]
			if case['times']['finished'] == None and case['times']['accepted']:
				working += 1


		## Then we find out how many cases are currently xx % completed.
		for w in range(self.settings['queuepos']-workers, self.settings['queuepos']+1):
			if w <= 0: continue
			if len(notify) > workers-working: break

			case = self.q[w] # case data, returned as a map		

			## Case is already completed, don't count for anything	
			if case['times']['accepted'] and case['times']['finished']:
				continue

			t = case['task'][0] # case type
			accepted = case['times']['accepted'] # time when case was accepted
			maxofcasetypeintime = times[t] # maximum avrage time of the case type
			percentage = 100.0/maxofcasetypeintime

			if percentage*(time() - accepted) >= self.settings['notifypercentage']:
				if not int(w) in notify:
					print 'Appending #1 -',int(w),case
					notify.append(int(w))

		if working < workers:
			for i in range(self.settings['queuepos']+len(notify), self.settings['queuepos']+len(notify)+working+1):
				if not int(i) in notify and int(i) in self.q:
					if not self.q[int(i)]['times']['accepted']:
						print 'Appending #2 -',int(i),case
						notify.append(int(i))

		if len(notify) > 0:
			for _id in notify:
				case = self.q[_id]
				print strftime('%H:%M:%S') + ' -> Time to notify ' + case['identifier'] + '!'

	def _get(self, back=5):
		queues = []
		unaccepted = []
		accepted = []
		finished = []
		for i in range(0, self.settings['queuepos']+1):
			if self.q[i]['times']['accepted'] and not self.q[i]['times']['finished']:
				accepted.append(str(i) + 'accepted:' + self.q[i]['identifier'] + '@' + self.q[i]['source'])
			elif self.q[i]['times']['accepted'] and self.q[i]['times']['finished']:
				finished.append(str(i) + 'finished:' + self.q[i]['identifier'] + '@' + self.q[i]['source'])
			else:
				unaccepted.append(str(i) + ':unaccepted:' + self.q[i]['identifier'] + '@' + self.q[i]['source'])

			if len(unaccepted) >= back:
				break

		for q in unaccepted[:back]:
			queues.append(q)
		if len(queues) < back:
			for q in accepted[0-(back-len(queues)):]:
				queues.append(q)
		if len(queues) < back:
			for q in finished[0-(back-len(queues)):]:
				queues.append(q)

		return queues

	def get_queuepos(self):
		self.settings['queuepos'] += 1
		return self.settings['queuepos']

	def accept(self, _id):
		if not self.q[_id]['times']['accepted']:
			self.q[_id]['times']['accepted'] = time()

	def complete(self, _id):
		if not self.q[_id]['times']['finished']:
			self.q[_id]['times']['finished'] = time()