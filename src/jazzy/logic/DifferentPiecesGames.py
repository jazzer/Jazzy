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
from jazzy.logic.MoveHistory import Move
from jazzy.logic.GameOver import GameOver
from jazzy.server.MessageHandler import Message
from jazzy.logic.Pieces import *


# http://en.wikipedia.org/wiki/Berolina_chess
class BerolinaGame(ClassicGame):
    def startInit(self):
        super(BerolinaGame, self).startInit()
        self.pieceMap['p'] = BerolinaPawn
    
class CoinGame(ClassicGame):
    def startInit(self):
        super(CoinGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/4C3/PPPPPPPP/RNBQKBNR')
        self.pieceMap['c'] = Coin
    
    def endInit(self):
        # do the normal things
        super(CoinGame, self).endInit()
        # change something
        coin_pos = self.board.findPieces('c', None)
        for pos in coin_pos:
            self.board.fields[pos].color = None
            
    def getGameOverMessage(self):
        player = self.board.getCurrentPlayer()
        msg = None
        go = GameOver(self.board)
        if go.noLegalMove() and not go.inCheck():
            msg = 'No move left'
            winner = player.mq.shortenedId
            result = '0-1' if player.color == self.COLORS[0] else '1-0'
            return Message('gameover', {'winner': winner, 'msg': msg, 'result': result})
        else:
            return super(CoinGame, self).getGameOverMessage()

    def move(self, move, board):
        coin_pos = board.findPieces('c', None).pop() # there only is one ;-)
        coin_target = coin_pos + (move.toField - move.fromField)
        board.move(Move(coin_pos, coin_target))
        # normal stuff
        return [Move(coin_pos, coin_target)] + super(CoinGame, self).move(move, board)
    
    def filterMovesByRules(self, moveSet, board, player):
        moveSet = super(CoinGame, self).filterMovesByRules(moveSet, board, player)
        
        for move in set(moveSet):
            # check if the coin can move the same way
            coin_pos = board.findPieces('c', None).pop() # there only is one ;-)
            diff = board.getDiffPos(board.splitPos(move.fromField), board.splitPos(move.toField))
            coin_target_XY = board.addPos(board.splitPos(coin_pos), diff)
            # coin target field must be empty now (before having moved the piece!)
            coin_target = board.mergePos(coin_target_XY[0], coin_target_XY[1])
            # coin must respect borders as well of course
            if not board.staysInBoard(coin_pos, coin_target, diff[0], diff[1]):
                moveSet.remove(move)   
                continue
            try:
                if not (board.fields[coin_target] is None):
                    moveSet.remove(move)
            except IndexError:
                pass
        return moveSet    
        
