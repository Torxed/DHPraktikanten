from os import _exit
from time import strftime
import sys
def log(s, source='', die=False):
	if len(source) > 0:
		source = '[' + source + '] '
	sys.stdout.write(strftime('%Y-%m-%d %H:%M:%S - ' + source + s + '\n'))
	sys.stdout.flush()
	if die: _exit(1)
