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


from jazzy.logic.MoveHistory import Move
import copy

class Piece(object):
    def __init__(self, color, board):
        self.moveType = []
        self.color = color
        self.board = board
        self.shortName = ' '

    def getPossibleMoves(self, currPos):
        resultSet = set()
        for mType in self.moveType:
            movedPos = currPos
            stop = False
            for _ in range(mType['max']):
                startPos = movedPos
                
                parts = self.board.splitPos(movedPos)
                col = parts[0]
                row = parts[1]

                # calculate new position
                newCol = (col + mType['dirX'] + self.board.width) % self.board.width
                newRow = (row + mType['dirY'] + self.board.height) % self.board.height
                    
                movedPos = self.board.mergePos(newCol, newRow)
                
                # compute some features
                fields = self.board.fields
                practically_empty = (fields[movedPos] is None) or (fields[movedPos].color is None) 
                capturable_piece = (not(practically_empty) and (self.board.CAN_TAKE_OWN_PIECES or (not(self.board.CAN_TAKE_OWN_PIECES) and fields[movedPos].color != fields[currPos].color)))

                # hit another piece?
                if ('hit_only' in mType and mType['hit_only'] == True and practically_empty):
                    break
                elif ('move_only' in mType and mType['move_only'] == True) and not practically_empty:
                    break
                     
                # stay in bounds     
                if not self.board.staysInBoard(startPos, movedPos, mType['dirX'], mType['dirY']):
                    break
                
                # break if non-capturable piece blocks the way (usually own-colored)
                if not(practically_empty) and not(capturable_piece):
                    break                                     
                # stop if hit a piece on our way
                if capturable_piece:
                    stop = True

                # found a place to move to    
                resultSet.add(Move(currPos, movedPos))
                
                if stop:
                    break;

        return resultSet
    
    def getShortName(self):
        if self.color == 'white':
            return self.shortName.upper()            
        return self.shortName.lower()
    
    def __unicode__(self):
        return "[piece] type: " + self.getShortName()

    def __deepcopy__(self, memo):
        board = self.board
        self.board = None
        result = copy.copy(self)#, memo)
        self.board = board
        return result


class King(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'k'
        self.moveType = [
                         {'dirX': 1, 'dirY': 1, 'max': 1},
                         {'dirX': 0, 'dirY': 1, 'max': 1},
                         {'dirX':-1, 'dirY': 1, 'max': 1},
                         {'dirX': 1, 'dirY': 0, 'max': 1},
                         {'dirX':-1, 'dirY': 0, 'max': 1},
                         {'dirX': 1, 'dirY':-1, 'max': 1},
                         {'dirX': 0, 'dirY':-1, 'max': 1},
                         {'dirX':-1, 'dirY':-1, 'max': 1},
                        ]
        
        
class Queen(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'q'
        diag_len = max(board.width, board.height)
        self.moveType = [
                         {'dirX': 1, 'dirY': 1, 'max': diag_len},
                         {'dirX': 0, 'dirY': 1, 'max': diag_len},
                         {'dirX':-1, 'dirY': 1, 'max': diag_len},
                         {'dirX': 1, 'dirY': 0, 'max': diag_len},
                         {'dirX':-1, 'dirY': 0, 'max': diag_len},
                         {'dirX': 1, 'dirY':-1, 'max': diag_len},
                         {'dirX': 0, 'dirY':-1, 'max': diag_len},
                         {'dirX':-1, 'dirY':-1, 'max': diag_len}
                        ]
        
        
class Rook(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'r'
        self.moveType = [
                         {'dirX': 0, 'dirY': 1, 'max': board.height},
                         {'dirX': 1, 'dirY': 0, 'max': board.width},
                         {'dirX':-1, 'dirY': 0, 'max': board.width},
                         {'dirX': 0, 'dirY':-1, 'max': board.height} 
                        ]
        

class Bishop(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'b'
        diag_len = max(board.width, board.height)
        self.moveType = [
                         {'dirX': 1, 'dirY': 1, 'max': diag_len},
                         {'dirX':-1, 'dirY': 1, 'max': diag_len},
                         {'dirX': 1, 'dirY':-1, 'max': diag_len},
                         {'dirX':-1, 'dirY':-1, 'max': diag_len} 
                        ]
        

class Knight(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'n'
        self.moveType = [
                         {'dirX': 1, 'dirY': 2, 'max': 1},
                         {'dirX':-1, 'dirY': 2, 'max': 1},
                         {'dirX': 1, 'dirY':-2, 'max': 1},
                         {'dirX':-1, 'dirY':-2, 'max': 1},
                         {'dirX': 2, 'dirY': 1, 'max': 1},
                         {'dirX': 2, 'dirY':-1, 'max': 1},
                         {'dirX':-2, 'dirY': 1, 'max': 1},
                         {'dirX':-2, 'dirY':-1, 'max': 1} 
                        ]
        
        
class Pawn(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'p'
        # settings
        self.START_BOOST = 2
        self.NORMAL_SPEED = 1
        
    def getPossibleMoves(self, currPos):
        row = currPos // self.board.width
        dirY = 1 if self.color == 'black' else - 1
        if (row == 1 and self.color == 'black') or (row == (self.board.height - 2) and self.color == 'white'):
            self.moveType = [
                             {'dirX': 0, 'dirY': dirY, 'max': self.START_BOOST, 'move_only': True},
                             {'dirX': 1, 'dirY': dirY, 'max': 1, 'hit_only': True},
                             {'dirX':-1, 'dirY': dirY, 'max': 1, 'hit_only': True}
                             ]
        else:
            self.moveType = [
                             {'dirX': 0, 'dirY': dirY, 'max': self.NORMAL_SPEED, 'move_only': True},
                             {'dirX': 1, 'dirY': dirY, 'max': 1, 'hit_only': True},
                             {'dirX':-1, 'dirY': dirY, 'max': 1, 'hit_only': True}
                             ]

        return super(Pawn, self).getPossibleMoves(currPos)
    
    
class Coin(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'c'
