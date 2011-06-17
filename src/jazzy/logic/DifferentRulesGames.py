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
from jazzy.logic.MoveHistory import Move

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

# http://en.wikipedia.org/wiki/Dark_chess
class DarkGame(ClassicGame):
    def startInit(self):
        super(DarkGame, self).startInit()
        self.CHECK_FOR_CHECK = False
        self.NO_WATCHERS = True
        self.SHOW_LAST_MOVE = False
    
    def getFenPos(self, board, player):
        hiddenSet = set(range(board.width * board.height))
        print(str(hiddenSet))
        # my pieces are visible
        hiddenSet.difference_update(set(board.findPlayersPieces(player)))
        print(str(hiddenSet))
        # my target fields are visible
        moves = board.getPlayerMoves(player)
        for move in moves:
            if move.toField in hiddenSet:
                hiddenSet.remove(move.toField)
        print(str(hiddenSet))
        return self._getFenPosFiltered(board, player, list(hiddenSet))

    def move(self, move, board):
        super(DarkGame, self).move(move, board)
        # always reissue current situation as message to all players
        for player in self.players:
            sitMsg = self.getSituationMessage(player.mq)
            # issue the message to the player
            player.mq.addMsg(sitMsg)
        return []
    
    # TODO change gameover (extinction!)

# http://en.wikipedia.org/wiki/Atomic_chess
class AtomicGame(ClassicGame):
    def startInit(self, fenPos='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'):
        super(AtomicGame, self).startInit()
        # settings
        self.CHECK_FOR_CHECK = False
        
    def getGameOverMessage(self):
        # king killed
        player = self.board.getNextCurrentPlayer()
        go = GameOver(self.board)
        if go.notRequiredPiecesLeft(self.kingPieceTypes):
            return self._valueResult(player, 'Extincted')
        # default stuff
        return super(AtomicGame, self).getGameOverMessage()
     
    def move(self, move, board):
        capture = True
        if board.fields[move.toField] is None:
            capture = False
        
        explosionMoves = super(AtomicGame, self).move(move, board)
        
        if not capture:
            return explosionMoves
        
        # create explosion moves
        target = move.toField
        for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
                # piece itself
                if x == 0 and y == 0:
                    continue
                # fields around it
                explosionTarget = board.moveByDirection(target, x, y)
                if explosionTarget is None:
                    continue
                if board.fields[explosionTarget] is None:
                    continue 
                if board.fields[explosionTarget].shortName in self.pawnPieceTypes:
                    continue 
                move = Move(explosionTarget, explosionTarget)
                move.toPiece = '' # indicates that field will be cleared
                move.silent = True
                # execute on board
                board.move(move) 
                explosionMoves.append(move)
                 
        return explosionMoves

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
    
# http://en.wikipedia.org/wiki/Antichess
class AntiGame(ClassicGame):   
    # check is not important here
    def startInit(self):
        # default
        super(AntiGame, self).startInit()
        # change
        self.CHECK_FOR_CHECK = False
    
    # force capturing if possible
    def filterMovesByRules(self, moveSet, board, player):
        # default
        moveSet = super(AntiGame, self).filterMovesByRules(moveSet, board, player)
        # change
        captureMoves = []
        for move in moveSet:
            if not(board.fields[move.toField] is None):
                captureMoves.append(move)
        if len(captureMoves) > 0:
            return set(captureMoves)
        # default
        return moveSet
     
    # you won if you lost all your pieces
    def getGameOverMessage(self):
        player = self.board.getCurrentPlayer()
        go = GameOver(self.board)
        if go.noPiecesLeft():
            msg = 'No pieces left'
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
            return self._generateGameOverMessage(msg, result, winner)
        elif go.noLegalMove():
            msg = 'No legal move'
            winner = ''
            result = '0.5-0.5'
            return self._generateGameOverMessage(msg, result, winner)
        return None
        
