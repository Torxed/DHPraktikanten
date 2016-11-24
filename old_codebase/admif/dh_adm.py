import pyglet
from pyglet.gl import *
from time import sleep, time
from threading import *
from socket import *
from os import _exit
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from random import randint, random

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LINE_SMOOTH)
glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)

pyglet.clock.set_fps_limit(30)

DEBUG = 1

#core = {'pickle_ignore' : {'password' : None}}


def refstr(s):
	return s.strip(" \t:,\r\n\"'")

def pad(s, p=None):
	pos = 0
	if not p:
		p = core['pickle_ignore']['password']
	BLOCK_SIZE = 32
	while float(len(s))/float(BLOCK_SIZE) not in (1.0, 2.0, 3.0):
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

	try:
		decoded = DecodeAES(cipher, what)
	except:
		return what

	passstringbuildup = ''
	for c in p:
		passstringbuildup += c
		while decoded[0-len(passstringbuildup):] == passstringbuildup:
			decoded = decoded[:0-len(passstringbuildup)]
	return decoded

class network(Thread):
	def __init__(self, sock, user, key):
		Thread.__init__(self)
		self.sock = sock
		self.inbuffer = ''
		self.data = {}
		self.lockedbuffer = False
		self.user = user
		self.key = key
		self.start()
		#self.text_sprites = {'name' : {'sprite' : <handle>, 'text' : '...'}}
		self.text_sprites = {}

	def send(self, what):
		if self.sock:
			outid = str(time() + random())
			try:
				self.sock.send(self.user + '%%' + encrypt(outid + '%%' + what, self.key) + '\n')
				return outid
			except:
				return None
		return None

	def disconnect(self):
		try:
			self.sock.close()
		except:
			pass
		del self.sock
		self.sock = None
	def connect(self, host='127.0.0.1', port = 6660):
		self.sock = socket()
		try:
			self.sock.connect(('127.0.0.1', 6660))
			self.sock.send(self.user + '%%' + encrypt('register::push', self.key) + '\n')
			return True
		except Exception, e:
			print Exception, e
			del self.sock
			self.sock = None
			return False

#	def get(self, what=None):
#		print 'Fetching',what
#		print ' Locked buffer'
#		while self.lockedbuffer:
#			sleep(1)
#		self.lockedbuffer = True
#		print ' - Passed'
#
#
#		if not what or what not in self.data:
#			ret = self.inbuffer
#			print ' Missing ID:',ret
#		else:
#			ret = self.data[what]
#			print ' Found ID:',ret
#
#		if len(ret) <= 0:
#			self.lockedbuffer = False
#			print ' Empty buffer, returning'
#			print 'DEBUG:',str(self.data)
#			return ''
#
#		if not what or what not in self.data:
#			self.inbuffer = ''
#		else:
#			print ' Deleting what'
#			del self.data[what]
#
#		self.lockedbuffer = False
#		print ' Returning dec:',ret,decrypt(ret, self.key)
#		return decrypt(ret, self.key)

	def run(self):
		if not self.sock:
			while 1:
				if self.connect():
					break
				else:
					sleep(1)
				
		while 1:
			try:
				data = self.sock.recv(8192)
			except:
				self.disconnect()
				while 1:
					if self.connect():
						break
					else:
						sleep(1)
				continue

			while self.lockedbuffer:
				sleep(1)
			self.lockedbuffer = True

			for line in data.split('\n'):
				if len(line) <= 0: continue
				print '<<',line

				if '%%' in line:
					_id, data = line.split('%%',1)
					data = decrypt(data, self.key)
					print '\t<[',data
					if ':' in data:
						cmd, data = data.split(':',1)
						self.text_sprites[cmd] = data
					else:
						print 'Unknown data'
				else:
					print 'Network delivered to inbuffer (missing ID)'
					self.inbuffer += line

			self.lockedbuffer = False
			sleep(1)

def hextoint(i):
	if i > 255:
		i = 255
	return (1.0/255.0) * i

class clip():
	def __init__(self, x, y, width, height, maxwidth):
		self.x = 0
		self.y = 0
		self.width = width
		self.height = height
		self.maxwidth = maxwidth

	def reset(self):
		self.x = 0
		self.y = 0

	def slice(self, num):
		self.x = (self.width*num)%self.maxwidth

	def next(self):
		self.x = (self.x+self.width)%self.maxwidth

	def get(self):
		return (self.x, self.y, self.width, self.height)

