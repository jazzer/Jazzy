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

class CoinGame(ClassicGame):
    def __init__(self):
        # do the normal things
        super(CoinGame, self).__init__()
        # change something
        self.board.loadFenPos('rnbqkbnr/pppppppp/8/8/8/4C3/PPPPPPPP/RNBQKBNR')
        coin_pos = self.board.findPieces('c', None)
        for pos in coin_pos:
            self.board.fields[pos].color = None

    def move(self, move):
        coin_pos = self.board.findPieces('c', None).pop() # there only is one ;-)
        coin_target = coin_pos + (move.toField - move.fromField)
        self.board.move(Move(coin_pos, coin_target))
        # normal stuff
        return [Move(coin_pos, coin_target)] + super(CoinGame, self).move(move)
        
        
    def isLegalMove(self, move):
        # check if the coin can move the same way
        coin_pos = self.board.findPieces("c", None).pop() # there only is one ;-)
        diff = self.board.getDiffPos(self.board.splitPos(move.fromField), self.board.splitPos(move.toField))
        coin_target_XY = self.board.addPos(self.board.splitPos(coin_pos), diff)
        # coin target field must be empty now (before having moved the piece!)
        coin_target = self.board.mergePos(coin_target_XY[0], coin_target_XY[1])
        if not (self.board.fields[coin_target] is None):
            return False
        # coin must respect borders as well of course
        if not self.board.staysInBoard(coin_pos, coin_target, diff[0], diff[1]):
            return False   
        
        # temporarly hide coin (to keep normal move tests)
        coin = self.board.fields[coin_pos]
        self.board.fields[coin_pos] = None
        
        # do the normal things
        result = super(CoinGame, self).isLegalMove(move)
    
        # restore coin
        self.board.fields[coin_pos] = coin
        
        return result

