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


import re
import copy
from jazzy.logic.Pieces import *
from jazzy.logic.Move import Move, NullMove

class Board(object):

    def __init__(self, game, width=8, height=8):
        self.game = game
        self.width = width
        self.height = height
        self.clear() # self.fields is created here
        self.moveHistory = []
        
        # settings
        self.LIMIT_TOP_BOTTOM = True
        self.LIMIT_LEFT_RIGHT = True
        self.CAN_TAKE_OWN_PIECES = False
    
    def splitPos(self, pos):
        return (pos % self.width, pos // self.width)
    
    def mergePos(self, col, row):
        return self.width * row + col
    
    def addPos(self, start, diff):
        return ((start[0] + diff[0]) % self.width, (start[1] + diff[1]) % self.height)
    
    def getDiffPos(self, fromXY, toXY):
        return (toXY[0] - fromXY[0], toXY[1] - fromXY[1])
    
    def moveByDirectionFromPos(self, fromPos, dirX, dirY):
        toPos = self.addPos(fromPos, (dirX, dirY))
                
        if self.LIMIT_LEFT_RIGHT:
            toLeft = (dirX < 0)
            toRight = (dirX > 0)
            if toLeft and toPos[0] > fromPos[0]:
                return None
            if toRight and toPos[0] < fromPos[0]:
                return None
        if self.LIMIT_TOP_BOTTOM:
            up = (dirY < 0)
            down = (dirY > 0)
            if up and toPos[1] > fromPos[1]:
                return None
            if down and toPos[1] < fromPos[1]:
                return None
        
        return toPos
    
    def moveByDirection(self, fromField, dirX, dirY):
        result = self.moveByDirectionFromPos(self.splitPos(fromField), dirX, dirY)
        if result is None:
            return None
        return self.mergePos(result[0], result[1])
    
    
    def fieldToString(self, id):
        pos = self.splitPos(id)
        # lowercase letters
        if pos[0] < 27:
            return chr(97 + pos[0]) + str(self.height - pos[1])
        # uppercase letters
        if pos[0] < 53:
            return chr(65 + pos[0]) + str(self.height - pos[1])
        # no way we can have bigger boards than that using classic notation
        return None
        
    def stringToField(self, string):
        col = ord(string[0:1])
        row = string[1:] 
        return self.mergePos(col, row)
        
        
    def clear(self):
        self.fields = []
        for _ in range(self.width * self.height):
            self.fields.append(None)
    
    def loadFenPos(self, fenString):
        # clear fields
        self.clear()
        self.game.usedPieces = set()
        
        # create new pieces        
        chars = list(fenString)
        posCounter = 0
        addValue = 0
        for i in range(len(chars)):
            char = chars[i]
            if char == '/':
                posCounter = posCounter + addValue
                addValue = 0
                continue;
            elif re.match('\d', char):
                addValue = addValue * 10 + int(char)
            else:
                if addValue > 0:
                    posCounter = posCounter + addValue
                    addValue = 0
                # piece of some kind
                pieceClass = self.game.pieceMap[char.lower()]
                self.game.usedPieces.add(char.lower());
                color = 'white' if char.isupper() else 'black'
                piece = pieceClass(color, self)
                #print("setting " + piece.__unicode__() + " to " + str(posCounter))
                self.fields[posCounter] = piece
                posCounter += 1     
 
    
    def move(self, move):
        
        if isinstance(move, NullMove):
            return
        
        fromPiece = self.fields[move.fromField]
        self.fields[move.toField] = fromPiece
        self.fields[move.fromField] = None
        if not(move.toPiece is None):
            if move.toPiece == '':
                self.fields[move.toField] = None # remove the piece
            else:
                self.fields[move.toField] = move.toPiece
                
    def getPlayerMoves(self, player):
        targets = set([])
        for i in range(len(self.fields)):
            piece = self.fields[i]
            # empty fields
            if piece is None:
                continue
            # not player's pieces
            if piece.color != player.color:
                continue
            # desired pieces here, add up their possible moves
            targets |= set(piece.getPossibleMoves(i))
        return targets
    
    def getRankFields(self, index):
        return range(self.mergePos(0, index), self.mergePos(self.width - 1, index) + 1)
    
    def isInCheck(self, player):
        kingPositions = self.findPieces(self.game.kingPieceTypes, player.color)
        if (len(kingPositions) != 1):
            return False
            
        nextMoves = self.game.getPossibleMoves(self, checkTest=False, player=self.game.getNextPlayer(self, player))
        # check all the moves for one which killed the last king
        targetFields = []
        for nextMove in nextMoves:
            targetFields.append(nextMove.toField)
        selfInCheck = (len(kingPositions) > 0 and set(kingPositions).issubset(set(targetFields)))
        return selfInCheck
   
    def findPieces(self, pTypes, pColors):
        ''' returns list of requested pieces '''
        result = []
        for i in range(len(self.fields)):
            piece = self.fields[i]
            if piece is None:
                continue
            if pTypes is None or piece.shortName.lower() in pTypes:
                if pColors is None or (not(piece.color is None) and piece.color in pColors):
                    result.append(i) # save the piece's position, not the piece itself!
                    #print(str(result))
        return result

    def findPlayersPieces(self, player):
        return self.findPieces(None, player.color)

        
    def __unicode__(self):
        result = ""
        for row in range(self.height):
            for col in range(self.width):
                piece = self.fields[row * self.width + col]
                if piece is None:
                    result = result + "|_"
                else: 
                    result = result + "|" + piece.getShortName()
            result = result + "|\n"
        return result
    
    def __deepcopy__(self, memo):
            result = Board(self.game, self.width, self.height)
            result.moveHistory = copy.copy(self.moveHistory)
            for i in range(len(self.fields)):
                if self.fields[i] is None:
                    result.fields[i] = None
                else:
                    copiedPiece = copy.copy(self.fields[i])
                    copiedPiece.board = result
                    result.fields[i] = copiedPiece
            # restore the game
            result.game = self.game;
            return result
