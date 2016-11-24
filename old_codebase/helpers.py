import os, errno
from threading import *
from Crypto.Cipher import AES
from urllib import quote_plus
from base64 import b64encode, b64decode
from random import randint
from time import strftime, time
from config import core

def refstr(s):
	return s.strip(" \t:,\r\n\"'")

def pid_exists(pid):
	"""Check whether pid exists in the current process table."""
	if pid < 0:
		return False
	try:
		os.kill(pid, 0)
	except OSError, e:
		return e.errno == errno.EPERM
	else:
		return True

def getEvents(data):
	import unicodedata
	evlist = []
	for item in data:
		evlist.append(str(unicodedata.normalize('NFKD', item['name']).encode('iso-8859-15','replace').decode('utf-8', 'replace')))
	return evlist

def uniqueueid(l = 22):
	s = strftime('%Y-%d-%m %H:%M:%S')
	while len(s) < l:
		s += str(randint(0,1000))
	return b64encode(s)

def frange3(start, end=None, inc=None):
	"""A range function, that does accept float increments..."""
	import math

	if end == None:
		end = start + 0.0
		start = 0.0
	else: start += 0.0 # force it to be a float

	if inc == None:
		inc = 1.0
	count = int(math.ceil((end - start) / inc))

	L = [None,] * count

	L[0] = start
	for i in xrange(1,count):
		L[i] = L[i-1] + inc
	return L

def pad(s, p=None):
	pos = 0
	if not p:
		p = core['pickle_ignore']['password']
	BLOCK_SIZE = 32
	while float(len(s))/float(BLOCK_SIZE) not in frange3(1.0, 800.0):
		s += p[pos]
		pos = (pos +1)%(len(p))
	return s

def encrypt(what, p = None):
	if not p:
		p = core['pickle_ignore']['password']
	EncodeAES = lambda c, s: b64encode(c.encrypt(pad(s, p)))
	cipher = AES.new(pad(p, p))
	return EncodeAES(cipher, what)

def decrypt(what, p = None):
	if not p:
		p = core['pickle_ignore']['password']

	DecodeAES = lambda c, e: c.decrypt(b64decode(e))
	cipher = AES.new(pad(p, p))
	decoded = DecodeAES(cipher, what)

	passstringbuildup = ''
	for c in p:
		passstringbuildup += c
		while decoded[0-len(passstringbuildup):] == passstringbuildup:
			decoded = decoded[:0-len(passstringbuildup)]
	return decoded

def urlfix(s):
	return quote_plus(s)

def refstr(s):
	return s.strip(" \t:,\r\n\"'")

class nonblockingrecieve(Thread):
	def __init__(self, sock):
		self.sock = sock
		self.data = ''
		self.lastupdate = time()
		Thread.__init__(self)
		self.start()

	def run(self):
		while True:
			d = self.sock.recv(8192)
			if not d:
				break
			self.data += d
			self.lastupdate = time()

if __name__ == '__main__':
	import sys
	core['pickle_ignore']['password'] = raw_input('Enter master password: ')
	print sys.argv[1],'=',encrypt(sys.argv[1])
