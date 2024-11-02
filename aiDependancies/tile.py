# corresponding strings for rendering tiles
tileCharacters = {
	'g': "    ",
	'w': "xxxx",
	'r': " :D ",
	'b': "<<>>",
	'o': ">><<",
	'y': "(())",
	'p': "))(("
}

tileCategories = {
	'g': "EMPTY",
	'w': "WALL",
	'r': "EXIT",
	'b': "TRANSPORTER",
	'o': "TRANSPORTER",
	'y': "TRANSPORTER",
	'p': "TRANSPORTER",
	'0': "GOAL",
	'1': "GOAL",
	'2': "GOAL",
	'3': "GOAL",
	'4': "GOAL",
	'5': "GOAL",
	'6': "GOAL",
	'7': "GOAL",
	'8': "GOAL",
	'9': "GOAL"
}

transporterPairs = {
	'b': 'o',
	'o': 'b',
	'y': 'p',
	'p': 'y'
}

class Tile:
	def __init__(self, x=0, y=0, cellType='g', layer = 0):
		self.relativePosition = [x, y, layer] # position in the agent's coordinate system
		self.type = cellType                  # character corresponding to the cell type
		self.relations = {
			'N': None,
			'S': None,
			'E': None,
			'W': None
		}
		self.tileCategory = tileCategories[cellType] or "UNKNOWN"

		if self.tileCategory == "TRANSPORTER" and ('U' not in self.relations.keys()):
			self.relations['U'] = None
	
	def hasUnknowns(self):
		# if self.tileCategory == "TRANSPORTER":
		# 	# print(self.relations.values())
		return ( None in self.relations.values() ) and ( self.type != 'w' )
		# return ( None in self.relations.values() )

	def numUnknowns(self):
		# tallies unknowns to weight searching
		count = 0
		for tile in self.relations.values():
			if not tile:
				count += 1
		return count

	def __del__(self):
		del self.relations
	# again, just some code for terminal output
	def __str__(self):
		if self.type not in tileCharacters.keys(): return str(self.type)
		if self.tileCategory in ("EMPTY", "TRANSPORTER"): return "".join(list(map(lambda key: key if self.relations[key] == None else ' ', self.relations.keys())))
		return tileCharacters[self.type]
