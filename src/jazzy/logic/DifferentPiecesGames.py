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
from jazzy.logic.Move import Move
from jazzy.logic.GameOver import GameOver
from jazzy.server.MessageHandler import Message
from jazzy.logic.Pieces import *


# http://en.wikipedia.org/wiki/Berolina_chess
class BerolinaGame(ClassicGame):
    meta = {'title': 'Berolina Chess',
            'desc': 'Pawns are Berolina Pawns',
            'link': 'http://en.wikipedia.org/wiki/Berolina_chess',
            'details': 'All pawns are replaced by pawns that move like normal pawns capture and vice versa.',
            'players': 2}
    
    def startInit(self):
        super(BerolinaGame, self).startInit()
        self.pieceMap['p'] = BerolinaPawn

class StationaryKingGame(ClassicGame):
    meta = {'title': 'Stationary King Chess',
            'desc': "King can't move",
            'link': 'http://en.wikipedia.org/wiki/Chess_variant#Chess_with_unusual_rules',
            'details': 'The king piece cannot move at all.',
            'players': 2}
    
    def startInit(self):
        super(StationaryKingGame, self).startInit()
        self.pieceMap['k'] = StationaryKing
        self.CASTLING = False
        
class StrongKingGame(ClassicGame):
    meta = {'title': 'Strong King Chess',
            'desc': 'King can move up to two steps in any direction',
            'link': '#own_idea',
            'details': 'The king pieces can move one or two steps in any direction making the king a much stronger piece and mating him a lot harder.',
            'players': 2}
    def startInit(self):
        super(StrongKingGame, self).startInit()
        self.pieceMap['k'] = StrongKing
    

class FearGame(ClassicGame):
    meta = {'title': 'Fear Chess',
            'desc': 'Pawns can move back',
            'link': '#own_idea',
            'details': 'All pawns can additionally to their usual moves go one step back at any time. Only on their first move they may advance two steps.',
            'players': 2}
    
    def startInit(self):
        super(FearGame, self).startInit()
        self.pieceMap['p'] = FearPawn
    

class CoinGame(ClassicGame):
    meta = {'title': 'Coin Chess',
            'desc': 'A coin must be able to follow your moves',
            'link': 'http://de.wikipedia.org/wiki/Schachvariante#M.C3.BCnzenschach.2FPfennigschach',
            'details': "At the beginning of the game, a coin is place on square e3. Whenever a move is executed, the coin must mimic the chosen piece's movement before the piece is moved. The coin cannot capture pieces. If one player has no legal moves, he looses.",
            'players': 2}
    def startInit(self):
        super(CoinGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/4C3/PPPPPPPP/RNBQKBNR')
        self.pieceMap['c'] = Coin
            
    def getGameOverMessage(self):
        player = self.getCurrentPlayer(self.board)
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
        coin_move = Move(coin_pos, coin_target)
        coin_move.silent = True
        board.move(coin_move)
        # normal stuff
        return [coin_move] + super(CoinGame, self).move(move, board)
    
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
        
