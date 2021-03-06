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


from jazzy.logic.Move import Move
import copy

class Piece(object):
    def __init__(self, color, board):
        self.moveType = []
        self.color = color
        self.board = board
        self.shortName = ' '
        self.moveCount = 0
        self.value = 0
        
    def setColor(self, color):
        self.color = color;

    def getPossibleMoves(self, currPos):
        resultSet = set()
        for mType in self.moveType:
            movedPos = currPos
            stop = False
            for _ in range(mType['max']):
                startPos = movedPos
                
                # move on board (respecting bounds)
                if self.board is None:
                    pass
                movedPos = self.board.moveByDirection(startPos, mType['dirX'], mType['dirY'])
                # did we hit bounds?
                if movedPos is None:
                    break
                
                # compute some features
                fields = self.board.fields
                practically_empty = (fields[movedPos] is None) or (fields[movedPos].color is None) 
                capturable_piece = (not(practically_empty) and (self.board.CAN_TAKE_OWN_PIECES or (not(self.board.CAN_TAKE_OWN_PIECES) and fields[movedPos].color != fields[currPos].color)))

                # hit another piece?
                if ('hit_only' in mType and mType['hit_only'] == True and practically_empty):
                    break
                elif ('move_only' in mType and mType['move_only'] == True) and not practically_empty:
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
        result.moveType = copy.deepcopy(self.moveType)
        return result


class King(Piece):
    def __init__(self, color, board):
        super(King, self).__init__(color, board)
        self.shortName = 'k'
        self.value = 100
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

class StrongKing(King):
    def __init__(self, color, board):
        super(StrongKing, self).__init__(color, board)
        self.moveType = [
                         {'dirX': 1, 'dirY': 1, 'max': 2},
                         {'dirX': 0, 'dirY': 1, 'max': 2},
                         {'dirX':-1, 'dirY': 1, 'max': 2},
                         {'dirX': 1, 'dirY': 0, 'max': 2},
                         {'dirX':-1, 'dirY': 0, 'max': 2},
                         {'dirX': 1, 'dirY':-1, 'max': 2},
                         {'dirX': 0, 'dirY':-1, 'max': 2},
                         {'dirX':-1, 'dirY':-1, 'max': 2},
                        ]

class StationaryKing(King):
    def __init__(self, color, board):
        super(StationaryKing, self).__init__(color, board)
        self.moveType = []
        
        
class Queen(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, color, board)
        self.shortName = 'q'
        self.value = 10
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
        self.value = 5
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
        self.value = 3
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
        self.value = 2.9
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
        self.value = 1

        self.startInit()
        self.endInit()
    
    def startInit(self):
        # settings
        self.START_BOOST = 2
        self.NORMAL_SPEED = 1
        self.STRAIGHT = {'type': 'move_only'}
        self.DIAGONAL = {'type': 'hit_only'}
        self.changedSpeed = False
        # enable hooking
        #self.endInit()
        
    def endInit(self):
        dirY = 1 if self.color == 'black' else - 1
        self.moveType = [
              {'dirX': 1, 'dirY': dirY, 'max': 1},
              {'dirX':-1, 'dirY': dirY, 'max': 1},
              {'dirX': 0, 'dirY': dirY, 'max': self.START_BOOST}
        ]
        # add types
        if not(self.DIAGONAL is None):
            self.moveType[0][self.DIAGONAL['type']] = True
            self.moveType[1][self.DIAGONAL['type']] = True
        if not(self.STRAIGHT is None):
            self.moveType[2][self.STRAIGHT['type']] = True
            
    def setColor(self, color):
        super(Pawn, self).setColor(color)
        self.endInit();
        
    def getPossibleMoves(self, currPos):
        # move type can only change after first move in this standard configuration
        if (self.moveCount > 0 and not self.changedSpeed):
            for moveType in self.moveType:
                if not('hit_only' in moveType):
                    moveType['max'] = self.NORMAL_SPEED
            self.changedSpeed = True
        
        return super(Pawn, self).getPossibleMoves(currPos)

class SlowPawn(Pawn):
    def startInit(self):
        super(SlowPawn, self).startInit()
        # settings
        self.START_BOOST = 1

class LeganPawn(Pawn):
    def endInit(self):
        super(LeganPawn, self).endInit()
        # settings
        dirX = 1 if self.color == 'black' else - 1
        dirY = 1 if self.color == 'black' else - 1
        self.moveType = [
              {'dirX': 0, 'dirY': dirY, 'max': 1, 'hit_only': True},
              {'dirX': dirX, 'dirY': 0, 'max': 1, 'hit_only': True},
              {'dirX': dirX, 'dirY': dirY, 'max': self.START_BOOST, 'move_only': True}
        ]

class BerolinaPawn(Pawn):
    def endInit(self):
        # settings
        self.DIAGONAL = {'type': 'move_only'}
        self.STRAIGHT = {'type': 'hit_only'}

        super(BerolinaPawn, self).endInit()

class FearPawn(Pawn):
    def endInit(self):
        super(FearPawn, self).endInit()
        dirY = 1 if self.color == 'black' else - 1
        # allow one step back as well
        self.moveType += [
              {'dirX': 0, 'dirY': -dirY, 'max': 1}
        ]

    
    
class Coin(Piece):
    def __init__(self, color, board):
        Piece.__init__(self, None, board)
        self.shortName = 'c'


# combined pieces
def combinePieces(color, board, classesList):
    resultMoveType = []
    for clazz in classesList:
        object = clazz(color, board)
        resultMoveType += object.moveType
        del object
    return resultMoveType

class PrimeMinister(Piece):
    def __init__(self, color, board):
            super(PrimeMinister, self).__init__(color, board)
            self.moveType = combinePieces(color, board, [Bishop, Knight])
            self.shortName = 'i'
# add alias for Capablanca chess
Archbishop = PrimeMinister

class Chancellor(Piece):
    def __init__(self, color, board):
            super(Chancellor, self).__init__(color, board)
            self.moveType = combinePieces(color, board, [Rook, Knight])
            self.shortName = 'h'
