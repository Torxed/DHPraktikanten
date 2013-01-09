from socket import *
from config import *
from time import time, sleep
from base64 import b64encode
from hashlib import sha1
from urllib import quote
from getpass import getpass
from helpers import *
import json
import hmac

class OAuth():
	def __init__(self, host):
		self.host = host
		self.cookies = {}

	def eatcookie(self, data):
		cookie, trash = data.split(';',1)
		name, value = cookie.split('=',1)
		self.cookies[name] = value

	def get(self, url='/oauth/request_token'):
		url = 'POST ' + url + ' HTTP/1.1'
		header = {'User-Agent' : 'foobar',
					'Host' : self.host,
					'Accept' : '*/*',
					'Authorization' : 'OAuth'}
		OAuthdata = {'oauth_callback' : 'http://127.0.0.1',
					'oauth_consumer_key' : decrypt(core['cco']['consumer_key']),
					'oauth_nonce' : uniqueueid(),
					'oauth_timestamp' : str(int(time())),
					'oauth_signature_method' : 'HMAC-SHA1',
					'oauth_version' : '1.0'}

		if len(self.cookies) > 0:
			header['Cookie'] = ''
			for cookie, value in self.cookies.items():
				header['Cookie'] += cookie + '=' + value + '; '
			header['Cookie'] = header['Cookie'][:-2]

		if len(core['cco']['access_key']) > 0:
			OAuthdata['oauth_token'] = core['cco']['access_key']
			del OAuthdata['oauth_callback']

		signstring = ''
		signstring += url.split(' ')[0] + '&' + quote('http://' + self.host + url.split(' ')[1]).replace('/', '%2F') + '&'

		values = ''
		first = True
		for item in sorted(OAuthdata):
			val = OAuthdata[item]

			## ===> We double-escape these two strings for some reason.
			##
			## meaning, http:// will become http%XX%XX%XX but then we
			## escape % again so it will be http%YYxx%YYxx%YYxx
			##
			if item in ('oauth_callback', 'oauth_nonce'):
				val = urlfix(val)

			if first:
				values += urlfix(item + '=' + val)
				first = False
			else:
				values += urlfix('&' + item + '=' + val)

		signstring += values
		signature = b64encode(hmac.new(decrypt(core['cco']['consumer_secret'])+'&'+core['cco']['access_secret'], signstring, sha1).digest())
		
		OAuthdata['oauth_signature'] = signature

		requeststring = url + '\r\n'
		for k, v in header.items():
			if k == 'Authorization': continue
			requeststring += k + ': ' + v + '\r\n'
		requeststring += 'Authorization: Oauth '
		for k, v in OAuthdata.items():
			v = OAuthdata[k]
			requeststring += urlfix(k) + '="' + urlfix(v) + '",'
		requeststring = requeststring[:-1]+'\r\n' # Trailing ,
		requeststring += '\r\n' #Ending headers

		s = socket()
		s.connect((self.host, 80))
		s.send(requeststring)

		datahandle = nonblockingrecieve(s)
		loops = 0
		last = 'X'
		data = ''
		while loops <= 10 and time() - datahandle.lastupdate:
			d = datahandle.data
			if d != last:
				loops = 0
				data = d
				last = data
			else:
				loops += 1
			sleep(0.25)

		datahandle._Thread__stop()
		#datahandle._Thread__delete()
		try:
			headers, d = data.split('\r\n\r\n')
		except:
			print [data]
			return {}

		for row in headers.split('\r\n'):
			if len(row) <= 0: continue
			if not ':' in row: continue # most likely HTTP/1.1 status code
			k, v = row.split(':',1)
			k, v = refstr(k).lower(), refstr(v)
			if k == 'set-cookie':
				self.eatcookie(v)

		s.close()
		return json.loads(d)

if __name__ == '__main__':
	if not 'password' in core['pickle_ignore']:
		core['pickle_ignore']['password'] = getpass('Enter master password: \n')

	x = OAuth('api.crew.dreamhack.se')
	tokens = x.get()
	core['cco']['access_key'] = str(tokens['oauth_token'])
	core['cco']['access_secret'] = str(tokens['oauth_token_secret'])
	print x.get('/1/event/get/all')
	print x.get('/1/user/get/635') # <- broke