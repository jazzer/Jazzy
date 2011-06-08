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


class Piece(object):
    def __init__(self, color, board):
        self.moveType = []
        self.color = color
        self.board = board
        self.shortName = ' '

    def getTargets(self, currPos):
        resultList = []
        for mType in self.moveType:
            movedPos = currPos
            stop = False
            for _ in range(1, mType['max'] + 1):
                startPos = movedPos
                
                parts = self.board.splitPos(movedPos)
                col = parts[0]
                row = parts[1]

                # calculate new position
                newCol = (col + mType['dirX'] + self.board.width) % self.board.width
                newRow = (row + mType['dirY'] + self.board.height) % self.board.height
                    
                movedPos = self.board.mergePos(newCol, newRow) 

                # hit another piece?
                if ('hit_only' in mType and mType['hit_only'] == True) and (self.board.fields[movedPos] is None):
                    break
                elif ('move_only' in mType and mType['move_only'] == True) and not(self.board.fields[movedPos] is None):
                    break
                     
                # stay in bounds     
                if not self.board.staysInBoard(startPos, movedPos, mType['dirX'], mType['dirY']):
                    break
                    
                
                # stop if hit a piece on our way
                if not ('move_only' in mType) and not ('hit_only' in mType) and not(self.board.fields[movedPos] is None):
                    if not (self.board.CAN_TAKE_OWN_PIECES) and self.board.fields[movedPos].color == self.color: 
                        break
                    stop = True

                # found a place to move to    
                resultList.append(movedPos)
                
                if stop:
                    break;

        return resultList
    
    def getShortName(self):
        if self.color == 'white':
            return self.shortName.upper()            
        return self.shortName.lower()
    
    def __unicode__(self):
        return "[piece] type: " + self.getShortName()



class King(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'k'
        self.moveType = [
                         {'dirX': 1, 'dirY': 1, 'max': 1}, 
                         {'dirX': 0, 'dirY': 1, 'max': 1}, 
                         {'dirX': -1, 'dirY': 1, 'max': 1}, 
                         {'dirX': 1, 'dirY': 0, 'max': 1}, 
                         {'dirX': -1, 'dirY': 0, 'max': 1}, 
                         {'dirX': 1, 'dirY': -1, 'max': 1}, 
                         {'dirX': 0, 'dirY': -1, 'max': 1}, 
                         {'dirX': -1, 'dirY': -1, 'max': 1}, 
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
                         {'dirX': -1, 'dirY': 2, 'max': 1},
                         {'dirX': 1, 'dirY': -2, 'max': 1},
                         {'dirX': -1, 'dirY': -2, 'max': 1},
                         {'dirX': 2, 'dirY': 1, 'max': 1},
                         {'dirX': 2, 'dirY': -1, 'max': 1},
                         {'dirX': -2, 'dirY': 1, 'max': 1}, 
                         {'dirX': -2, 'dirY': -1, 'max': 1} 
                        ]
        
        
class Pawn(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'p'
        # settings
        self.START_BOOST = 2
        self.NORMAL_SPEED = 1
        
    def getTargets(self, currPos):
        row = currPos // self.board.width
        dirY = 1 if self.color == 'black' else -1
        if (row == 1 and self.color == 'black') or (row == (self.board.height - 2) and self.color == 'white'):
            self.moveType = [
                             {'dirX': 0, 'dirY': dirY, 'max': self.START_BOOST, 'move_only': True},
                             {'dirX': 1, 'dirY': dirY, 'max': 1, 'hit_only': True},
                             {'dirX': -1, 'dirY': dirY, 'max': 1, 'hit_only': True}
                             ]
        else:
            self.moveType = [
                             {'dirX': 0, 'dirY': dirY, 'max': self.NORMAL_SPEED, 'move_only': True},
                             {'dirX': 1, 'dirY': dirY, 'max': 1, 'hit_only': True},
                             {'dirX': -1, 'dirY': dirY, 'max': 1, 'hit_only': True}
                             ]


        return super(Pawn, self).getTargets(currPos)
    
    
class Coin(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'c'
