'''
Copyright (c) 2011-2012 Johannes Mitlmeier

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


class GameOver(object):

    def __init__(self, board):
        self.board = board
        
    
    def noLegalMove(self):
        # make sure we know possible moves
        self.board.game.parsePossibleMoves()
        # count
        return len(self.board.game.possibleMoves) == 0

    def inCheck(self):
        return self.board.isInCheck(self.board.game.getCurrentPlayer(self.board))
    
    def noPiecesLeft(self):
        currPlayer = self.board.game.getCurrentPlayer(self.board)
        pieces = self.board.findPlayersPieces(currPlayer)
        return len(pieces) == 0

    def notRequiredPiecesLeft(self, pieceSet):        
        currPlayer = self.board.game.getCurrentPlayer(self.board)
        pieces = self.board.findPlayersPieces(currPlayer)
        pieceTypes = []
        for piecePos in pieces:
            pieceTypes.append(self.board.fields[piecePos].shortName)
        return not pieceSet.issubset(set(pieceTypes))
    