class window():
	def __init__(self, network=None, background = None, menu = None, menu_items = [], startpos=(0,0)):
		self.sprites = {}
		self.menuitem = {}
		self.objects = {}
		self.layers = {}
		self.textobjects = []
		self.network = network

		## ============ Process:
		## * Add the desired background-image
		## * Add the sprite based on that image
		## * Add the sprite-name as a layer id to layers['name'] = <id>
		## --- After the layout is done, populate the menu by doing ---
		## * First, get the layer-id and share it across the items
		## * Loop through each menu-item-name and store an image of it in self.menuitem
		## * store the menu-item-name-IMAGE in self.sprites with a clip value of X
		##   (later, when pressing the image, clip value will have an additional X to
		##	  swap the image shown to something else, example: 40x40 clip, will be 80x40
		##    and the image will contain "plain button" at 40x40 and "active" on 80x40)
		## --- Once the menu is populated, we'll calculate layer ID's for easy access -----
		## * Loop through layer-names and get their ID
		## * Store the ID in a new dictionary by   var[ID] = ['name', 'name']
		## --- Last but not least, update the sprite position with the stored position ---
		## * Loop through eacy sprite in self.sprite
		## * Set the position of that sprite.x and sprite.y to sprite.pos.x and sprite.pos.y

		## ===== Build the window-background ===== #
		if background:
			self.background = pyglet.image.load(background)
			# Special step in order to place menu correctly if no background image is given
			self.backgrounddimensions = self.background.width, self.background.height
			self.sprites['background'] = {
							'sprite' : pyglet.sprite.Sprite(self.background.get_region(0, 0, self.background.width, self.background.height)),
							'click' : None,
							'clip' : clip(0, 0, self.background.width, self.background.height, self.background.width),
							'pos' : startpos}
			self.layers['background'] = len(self.layers)-1
		else:
			self.menu = None
			self.backgrounddimensions = 0, 0

		## ==== Build the menu ==== #
		if menu:
			self.menu = pyglet.image.load('menu.png')
			self.sprites['menu'] = {
							'sprite' : pyglet.sprite.Sprite(self.menu.get_region(0, 0, self.menu.width, self.menu.height)),
							'click' : self.menu_click,
							'clip' : clip(0, 0, self.menu.width, self.menu.height, self.menu.width),
							'pos' : (startpos[0]+self.backgrounddimensions[0]-(self.menu.width/2), startpos[1]+self.backgrounddimensions[1]-self.menu.height)}
			self.layers['menu'] = 1000
		else:
			self.menu = None
		
		itempos = 40
		layer = 1001
		for item in menu_items:
			self.menuitem['menu_' + str(item)] = pyglet.image.load(item + '.png')

			self.sprites['menu_' + str(item)] = {
						'sprite' : pyglet.sprite.Sprite(self.menuitem['menu_' + str(item)].get_region(0, 0, 40, 40)),
						'click' : self.button,
						'clip' : clip(0, 0, 40, 40, self.menuitem['menu_' + str(item)].width),
						'pos' : (self.sprites['menu']['pos'][0]+((54-40)/2)+1, self.sprites['menu']['pos'][1]+self.sprites['menu']['sprite'].height-10-itempos)
						}
			itempos += 40
			self.layers['menu_' + str(item)] = layer

		self.layerids = {}
		for layer in self.layers:
			_id = self.layers[layer]
			if not _id in self.layerids:
				self.layerids[_id] = []
			self.layerids[_id].append(layer)

		for sprite in self.sprites:
			self.sprites[sprite]['sprite'].x = self.sprites[sprite]['pos'][0]
			self.sprites[sprite]['sprite'].y = self.sprites[sprite]['pos'][1]

		self.timing = time()

	def build(self, name, _type, pos, layerid=None):
		if not layerid:
			layerid = len(self.layerids)-1
		pos = pos[0] + self.sprites['background']['pos'][0], pos[1] + self.sprites['background']['pos'][1]

		action = None
		if 'list' in _type:
			action = self.list
		elif 'button' in _type:
			action = self.button

		if 'obj_' + str(name) in self.objects:
			## TODO: Don't call build unless a change is made!
			self.objects['obj_' + str(name)] = pyglet.image.load(_type + '.png')
			self.sprites['obj_' + str(name)]['sprite'] = pyglet.sprite.Sprite(self.objects['obj_' + str(name)].get_region(0, 0,  self.objects['obj_' + str(name)].width,  self.objects['obj_' + str(name)].height))
			self.sprites['obj_' + str(name)]['sprite'].x = pos[0]
			self.sprites['obj_' + str(name)]['sprite'].y = pos[1]
		else:
			self.objects['obj_' + str(name)] = pyglet.image.load(_type + '.png')
			self.sprites['obj_' + str(name)] = {
						'sprite' : pyglet.sprite.Sprite(self.objects['obj_' + str(name)].get_region(0, 0,  self.objects['obj_' + str(name)].width,  self.objects['obj_' + str(name)].height)),
						'click' : action,
						'clip' : clip(0, 0, self.objects['obj_' + str(name)].width, self.objects['obj_' + str(name)].height, self.objects['obj_' + str(name)].width),
						'pos' : pos
						}

			txtobj = self.text = pyglet.text.Label(text=name, font_name='Verdana', font_size=8, bold=False, italic=False,
										color=(0, 0, 0, 255), x=pos[0]+10, y=pos[1]+8,
										width=self.objects['obj_' + str(name)].width, height=None, anchor_x='left', anchor_y='baseline',
										multiline=False, dpi=None, batch=None, group=None)
			self.sprites['obj_' + str(name)]['sprite'].x = pos[0]
			self.sprites['obj_' + str(name)]['sprite'].y = pos[1]

			self.textobjects.append(txtobj)

			self.layers['obj_' + str(name)] = layerid
			if not layerid in self.layerids:
				self.layerids[layerid] = []
			if not 'obj_' + str(name) in self.layerids[layerid]:
				self.layerids[layerid].append('obj_' + str(name))

	def menu_click(self, item):
		_id = self.network.send('get::queue::5')
		for i in range(0,5):
			print 'get::queue = ' + _id
			data = self.network.get(_id)
			if len(data) > 0:
				break
			sleep(0.01)

		starter = 360
		for queueid in data.replace('\n', '').split(';'):
			if len(queueid) <= 0: continue
			self.build(queueid, 'list_new', (self.sprites['background']['sprite'].x,self.sprites['background']['sprite'].y + starter))
			starter -= 27

	def list(self, item):
		name = item.split('_')[1]
		print 'List was clicked:',name
		_id = self.network.send('update::queue::' + name)

	def button(self, item):
		for sprite in self.sprites:
			if 'menu_' in sprite:
				if item in sprite:
					self.sprites[sprite]['clip'].slice(2)
				else:
					self.sprites[sprite]['clip'].reset()
				self.sprites[sprite]['sprite'].image = self.menuitem[sprite].get_region(*self.sprites[sprite]['clip'].get())

		print 'Clicked: ' + item

			
		if 'irc' in item:
			_id = self.network.send('get::history::irc::5')
			print str(self.network.text_sprites)
			"""			data = ''
			for i in range(0,5):
				print 'get::history::irc::5 = ' + _id
				data = self.network.get(_id)
				if len(data) > 0:
					break
				sleep(0.01)

			starterx = self.sprites['background']['pos'][0] + 10
			startery = self.sprites['background']['pos'][1]+self.background.height-80
			data = data.replace('\n','')
			self.textobjects = []
			for msg in data.split(';'):
				if len(msg) <= 0: continue

				_from, _msg = msg.split(':',1)
				txtobj = self.text = pyglet.text.Label(text=_from + ': ' + _msg, font_name='Verdana', font_size=8, bold=False, italic=False,
											color=(255, 255, 255, 255), x=starterx, y=startery, width=235, height=None, anchor_x='left', anchor_y='baseline',
											multiline=True, dpi=None, batch=None, group=None)
				self.textobjects.append(txtobj)
				startery -= txtobj.content_height+2
			"""

