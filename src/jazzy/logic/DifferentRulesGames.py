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
from jazzy.logic.GameOver import GameOver

class ExtinctionGame(ClassicGame):    
    def getGameOverMessage(self):
        # player extincted?
        player = self.board.getNextCurrentPlayer()
        go = GameOver(self.board)
        if go.notRequiredPiecesLeft(self.usedPieces):
            return self._valueResult(player, 'Extincted')
        # default stuff
        return super(ExtinctionGame, self).getGameOverMessage()
        
    def _valueResult(self, player, msg):
        if msg == 'Extincted':
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
            return self._generateGameOverMessage(msg, result, winner)
        # default stuff
        return super(ExtinctionGame, self)._valueResult(player, msg)

# http://en.wikipedia.org/wiki/Monochromatic_chess
class MonochromaticGame(ClassicGame):    
    def filterMovesByRules(self, moveSet, board, player):
        self.colorCheck(self, moveSet, board, player, 1)
        
    def colorCheck(self, moveSet, board, player, modulo):
        # keep what's in basic game
        moveSet = super(MonochromaticGame, self).filterMovesByRules(moveSet, board, player)
        # filter our moves
        for move in set(moveSet):
            fromSplit = self.board.splitPos(move.fromField);
            toSplit = self.board.splitPos(move.toField);
            # Manhattan distance even or odd?
            if (math.fabs(fromSplit[0] - toSplit[0]) + math.fabs(fromSplit[1] - toSplit[1])) % 2 == modulo:
                moveSet.remove(move)
        return moveSet
    
    def _valueResult(self, player, msg):
        if msg == 'Stalemate':
            winner = self.board.getCurrentPlayer().mq.shortenedId
            result = '0-1' if player.color == self.COLORS[0] else '1-0'
            return self._generateGameOverMessage('No legal move', result, winner)
        # default stuff
        return super(ExtinctionGame, self)._valueResult(player, msg)


# http://en.wikipedia.org/wiki/Monochromatic_chess
class BichromaticGame(MonochromaticGame):    
    def filterMovesByRules(self, moveSet, board, player):
        self.colorCheck(self, moveSet, board, player, 0)
        
        
        
# http://en.wikipedia.org/wiki/Checkless_chess
class ChecklessGame(ClassicGame):    
    def getGameOverMessage(self):
        result = super(ChecklessGame, self).getGameOverMessage()
        if result is None:
            player = self.board.getNextCurrentPlayer()
            go = GameOver(self.board)
            if go.inCheck():
                msg = 'Check without mate'
                winner = self.board.getCurrentPlayer().mq.shortenedId
                result = '0-1' if player.color == self.COLORS[0] else '1-0'
                return self._generateGameOverMessage(msg, result, winner)
            else:
                return None
        return result