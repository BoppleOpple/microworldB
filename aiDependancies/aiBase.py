import math
from aiDependancies.tile import Tile, tileCategories
from aiDependancies.map import Map, directionCoordinates, directionOpposites

class AI:
    def __init__(self, max_turns):
        """
        Called once before the sim starts. You may use this function
        to initialize any data or data structures you need.
        """

        self.print = False

        self.turn = -1
        self.location = Tile() # tile object
        self.memory = Map()    # map of agent's memory
        self.memory.rememberTile(self.location)

        self.timeToGoal = math.inf
        self.timeGoalLastChecked = 0
        self.escaping = False

        # remember the current "plan" to avoid recalculating paths
        self.maxTurns = max_turns or 400
        self.nextActions = []

    def checkEscape(self):
        # if we know where it is
        if 'r' in self.memory.landmarks.keys():
            # and we might not have time to do other stuff
            if self.timeToGoal + self.turn * 2 - self.timeGoalLastChecked + 1 >= self.maxTurns:
                if self.print: print("time check at", self.turn)
                # find the absolute fastest route to the goal
                escapeRoute = self.memory.bft(
                    *self.location.relativePosition,
                    lambda tile: tile.tileCategory == "EXIT"
                ) + ['U']
                # update our times
                self.timeToGoal = len(escapeRoute)
                self.timeGoalLastChecked = self.turn

                if self.print: print("time to exit", self.timeToGoal)

                # if we were right and do need to leave, GET OUT
                if self.timeToGoal + self.turn * 2 - self.timeGoalLastChecked + 1 >= self.maxTurns:
                    self.escaping = True
                    return escapeRoute
        return None
    
    def getPath(self, start: Tile, moves: list):
        # builds a path by simulating stepping through known territory
        result = [start]
        for move in moves:
            if move in result[-1].relations.keys():
                if result[-1].relations[move]:
                    result.append(result[-1].relations[move])
            else:
                result.append(result[-1])
        return result

    def move(self, inp: str):
        # update our memory if we grab a goal
        if inp == 'U' and self.location.tileCategory == "GOAL":
            del self.memory.landmarks[self.location.type]
            self.location.type = 'g'
            self.location.tileCategory = tileCategories['g']
        
        # otherwise move if possible
        elif inp in self.location.relations.keys():
            destination = self.location.relations[inp]

            # if the agent doesn't hit a wall when trying to move, update its position
            if destination and destination.type != 'w':
                self.location = destination