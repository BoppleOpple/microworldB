from aiDependancies.tile import Tile, transporterPairs
import random

# define how cardinal directions are oriented in the agent's map
directionCoordinates = {
    'N': ( 0, -1),
    'S': ( 0,  1),
    'W': (-1,  0),
    'E': ( 1,  0)
}

# define opposite directions, since it's cheap and easy
directionOpposites = {
    'N': 'S',
    'S': 'N',
    'E': 'W',
    'W': 'E'
}

class Map:
	def __init__(self, layer = 0):
		self.data = [[]]       # map data stored sideways relative to the world, (y, x)
		self.origins = [[0, 0]] # coordinate of "top-left" tile in map, (x, y)
		self.sizes = [[0, 0]]   # bounds of map, (x, y)
		self.landmarks = {}
		self.mergedLayers = []
	
	# function to handle expanding map to accomidate new information, if necessary
	def rememberTile(self, t: Tile = Tile(), update = False):
		self.expandMapForTile(t)
		
		# once expanded, store the tile data
		if (self.tileAt(*t.relativePosition) == None or update):
			self.setTile(t)
		else:
			t = self.tileAt(*t.relativePosition)
		
		# if there are ever 2 landmarks, we found a way to merge layers!
		if (t.tileCategory in ("GOAL", "TRANSPORTER", "EXIT")):
			if (t.type not in self.landmarks):
				self.landmarks[t.type] = t
			elif t.relativePosition[2] != self.landmarks[t.type].relativePosition[2]:
				self.mergeLayers(t.relativePosition, self.landmarks[t.type].relativePosition)
				t = self.landmarks[t.type]

		# register which directions of the tile are known and which are not
		self.updateRelations(self.tileAt(*t.relativePosition))

	def mergeLayers(self, p1, p2):
		# dont merge if we dont have to
		if p1[2] == p2[2]:
			return

		# find the difference in origins
		offset = None
		mergeLayer = -1
		obsoleteLayer = -1
		if p1[2] < p2[2]:
			offset = (
				p1[0] - p2[0],
				p1[1] - p2[1]
			)
			mergeLayer = p1[2]
			obsoleteLayer = p2[2]
		else:
			offset = (
				p2[0] - p1[0],
				p2[1] - p1[1]
			)
			mergeLayer = p2[2]
			obsoleteLayer = p1[2]
		
		# relocate each tile on the old layer
		for line in self.data[obsoleteLayer]:
			for tile in line:
				if tile:
					newPosition = [
						tile.relativePosition[0] + offset[0],
						tile.relativePosition[1] + offset[1],
						mergeLayer
					]
					
					tile.relativePosition = newPosition
					oldTile = self.tileAt(*newPosition)
					
					self.expandMapForTile(tile)
					self.setTile(tile)
		
		# and link them up
		for line in self.data[mergeLayer]:
			for tile in line:
				if tile:
					self.updateRelations(tile)
		# self.data[obsoleteLayer] = []
		
		# remind us to not print the layer again
		self.mergedLayers.append(obsoleteLayer)

	def updateRelations(self, tile: Tile):

		# add each neighbor as a linked list reference
		for direction, offset in directionCoordinates.items():
			opposite = directionOpposites[direction]
			neighbor = self.tileAt(tile.relativePosition[0] + offset[0], tile.relativePosition[1] + offset[1], tile.relativePosition[2])

			tile.relations[direction] = neighbor
			if neighbor:
				neighbor.relations[opposite] = tile
				
		
		# and add the extra transporter dimension
		if tile.tileCategory == "TRANSPORTER":
			other = transporterPairs[tile.type]

			if tile.type not in self.landmarks.keys():
				self.landmarks[tile.type] = tile

			if other not in self.landmarks.keys():
				self.landmarks[other] = Tile(0, 0, other, len(self.data))
				self.rememberTile(self.landmarks[other])

			tile.relations['U'] = self.landmarks[other]
			self.landmarks[other].relations['U'] = self.landmarks[tile.type]

	# since memory is not indexed with coordinates, just make a function to avoid mistakes
	def tileAt(self, x, y, layer = 0):
		if not (layer in range(len(self.sizes)) and x in range(self.origins[layer][0], self.origins[layer][0]+self.sizes[layer][0]) and y in range(self.origins[layer][1], self.origins[layer][1]+self.sizes[layer][1])): return None
		return self.data[layer][y-self.origins[layer][1]][x-self.origins[layer][0]]

	def setTile(self, t: Tile):
		x, y, layer = t.relativePosition
		if not (layer in range(len(self.sizes)) and x in range(self.origins[layer][0], self.origins[layer][0]+self.sizes[layer][0]) and y in range(self.origins[layer][1], self.origins[layer][1]+self.sizes[layer][1])):
			return None
		self.data[layer][y-self.origins[layer][1]][x-self.origins[layer][0]] = t
	
	def expandMapForTile(self, t: Tile):
		layer = t.relativePosition[2]
		# if the tile is "left" of map
		while (layer >= len(self.data)):
			self.data.append([])
			self.sizes.append([0, 0])
			self.origins.append([0, 0])

		# if the tile is "left" of map
		while (t.relativePosition[0] < self.origins[layer][0]):
			for i in range(self.sizes[layer][1]): self.data[layer][i].insert(0, None)
			self.sizes[layer][0] += 1
			self.origins[layer][0] -= 1
		
		# if the tile is "right" of map
		while (t.relativePosition[0] >= self.origins[layer][0] + self.sizes[layer][0]):
			for i in range(self.sizes[layer][1]): self.data[layer][i].append(None)
			self.sizes[layer][0] += 1

		# if the tile is "above" map
		while (t.relativePosition[1] < self.origins[layer][1]):
			self.data[layer].insert(0, [None for i in range(self.sizes[layer][0])])
			self.sizes[layer][1] += 1
			self.origins[layer][1] -= 1
		
		# if the tile is "below" map
		while (t.relativePosition[1] >= self.origins[layer][1] + self.sizes[layer][1]):
			self.data[layer].append([None for i in range(self.sizes[layer][0])])
			self.sizes[layer][1] += 1

		if self.sizes[0][0] > 100:
			pass

	def bft(self, x = 0, y = 0, layer = 0, condition = lambda tile: tile.hasUnknowns(), priority=lambda KVPair: random.random()):
		# store the coordinates of "seen" tiles
		tilesChecked = [(x, y, layer)]

		# store the visitable tiles alongside the path taken to reach them
		tileFrontier = [([], self.tileAt(x, y, layer))]

		# while there are still unsearched tiles
		while tileFrontier:
			# remove a tile
			currentPath, currentTile = tileFrontier.pop(0)
			
			# print(currentTile.relativePosition)

			# move to it if it has an unknown neighbor
			if condition(currentTile):
				return currentPath

			# add unseen neighbors to the frontier if not
			neighbors = []

			# for each direction (in a random order because determinism is less fun)
			for direction, destination in sorted(currentTile.relations.items(), key=priority):
				# add the neighbor in that direction, alongside the updated path to it
				# this neighbor will always be known, since the function would have already returned otherwise

				neighbors.append([
					currentPath + [direction],
					destination
				])
			
			# now, select only those neighbors which are not already in the frontier and aren't walls
			frontierAdditions = list(filter(lambda t: t[1] and t[1].type != 'w' and t[1].relativePosition not in tilesChecked, neighbors))

			# and add those to the list of seen tiles and the list of visitable tiles
			tileFrontier.extend(frontierAdditions)
			tilesChecked.extend([addition[1].relativePosition for addition in frontierAdditions])
		
		# if nothing is found, walk randomly (this should never happen if the map is completeable)
		return [random.choice(['N', 'S', 'E', 'W'])]

	
	def print(self):
		# print the current map knowledge using some unreadable list manipulation (sorry)
		for layer in range(len(self.data)):
			if not self.data[layer] or layer in self.mergedLayers: continue
			print(f"layer: {layer:3} | " + ' '.join([f"{i+self.origins[layer][0]:4}" for i in range(self.sizes[layer][0])]))
			print("-----------+-" + 5*self.sizes[layer][0]*'-')
			print('\n'.join([f"       {i+self.origins[layer][1]:3d} | " +' '.join([f"{str(tile) if tile else "  ? ":>4}" for tile in self.data[layer][i]]) for i in range(self.sizes[layer][1])]))
			print("-----------+-" + 5*self.sizes[layer][0]*'-')
			print()
		print("landmarks:", list(map(lambda p: (p[0], p[1].relativePosition), self.landmarks.items())))