#			self.windows['queue'].build('Summalajnen', 'list_accepted', (300,433))
#			self.windows['queue'].build('Faern', 'list_done', (300,406))
#			self.windows['queue'].build('Etech', 'list_done', (300,379))

		#else:
		#	self.textobjects = []

	def dummy(self, sprite):
		print 'Dummy called'

	def draw(self):
		for _id in range(min(self.layerids), max(self.layerids)+1):
			if not _id in self.layerids: continue
			layers = self.layerids[_id]
			for layer in layers:
				self.sprites[layer]['sprite'].draw()

		for txt in self.textobjects:
			txt.draw()

	def drag(self, x, y):
		for sprite in self.sprites:
			self.sprites[sprite]['pos'] = self.sprites[sprite]['pos'][0] + x, self.sprites[sprite]['pos'][1] + y

			self.sprites[sprite]['sprite'].x = self.sprites[sprite]['pos'][0]
			self.sprites[sprite]['sprite'].y = self.sprites[sprite]['pos'][1]

		for txt in self.textobjects:
			txt.x = txt.x + x
			txt.y = txt.y + y

	def inside(self, x,y):
		for sprite in self.sprites:
			if x >= self.sprites[sprite]['pos'][0] and x <= self.sprites[sprite]['pos'][0]+self.sprites[sprite]['sprite'].width:
				if y >= self.sprites[sprite]['pos'][1] and y <= self.sprites[sprite]['pos'][1]+self.sprites[sprite]['sprite'].height:
					return True

		return False

	def click(self, x, y):
		clicked = None
		for sprite in self.sprites:
			s = self.sprites[sprite]['sprite']
			sw, sh = s.width, s.height
			if x >= s.x and x <= s.x+sw:
				if y >= s.y and y <= s.y+sh:
					if clicked:
						if self.layers[sprite] > self.layers[clicked]:
							clicked = sprite
					else:
						clicked = sprite
		if clicked and self.sprites[clicked]['click']:
			self.sprites[clicked]['click'](clicked)

	def update(self):
		if time() - self.timing > 0.1:
			self.clipx = (self.clipx+self.clipsize) % self.background.width
			self.sprites['background']['sprite'] = pyglet.sprite.Sprite(self.background.get_region(self.clipx, 0, self.clipsize, 25))
			self.sprites['background']['sprite'].x = self.posx
			self.sprites['background']['sprite'].y = self.posy
			self.timing = time()


