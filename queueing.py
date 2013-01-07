from time import time, sleep, localtime, strftime

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
			#	'times' : {'reg' : time()-(60*10), 'finished' : time()-(60*5), 'accepted' : time()-(60*10)},
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

	def add(self, source, identifier, task):
		self.q[len(self.q)+1] = {
			'source' : source,
			'identifier' : identifier,
			'task' : task,
			'times' : {'reg' : time(), 'finished' : None, 'accepted' : None},
		}
		times = self.queuetime()
		if len(times) == 0:
			return 1, '2 min'
		else:
			return (len(self.q)+1) - self.settings['queuepos'], ''.join(humantime(times[task[0]]))

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


	def get(self):
		self.settings['queuepos'] += 1
		return self.q[self.settings['queuepos']]

	def accept(self, _id):
		if not self.q[_id]['times']['accepted']:
			self.q[_id]['times']['accepted'] = time()

	def complete(self, _id):
		if not self.q[_id]['times']['finished']:
			self.q[_id]['times']['finished'] = time()