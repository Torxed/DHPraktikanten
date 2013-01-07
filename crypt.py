#!/usr/bin/env python

from Crypto.Cipher import AES
from getpass import getpass
import base64
import os, sys

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# generate a random secret key
secret = getpass('Enter your master password: ')

def pad(s):
	pos = 0
	while len(s) < BLOCK_SIZE:
		s += secret[pos]
		pos = (pos +1)%len(secret)-1
	return s

# one-liners to encrypt/encode and decrypt/decode a string
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(secret)

# create a cipher object using the random secret
cipher = AES.new(pad(secret))

# encode a string
encoded = EncodeAES(cipher, sys.argv[1])
print 'Encrypted string:', encoded

# decode the encoded string
decoded = DecodeAES(cipher, encoded)
print 'Decrypted string:', decoded