class window_job_connectionstatus(Thread):
	def __init__(self, network, sprite, command):
		Thread.__init__(self)

		if sprite == 'text':
			self.data = ''

		self.network = network
		self.command = command

		self.start()

	def run(self):
		while 1:
			_id = self.network.send(self.command)
			data = ''
			for i in range(0,100):
				data = self.network.get(_id)
				if len(data) > 0:
					break
				sleep(0.1)

			self.data = data

def label(text='Unknown'):
	return pyglet.text.Label(text=text, font_name='Verdana', font_size=8, x=10, y=10, multiline=False, width=300)


class gui (pyglet.window.Window):
	def __init__ (self):
		super(gui, self).__init__(1200, 900, fullscreen = False)

		self.colorscheme = {
			'background' : (hextoint(0), hextoint(0), hextoint(0), hextoint(255))
		}
		glClearColor(*self.colorscheme['background'])
		
		self.alive = 1
		user = 'DoXiD'
		key = '\x99\xeaV\xce\xd4|!C\x1d\x0cV\xef\x90O(*\xe4%j\xdba,N\x89\x0bm\xaa\x1ba\xd0\xc3,'
		self.net = network(None, user, key)

		self.bg = pyglet.image.load('background.jpg')

		self.windows = {'social' : window(self.net, 'social_bg.png', 'menu.png', ['facebook', 'twitter', 'irc']),
						'queue' : window(self.net, 'queue_bg.png', 'menu.png', startpos = (300,100))}

		self.console = {'version' : {'text' : label(), 'time' : time()}, 'status' : {'text' : label(), 'time' : time()}}

#		core['pickle_ignore']['password'] = self.key

		self.click = None
		self.drag = False


	def on_draw(self):
		self.render()
		self.flip()

	def on_close(self):
		self.alive = 0

	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		if self.click:
			self.drag = True
			self.click.drag(dx, dy)

	def on_mouse_press(self, x, y, button, modifiers):
		for win in self.windows:
			print 'Checking window: ' + win
			if self.windows[win].inside(x, y):
				print '	- Inside'
				self.click = self.windows[win]

	def on_mouse_release(self, x, y, button, modifiers):
		if not self.drag and self.click:
			self.click.click(x,y)
		
		self.click = None
		self.drag = False

	def on_key_press(self, symbol, modifiers):
		if symbol == 65307:
			#self.markus.close()
			#self.socket.close()
			self.alive = 0
		else:
			print symbol

	def render(self):
		self.clear()
		self.bg.blit(0,0)

		test = ''
		for win in self.windows:
			self.windows[win].draw()

		y = 10
		for key in sorted(self.net.text_sprites):
			val = self.net.text_sprites[key].strip()
			if key == 'queue':
				if len(val) > 1:
					if val[0] == ':':
						val = val[1:]
					qy = 360
					for queueitem in val.split(';'):
						_id, status, user = queueitem.split(':',2)
						self.windows['queue'].build(user.split('@',1)[0], 'list_' + status, (2,qy))
						qy -= 25
			else:
				if not key in self.console:
					self.console[key] = {'text' : label(), 'time' : time()}
				self.console[key]['text'].text = key + ': ' + val
				self.console[key]['time'] = time()
				self.console[key]['text'].y = y
				self.console[key]['text'].draw()
				y += 12

		#self.connectionstatus.text = self.connectionstatus_job.data

		#if self.connectionstatus.text != test:
		#	self.connectionstatus.draw()
		#	test = self.connectionstatus.text

		#self.queue.draw()
		#self.mexgared.update()
		#self.megared.sprite.draw()
		
		#self.megablue.update()
		#self.megablue.posx = 50
		#self.megablue.sprite.draw()

	def run(self):
		#_id = self.net.send('get::version')
		#data = ''
		#for i in range(0,5):
		#	print 'get::version = 0'
		#	data = self.net.get('0')
		#	if len(data) > 0:
		#		break
		#	sleep(0.01)

		#if data != '':
		#	self.versiontxt.text = data

		while self.alive == 1:
			event = self.dispatch_events()
			self.render()
			self.flip()

			sleep(0.01)

x = gui()
x.run()

_exit(1)