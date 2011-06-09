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
from jazzy.logic.Pieces import *

class Board(object):

    def __init__(self, game, width=8, height=8):
        self.game = game
        self.width = width
        self.height = height
        self.clear() # self.fields is created here
        self.pieceMap = {'k': King, 'q': Queen, 'r': Rook, 'b': Bishop, 'n': Knight, 'p': Pawn, 'c': Coin}
        self.usedPieces = self.pieceMap.keys()
        
        # settings
        self.LIMIT_TOP_BOTTOM = True
        self.LIMIT_LEFT_RIGHT = True
        self.CAN_TAKE_OWN_PIECES = False
    
    def splitPos(self, pos):
        return (pos % self.width, pos // self.width)
    
    def mergePos(self, col, row):
        return self.width * row + col
    
    def addPos(self, start, diff):
        return (start[0] + diff[0], start[1] + diff[1])
    
    def getDiffPos(self, fromXY, toXY):
        return (toXY[0] - fromXY[0], toXY[1] - fromXY[1])
    
    def staysInBoard(self, fromField, toField, dirX, dirY):
        fromXY = self.splitPos(fromField)
        toXY = self.splitPos(toField)
                
        if self.LIMIT_LEFT_RIGHT:
            toLeft = (dirX < 0)
            toRight = (dirX > 0)
            if toLeft and toXY[0] > fromXY[0]:
                #print("to left, but " + str(toXY[0]) + " > " + str(fromXY[0]))
                return False
            if toRight and toXY[0] < fromXY[0]:
                #print("to right, but " + str(toXY[0]) + " < " + str(fromXY[0]))
                return False
        if self.LIMIT_TOP_BOTTOM:
            up = (dirY < 0)
            down = (dirY > 0)
            if up and toXY[1] > fromXY[1]:
                #print("up, but " + str(toXY[1]) + " > " + str(fromXY[1]))
                return False
            if down and toXY[1] < fromXY[1]:
                #print("down, but " + str(toXY[1]) + " < " + str(fromXY[1]))
                return False
        
        return True
        
        
    def clear(self):
        self.fields = []
        for _ in range(self.width * self.height):
            self.fields.append(None)
        
    def loadFenPos(self, fenString):
        # clear fields
        self.clear()
        self.usedPieces = set()
        
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
                pieceClass = self.pieceMap[char.lower()]
                self.usedPieces.add(char.lower());
                color = 'white' if char.isupper() else 'black'
                piece = pieceClass(color, self)
                #print("setting " + piece.__unicode__() + " to " + str(posCounter))
                self.fields[posCounter] = piece
                posCounter += 1     
                
        self.game.parsePossibleMoves(self.game.getCurrentPlayer())
        
    
    def getFenPos(self):
        fenString = ''
        # build
        for row in range(self.height):
            for col in range(self.width):
                piece = self.fields[row * self.width + col]
                if piece is None:
                    fenString = fenString + '_'
                else:
                    fenString = fenString + piece.getShortName()
            fenString = fenString + '/'
        # shorten
        for length in range(self.width, 1, -1):
            fenString = fenString.replace(('_' * length), str(length))
            
        return fenString[:-1]
    
    def move(self, fromField, toField):
        fromPiece = self.fields[fromField]
        self.fields[toField] = fromPiece
        self.fields[fromField] = None
        
    def getPlayerTargets(self, player):
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
            targets |= set(piece.getTargets(i))
        return targets

   
    def findPieces(self, pTypes, pColors):
        result = set()
        for i in range(len(self.fields)):
            piece = self.fields[i]
            if piece is None:
                continue
            if pTypes is None or piece.shortName.lower() in pTypes:
                if pColors is None or piece.color in pColors:
                    result.add(i) # save the piece's position, not the piece itself!
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
            
