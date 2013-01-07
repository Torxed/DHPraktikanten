from os import _exit
from time import strftime
import sys
def log(s, die=False):
	sys.stdout.write(strftime('%Y-%m-%d %H:%M:%S - ' + s + '\n'))
	sys.stdout.flush()
	if die: _exit(1)
