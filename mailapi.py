import imaplib, re, smtplib
from config import core
from logger import *
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

def refstr(s):
	return s.strip(" \t:,\r\n\"'")

def getfrom(data):
	start = data.lower().find('from: ')
	end = data.find('\n',start)
	_from = re.findall('[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', refstr(data[start:end]))[0]
	return _from

class Mail():
	def __init__(self):
		log('Engine started', 'Email')

	def send(self, to, subject, text, attach=None):
		msg = MIMEMultipart()

		msg['From'] = core['email']['user']
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
		mailServer.login(core['email']['user'], core['email']['pass'])
		mailServer.sendmail(core['email']['user'], to, msg.as_string())
		log('Sending e-mail to ' + to,'Email')
		# Should be mailServer.quit(), but that crashes...
		mailServer.close()

		return True

	def getmailinglist(self):
		people = []
		mail = imaplib.IMAP4_SSL('imap.gmail.com')
		mail.login(core['email']['user'], core['email']['pass'])
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
						people.append((getfrom(item), item))

			i += 1
		return people
