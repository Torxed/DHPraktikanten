import pyglet
from pyglet.gl import *
from time import sleep, time
from threading import *
from socket import *
from os import _exit

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LINE_SMOOTH)
glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)

pyglet.clock.set_fps_limit(30)

class network(Thread):
	def __init__(self, sock):
		Thread.__init__(self)
		self.sock = sock
		self.inbuffer = ''
		self.lockedbuffer = False
		self.start()

	def send(self, what):
		if self.sock:
			try:
				self.sock.send(what+'\n')
				return True
			except:
				return False
		return False

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
			return True
		except:
			del self.sock
			self.sock = None
			return False
	def get(self):
		while self.lockedbuffer:
			print 'sleeping get'
			sleep(1)
		print 'Get Locking'
		self.lockedbuffer = True
		ret = self.inbuffer
		if len(ret) <= 0:
			self.lockedbuffer = False
			return ''

		if not ret[-1] == '\n':
			ret = ret[ret.rfind('\n')]
			self.inbuffer = self.inbuffer[len(ret):]
		else:
			self.inbuffer = ''
		print 'Get Unlocking'
		self.lockedbuffer = False
		return ret

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

			while self.lockedbuffer:
				print 'sleeping recv'
				sleep(1)
			print 'Sleeping Locking'
			self.lockedbuffer = True
			self.inbuffer += data
			print 'Sleeping Unlocking'
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
			self.layers['menu'] = len(self.layers)-1
		else:
			self.menu = None
		
		itempos = 40
		layer = len(self.layers)-1
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

		action = None
		if 'list' in _type:
			action = self.list
		elif 'button' in _type:
			action = self.button

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
		self.network.send('get::queue::5\n')
		for i in range(0,5):
			data = self.network.get()
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
		self.network.send('update::queue::' + name + '\n')

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
			self.network.send('get::history::irc::5\n')
			data = ''
			for i in range(0,5):
				data = self.network.get()
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


#			self.windows['queue'].build('Summalajnen', 'list_accepted', (300,433))
#			self.windows['queue'].build('Faern', 'list_done', (300,406))
#			self.windows['queue'].build('Etech', 'list_done', (300,379))

		#else:
		#	self.textobjects = []

	def dummy(self, sprite):
		print 'Dummy called'

	def draw(self):
		for _id in range(min(self.layerids), max(self.layerids)+1):
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

class gui (pyglet.window.Window):
	def __init__ (self):
		super(gui, self).__init__(1920, 1080, fullscreen = True)

		self.colorscheme = {
			'background' : (hextoint(0), hextoint(0), hextoint(0), hextoint(255))
		}
		glClearColor(*self.colorscheme['background'])
		
		self.alive = 1
		self.net = network(None)

		self.bg = pyglet.image.load('background.jpg')

		self.windows = {'social' : window(self.net, 'social_bg.png', 'menu.png', ['facebook', 'twitter', 'irc']),
						'queue' : window(self.net, 'queue_bg.png', 'menu.png', startpos = (300,100))}

		self.click = None
		self.drag = False

	def run(self):
		while self.alive == 1:
			self.render()
			event = self.dispatch_events()

	def on_draw(self):
		self.render()

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

		for win in self.windows:
			self.windows[win].draw()

		#self.queue.draw()
		#self.megared.update()
		#self.megared.sprite.draw()

		#self.megablue.update()
		#self.megablue.posx = 50
		#self.megablue.sprite.draw()

		self.flip()


class backend_for_test(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.alive = 1
		self.start()

	def run(self):
		s = socket()
		s.bind(('127.0.0.1', 6660))
		s.listen(4)

		ns, na = s.accept()

		while self.alive:
			x = ns.recv(8192)
			#print 'Socket got:',x
			ns.send('DoXiD:Testing testing! :D;DoXiD:Verkar fungera..;Summalajnen:Tja!\n')
			#print 'Sent!'

#b = backend_for_test()

x = gui()
x.run()

_exit(1)