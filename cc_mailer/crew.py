#!/usr/bin/python
import socket, ssl, re, sys, smtplib
from threading import *
from os import _exit
from os.path import isfile
from time import sleep, time, strftime
from urllib import urlencode, quote_plus
from getpass import getpass
from logger import log
from pickle import load, dump
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from getmail import *

__date__ = '2013-01-07 15:10 CET'
__version__ = '0.0.1'
__author__ = 'Anton Hvornum - http://www.linkedin.com/profile/view?id=140957723'

__customerUSR__ = ''
__customerPWD__ = ''#decrypt('')

gmail_user = ""
gmail_pwd = ""

log('Initated the script')
if not isfile('dh.db'):
	eventdb = []
else:
	f = open('dh.db','rb')
	eventdb = load(f)
	f.close()
log('DB loaded')

log('Getting mailinglist')
mailinglist = getmailinglist(gmail_user, gmail_pwd)

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
			d = self.sock.read()
			if not d:
				break
			self.data += d
			self.lastupdate = time()

class httplib():
	def __init__(self, htmldata):
		self.htmldata = htmldata
		self.sock = None
		self.cookies = {}
		self.lasturl = 'https://' + self.htmldata['host'] + '/'

	def connect(self):
		if not self.sock:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock = ssl.wrap_socket(s)
			self.sock.connect((self.htmldata['host'], 443))

	def eatcookie(self, data):
		cookie, trash = data.split(';',1)
		name, value = cookie.split('=',1)
		self.cookies[name] = value

	def parse(self, data):
		headers = {}
		if not '\r\n\r\n' in data:
			print 'Bad data:',[data]
			sys.stdout.flush()
			return None, None
		head, data = data.split('\r\n\r\n',1)
		for row in head.split('\r\n'):
			if len(row) <= 0: continue
			if not ':' in row: continue # most likely HTTP/1.1 status code
			k, v = row.split(':',1)
			k, v = refstr(k).lower(), refstr(v)
			if k == 'set-cookie':
				self.eatcookie(v)
			else:
				headers[k] = v
		return headers, data

	def sendrecieve(self, data):
		self.connect()
		self.sock.write(data)
		datahandle = nonblockingrecieve(self.sock)
		loops = 0
		last = 'X'
		data = ''
		while loops <= 10 and time() - datahandle.lastupdate:
			d = datahandle.data
			if d != last:
				loops = 0
				data = d
				last = data
				if '</html>' in data.lower():
					break
			else:
				loops += 1
			sleep(0.25)
		del last
		del loops
		try:
			datahandle._Thread__stop()
		except:
			pass
		try:
			datahandle._Thread__delete()
		except:
			pass

		self.disconnect()
		return data

	def disconnect(self):
		self.sock.close()
		self.sock = None

	def postformat(self):
		outdata = ''
		for k, v in self.htmldata['form'].items():
			outdata += k + '=' + quote_plus(v) + '&'
		outdata = outdata[:-1]
		return outdata

	def navigate(self):
		if 'inform' in self.htmldata and self.htmldata['inform']:
			log(self.htmldata['inform'])
		outdata = ''
		postdata = None

		if self.htmldata['type'] == 'GET':
			#print ' * Getting ' + self.htmldata['target']
			outdata += 'GET ' + self.htmldata['target'] + ' HTTP/1.1\r\n'
		else:
			outdata += 'POST ' + self.htmldata['target'] + ' HTTP/1.1\r\n'
			postdata = self.postformat()
			if not postdata:
				print 'Problem formatting the POST data'
				sys.stdout.flush()
				return None
			outdata += 'Content-Length: ' + str(len(postdata)) + '\r\n'
			outdata += 'Content-Type: application/x-www-form-urlencoded\r\n'
			outdata += 'Referer: https://' + self.htmldata['host'] + self.htmldata['target'] + '\r\n'

		outdata += 'Host: ' + self.htmldata['host'] + '\r\n'
		if len(self.cookies) > 0:
			outdata += 'Cookie: '
			for cookie, value in self.cookies.items():
				outdata += cookie + '=' + value + '; '
			outdata = outdata[:-2] + '\r\n'

		outdata += 'Accept-Encoding: text\r\n'
		outdata += 'User-Agent: Autoupdater/0.1 (X11; Linux i686) Own/20121204 AutoUpdater/0.1\r\n'
		outdata += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n'
		outdata += 'Connection: keep-alive\r\n'
		outdata += '\r\n'
		if postdata:
			outdata += postdata

		data = self.sendrecieve(outdata)

		headers, data = self.parse(data)
		if headers:
			if 'location' in headers:
				self.htmldata['type'] = 'GET'
				self.lastupdate = 'https://' + self.htmldata['host'] + self.htmldata['target']
				self.htmldata['target'] = headers['location']
				return self.navigate()
			else:
				self.lastupdate = 'https://' + self.htmldata['host'] + self.htmldata['target']
		return headers, data

