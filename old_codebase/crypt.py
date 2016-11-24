#!/usr/bin/env python

from Crypto.Cipher import AES
from getpass import getpass
from base64 import *
import os, sys

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# generate a random secret key
p = getpass('Enter your master password: ')

def pad(s):
	pos = 0
	while float(len(s))/float(BLOCK_SIZE) not in (1.0, 2.0, 3.0):
		s += p[pos]
		pos = (pos +1)%(len(p))
	return s

def EncodeAES(c, s):
	return b64encode(c.encrypt(pad(s)))

def DecodeAES(c, s):
	return c.decrypt(b64decode(s)).replace(p,'')

cipher = AES.new(pad(p))

# encode a string
encoded = EncodeAES(cipher, pad(sys.argv[1]))
print 'Encrypted string:', encoded

# decode the encoded string
decoded = DecodeAES(cipher, encoded)
print 'Decrypted string:', decoded
