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
		self.sock.send(what+'\n')

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
		while 1:
			data = self.sock.recv(8192)
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


class social_window():
	def __init__(self, network=None):
		self.background = pyglet.image.load('social_bg.png')
		self.menu = pyglet.image.load('menu.png')

		self.menuitem = {}
		self.menuitem['menu_facebook'] = pyglet.image.load('facebook.png')
		self.menuitem['menu_twitter'] = pyglet.image.load('twitter.png')
		self.menuitem['menu_irc'] = pyglet.image.load('irc.png')

		self.textobjects = []

		self.network = network

		self.sprites = {}
		self.sprites['background'] = {
						'sprite' : pyglet.sprite.Sprite(self.background.get_region(0, 0, self.background.width, self.background.height)),
						'click' : None,
						'clip' : clip(0, 0, self.background.width, self.background.height, self.background.width),
						'pos' : (0, 0)
						}
		self.sprites['menu'] = {
						'sprite' : pyglet.sprite.Sprite(self.menu.get_region(0, 0, self.menu.width, self.menu.height)),
						'click' : None,
						'clip' : clip(0, 0, self.menu.width, self.menu.height, self.menu.width),
						'pos' : (286-27, 444-228)
						}
		self.sprites['menu_facebook'] = {
						'sprite' : pyglet.sprite.Sprite(self.menuitem['menu_facebook'].get_region(0, 0, 40, 40)),
						'click' : self.button,
						'clip' : clip(0, 0, 40, 40, self.menuitem['menu_facebook'].width),
						'pos' : (self.sprites['menu']['pos'][0]+((54-40)/2)+1, self.sprites['menu']['pos'][1]+self.sprites['menu']['pos'][1]-40)
						}
		self.sprites['menu_twitter'] = {
						'sprite' : pyglet.sprite.Sprite(self.menuitem['menu_twitter'].get_region(0, 0, 40, 40)),
						'click' : self.button,
						'clip' : clip(0, 0, 40, 40, self.menuitem['menu_twitter'].width),
						'pos' : (self.sprites['menu']['pos'][0]+((54-40)/2)+1, self.sprites['menu']['pos'][1]+self.sprites['menu']['pos'][1]-80)
						}
		self.sprites['menu_irc'] = {
						'sprite' : pyglet.sprite.Sprite(self.menuitem['menu_irc'].get_region(0, 0, 40, 40)),
						'click' : self.button,
						'clip' : clip(0, 0, 40, 40, self.menuitem['menu_irc'].width),
						'pos' : (self.sprites['menu']['pos'][0]+((54-40)/2)+1, self.sprites['menu']['pos'][1]+self.sprites['menu']['pos'][1]-120)
						}


		self.layers = {'background' : 0, 'menu' : 1, 'menu_facebook' : 2, 'menu_twitter' : 2, 'menu_irc' : 2}
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

	def button(self, item):
		for sprite in self.sprites:
			if 'menu_' in sprite:
				if item in sprite:
					self.sprites[sprite]['clip'].slice(2)
				else:
					self.sprites[sprite]['clip'].reset()
				self.sprites[sprite]['sprite'].image = self.menuitem[sprite].get_region(*self.sprites[sprite]['clip'].get())

		if 'irc' in item:
			self.network.send('get::history::irc::5\n')
			data = ''
			for i in range(0,5):
				data = self.network.get()
				print [data]
				if len(data) > 0:
					break
				sleep(0.01)

			starterx = self.sprites['background']['pos'][0] + 10
			startery = self.sprites['background']['pos'][1]+self.background.height-80
			data = data.replace('\n','')
			for msg in data.split(';'):
				if len(msg) <= 0: continue

				_from, _msg = msg.split(':',1)
				txtobj = self.text = pyglet.text.Label(text=_from + ': ' + _msg, font_name='Verdana', font_size=8, bold=False, italic=False,
											color=(255, 255, 255, 255), x=starterx, y=startery, width=235, height=None, anchor_x='left', anchor_y='baseline',
											multiline=True, dpi=None, batch=None, group=None)
				self.textobjects.append(txtobj)
				startery -= txtobj.content_height+2
		else:
			self.textobjects = []

	def dummy(self, sprite):
		print 'Dummy called'

	def draw(self):
		for _id in self.layerids:
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
		if x >= self.sprites['background']['pos'][0] and x <= self.sprites['background']['pos'][0]+self.background.width:
			if y >= self.sprites['background']['pos'][1] and y <= self.sprites['background']['pos'][1]+self.background.height:
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
		self.bg = pyglet.image.load('background.jpg')
		self.social = social_window()

		self.click = None
		self.drag = False

		self.socket = socket()
		self.socket.connect(('127.0.0.1', 6660))
		#self.socket.bind(('', 6660))
		#self.socket.listen(4)

		#self.markus, addr = self.socket.accept()

		self.net = network(self.socket)
		self.social.network = self.net

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
		if self.social.inside(x, y):
			self.click = self.social

	def on_mouse_release(self, x, y, button, modifiers):
		if not self.drag:
			self.social.click(x,y)
		
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

		self.social.draw()
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