def mail(to, subject, text, attach=None):
	msg = MIMEMultipart()

	msg['From'] = gmail_user
	msg['To'] = to
	msg['Subject'] = subject

	msg.attach(MIMEText(text))

	if attach:
		part = MIMEBase('application', 'octet-stream')
		part.set_payload(open(attach, 'rb').read())
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition',
				'attachment; filename="%s"' % os.path.basename(attach))
		msg.attach(part)

	mailServer = smtplib.SMTP("smtp.gmail.com", 587)
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(gmail_user, gmail_pwd)
	mailServer.sendmail(gmail_user, to, msg.as_string())
	# Should be mailServer.quit(), but that crashes...
	mailServer.close()

def getSafetyHash(data):
	start = data.find('safetyhash')
	end = data.find('>',start)
	data = data[start:end]
	for val in data.split(' '):
		if '=' in val:
			k,v = val.split('=')
			k,v = refstr(k),refstr(v)
			if k=='value':
				return v
	#input type="hidden" class="safetyhash hidden" name="hash" value="6e0fd51feedf00560c2e20787ce72e1d07b6bdfb" />

def getEvents(data):
	start = data.find('<select')
	end = data.find('</select',start)

	data = data[start:end]
	options = re.findall(r"<option*.*</option>", data)
	cleaned = []
	for opt in options:
		opt = opt.replace('</option>', '')
		opt = opt.replace(re.findall(r"<*.*>", opt)[0], '')
		cleaned.append(opt)
	return cleaned

class Pages():
	def __init__(self):
		pass
	def root(self):
		return {
				'host' : 'crew.dreamhack.se',
				'target' : '/',
				'type' : 'GET',
				'form' : {},
				'inform' : 'Imitating login form retreival',
				}

	def dologin(self):
		return {
				'host' : 'crew.dreamhack.se',
				'target' : '/login.htm',
				'type' : 'POST',
				'form' : {'signin_username' : __customerUSR__,
							'signin_password' : __customerPWD__,
							'hash' : '',
							'button' : 'Logga in'},
				'inform' : 'Sending logininformation',
				}


## Pages is a class to build and return
## dictionary data used by the .navigate() function.
pages = Pages()

http = httplib(pages.root())
d = http.navigate()[1]
safetyhash = getSafetyHash(d)

http.htmldata = pages.dologin()
http.htmldata['form']['hash'] = safetyhash

inside_data = http.navigate()

events = getEvents(inside_data[1])

new = []
for e in events:
	if not e in eventdb:
		new.append(e)
		eventdb.append(e)
		log('New event: ' + str(e))

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

	for person in mailinglist:
		if len(person) <= 0 or '@' not in person: continue

		log('Sending mail to: ' + person)
		mail(person,
			t,
			m + " has been created on CC, apply for your position now!\n\n" + l)

for t in enumerate():
	try:
		t._Thread__delete()
	except:
		pass

f = open('dh.db', 'wb')
dump(eventdb, f)
f.close()
log('DB saved')

_exit(0)
