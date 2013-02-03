core = {
	'sender' : None,
	'outqueue' : {},
	'pickle' : {'flags' : {'dblock' : False},
				'conversation' : {},
				'stored_conversations' : {},
				'prio' : None, # <- Find what this does!
				},
	'pickle_ignore' : {},

	'email' : {'user' : '', # ./helpers.py user@email.com
				'pass' : '',}, #./helpers.py password
				
	'cco' : {'consumer_key' : '',
				'consumer_secret' : '',
				'access_key' : '',
				'access_secret' : '',},

	'twitter' : {'consumer_key' : '',
				'consumer_secret' : '',
				'access_key' : '',
				'access_secret' : '',},
}
