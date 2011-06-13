'''
Copyright (c) 2011 Johannes Mitlmeier

This file is part of Jazzy.

Jazzy is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/agpl.html>.
'''

from jazzy.logic.ClassicGame import ClassicGame
import math

class ExtinctionGame(ClassicGame):    
    pass

# http://en.wikipedia.org/wiki/Monochromatic_chess
class MonochromaticGame(ClassicGame):    
    def filterMovesByRules(self, moveSet, board, player):
        # keep what's in basic game
        moveSet = super(MonochromaticGame, self).filterMovesByRules(moveSet, board, player)
        # filter our moves
        for move in set(moveSet):
            fromSplit = self.board.splitPos(move.fromField);
            toSplit = self.board.splitPos(move.toField);
            # Manhattan distance even or odd?
            if (math.fabs(fromSplit[0] - toSplit[0]) + math.fabs(fromSplit[1] - toSplit[1])) % 2 == 1:
                moveSet.remove(move)
        return moveSet    

# http://en.wikipedia.org/wiki/Monochromatic_chess
class BichromaticGame(ClassicGame):    
    def filterMovesByRules(self, moveSet, board, player):
        # keep what's in basic game
        moveSet = super(MonochromaticGame, self).filterMovesByRules(moveSet, board, player)
        # filter our moves
        for move in set(moveSet):
            fromSplit = self.board.splitPos(move.fromField);
            toSplit = self.board.splitPos(move.toField);
            # Manhattan distance even or odd?
            if (math.fabs(fromSplit[0] - toSplit[0]) + math.fabs(fromSplit[1] - toSplit[1])) % 2 == 0:
                moveSet.remove(move)
        return moveSet    
