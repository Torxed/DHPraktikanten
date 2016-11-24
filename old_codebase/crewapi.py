from config import core

rows = {}
for hall in ('A', 'B', 'C', 'D'):
	for i in range(1, 77):
		if not hall in rows:
			rows[hall] = {}
		power = True
		rows[hall][i] = {'power' : power, 'issues' : []}


if not 'rows' in core['pickle']:
	core['pickle']['rows'] = rows
if not 'prio' in core['pickle']:
	core['pickle']['prio'] = []
if not 'powerissues' in core['pickle']:
	core['pickle']['powerissues'] = []


core['pickle']['quickpicks'] = {
	1 : {'title' : 'PC doesn\'t boot at all',
			'type' : 'hardware',
		},
	2 : {'title' : 'PC Boots but no image',
			'type' : 'hardware',
		},
	3 : {'title' : 'Cleaning (dusty PC)',
			'type' : 'hardware',
		},
	4 : {'title' : 'Software issue (game issue etc)',
			'type' : 'software',
		},
	5 : {'title' : 'Hardware issue (weird image}, computer creashes etc)',
			'type' : 'hardware',
		},
	6 : {'title' : 'Network issue (Bad or No connection at all)',
			'type' : 'software',
		},
	7 : {'title' : 'Upgrade or Change in PC parts (hardware)',
			'type' : 'hardware',
		},
	8 : {'title' : 'I have no idea what i\'m doing?!',
			'type' : 'software',
		},
	0 : {'title' : 'Other stuff',
			'type' : 'other',
		},
}

core['pickle']['supportscheme'] = {
	'00' : {'end' : '08', 'tech' : ('aSyx', 'MiniErrA')},
	'04' : {'end' : '12', 'tech' : ('ventris', 'vizze')},
	'08' : {'end' : '16', 'tech' : ('Backeman', 'MattiasLj', 'Triggerhappy')},
	'12' : {'end' : '20', 'tech' : ('Fughur', 'jalkmar', 'Käkben', 'level', 'Prozack')},
	'16' : {'end' : '00', 'tech' : ('DD_Rambo', 'Donkey', 'fozzie', 'SUMMALAJNEN')},
	'20' : {'end' : '04', 'tech' : ('DoXiD', 'Exxet', 'Jannibal', 'Miwca')}
}

core['pickle']['supportcases'] = []