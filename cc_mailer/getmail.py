import imaplib, re


def refstr(s):
	return s.strip(" \t:,\r\n\"'")

def getfrom(data):
	start = data.lower().find('from: ')
	end = data.find('\n',start)
	_from = re.findall('[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', refstr(data[start:end]))[0]
	return _from

def getmailinglist(usr, pwd):
	people = []
	mail = imaplib.IMAP4_SSL('imap.gmail.com')
	mail.login(usr, pwd)
	#listoflables = mail.list()
	mail.select('Watchdog')

	i = 1
	msg_data = True

	while msg_data:
		_type, msg_data = mail.fetch(str(i), '(RFC822)') # To get labledata: (X-GM-LABELS)
		msg_data = msg_data[0]

		if msg_data:
			for item in msg_data:
				if 'from' in item.lower():
					people.append(getfrom(item))

		i += 1
	return people
