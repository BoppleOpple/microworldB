# NAME(S): Liam Hillery
#
# APPROACH:
# |--------------------------------------------------------------------------------|
# While I considered doing more for this project, I decided against it because I
# didn't want to make my life harder for future projects by building off of a more
# convoluted algorithm than necessary. My thoughts at the beginning of this project
# were that I needed:
#   a.) Several states for the agent depending on its current goal
#   b.) Some method of remembering places the agent had already seen
#   c.) Some way to move from one place to another if the agent knows a path between
#       them
#
# My original intention was to use two states: one in which the agent searched for
# the goal and one in which it moved there once it know where the goal was. It would
# use a linked implementation of a graph to store the map, and use Dijkstra's
# algorithm to move between tiles. For the most part, this implementation didnt
# change, but there were a few important issues with my original plan that led me to
# this solution.
#
# Most notably of these changes, I added a state. This current algorithm has three
# modes, though it can switch between these modes in the middle of a cycle:
#   1.) Follow a path, no questions asked
#   2.) Find a path to somewhere new
#   3.) Find a path to the goal
# This change only really affected one thing, and that is that the agent would
# always follow its plan, unless it saw a path to the end. The flow of the program
# now looks something like:
#                                   +--------+------------------------+
#                                   |        |                        |
#                                   v        |                        |
# Find a path to somewhere new -> Follow that path ---+---> Find a path to the goal
#             ^                                       |
#             |                                       |
#             +---------------------------------------+
#
# Similarly, when finding a path, the program first had to know where the
# destination was before it could use Dijkstra's, so it had to run some traversal
# anyway. Once I realised that, I just used breadth-first search to find the
# shortest path, since this application is quite small. (this is what prompted the
# addition of the path-following phase)
# 
# Finally, instead of using a graph, I stored the map in a 2-dimensional list, since
# all of the tiles had to be accessed with coordinates anyway, so they would have to
# be indexable with vectors somehow. Also, the map is always rectangular, so its
# worst-case memory size would be equivalent or nearly equivalent. (plus it was much
# easier to render in terminal for debugging, for a small performance hit)
#
# |--------------------------------------------------------------------------------|
#
# NEW STUFF:
# This agent is the collector, so it will immediately move towards a goal once
# found. When no goals are found, its behavior is similar to that of the searcher,
# but with less randomness and without taking into account the number of tiles
# the destination would uncover.
#


import random
import math
from aiDependancies.tile import Tile, tileCategories
from aiDependancies.map import Map, directionCoordinates, directionOpposites
from aiDependancies.aiBase import AI as BaseAI

class AI (BaseAI):
    def update(self, percepts, msg):
        """
        PERCEPTS:
        Called each turn. Parameter "percepts" is a dictionary containing
        nine entries with the following keys: X, N, NE, E, SE, S, SW, W, NW.
        Each entry's value is a single character giving the contents of the
        map cell in that direction. X gives the contents of the cell the agent
        is in.

        COMAMND:
        This function must return one of the following commands as a string:
        N, E, S, W, U

        N moves the agent north on the map (i.e. up)
        E moves the agent east
        S moves the agent south
        W moves the agent west
        U uses/activates the contents of the cell if it is useable. For
        example, stairs (o, b, y, p) will not move the agent automatically
        to the corresponding hex. The agent must 'U' the cell once in it
        to be transported.

        The same goes for goal hexes (0, 1, 2, 3, 4, 5, 6, 7, 8, 9).
        """
        self.turn += 1
        
        # update location to match the map, in case the other agent
        # messed something up
        if self.location is not self.memory.tileAt(*self.location.relativePosition):
            self.location = self.memory.tileAt(*self.location.relativePosition)

        if self.print: print(f"B received the message: {msg}")
        
        pathOther = [self.location]
        if msg:
            # link maps if it gets one
            if type(msg) == Map:
                self.memory = msg
                # TODO make it not break everything if this isnt on the map
                self.location = self.memory.tileAt(*self.location.relativePosition)
            else:
                pathOther = self.getPath(*msg)
        
        # for each percept
        for direction, tiles in percepts.items():

            # (except X)
            if direction == 'X': continue

            # add the tile to memory
            for i in range(len(tiles)):
                tileLocation = (
                    self.location.relativePosition[0] + (i+1)*directionCoordinates[direction][0],
                    self.location.relativePosition[1] + (i+1)*directionCoordinates[direction][1],
                    self.location.relativePosition[2]
                )
                t = Tile(tileLocation[0], tileLocation[1], tiles[i], tileLocation[2])
                self.memory.rememberTile(t, t.type == 'g')

        # print the current state of memory, if enabled
        if self.print: self.memory.print()
        if self.print: print("B position:", self.location.relativePosition)
        if self.print: print("B options:", list(map(lambda p: (p[0], p[1].relativePosition if p[1] else None), self.location.relations.items())))

        # check if we need to escape
        escapeRoute = None
        if not self.escaping:
            escapeRoute = self.checkEscape()
            if escapeRoute:
                self.nextActions = escapeRoute
        
        # if there is no plan, make one
        if (not self.nextActions or self.turn % 5 == 0) and not self.escaping:
            goals = list(filter(lambda t: t.tileCategory == "GOAL", self.memory.landmarks.values()))

            # by going to the closest goal
            if goals:
                # can make this faster with a* or smth
                self.nextActions = self.memory.bft(
                    *self.location.relativePosition,
                    lambda tile: tile.tileCategory == "GOAL"
                ) + ['U']
            else:
                # or by finding the closest unknown tile
                # self.nextActions = self.memory.bft(
                #     *self.location.relativePosition,
                #     lambda tile: tile.hasUnknowns(),
                #     lambda KVPair: random.random() - math.dist(KVPair[1].relativePosition, pathOther[-1].relativePosition)
                # )
                self.nextActions = self.memory.bft(
                    *self.location.relativePosition,
                    lambda tile: tile.hasUnknowns(),
                    lambda KVPair: 3*random.random() + KVPair[1].numUnknowns() / 2 - math.dist(KVPair[1].relativePosition, pathOther[-1].relativePosition)
                )

        if self.print: print("B next actions:", self.nextActions)
        
        # if we're escaping, we can waste one unit of time by inputting "use" somewhere
        if self.escaping and self.turn + len(self.nextActions) < self.maxTurns and self.location.type == 'g':
            choice = 'U'
        else:
            # perform the first action in the plan
            choice = self.nextActions.pop(0)
        
        # update our position
        self.move(choice)

        # return a map first, and our intended path after that
        return choice, (self.location, self.nextActions)