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
from jazzy.server.Player import Pocket
import logging

logger = logging.getLogger("jazzyLog")


class Board(object):

    def __init__(self, game, width=8, height=8):
        self.id = '1'
        self.game = game
        self.width = width
        self.height = height
        self.clear() # self.fields is created here
        self.moveHistory = []
        self.resend = False # for triggering full retransmission of the board's status
        
        # do not change
        self.castlingsPossible = {} # dictionary of lists, keys = colors
        for color in game.COLORS:
            self.castlingsPossible[color] = [True, True]
        # draw related stuff
        self.drawXMoveCounter = 0
        if game.DRAW_REPETITION:
            self.positions = dict()
        
        # settings
        self.LIMIT_TOP_BOTTOM = True
        self.LIMIT_LEFT_RIGHT = True
        self.CAN_TAKE_OWN_PIECES = False
        
        # create and fill pockets
        self.pockets = {}
        self.capturePockets = {}
        for color in game.COLORS:
            self.pockets[color] = Pocket()
            self.capturePockets[color] = Pocket()
    
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
        # lower case letters
        if pos[0] < 27:
            return chr(97 + pos[0]) + str(self.height - pos[1])
        # upper case letters
        if pos[0] < 53:
            return chr(65 + pos[0]) + str(self.height - pos[1])
        # no way we can have bigger boards than that using classic notation, 
        # 53 should be okay as a one board limitation especially since
        # you can have more of them (some additional tricks necessary to link them)
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
        self.game.USED_PIECES = set()
        
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
                pieceClass = self.game.PIECE_MAP[char.lower()]
                self.game.USED_PIECES.add(char.lower());
                color = 'white' if char.isupper() else 'black'
                piece = pieceClass(color, self)
                #print("setting " + piece.__unicode__() + " to " + str(posCounter))
                self.fields[posCounter] = piece
                posCounter += 1     

    def getPiecesPocket(self, pos):
        if str(pos)[0] != 'p':
            return None
        return self.pockets[self.game.COLORS[int(pos[1])]]
 
    def getPieceByPos(self, pos):
        pocketColor = None
        if str(pos)[0] == 'p':
            # we got a piece in pocket
            pocketColor = self.game.COLORS[int(pos[1])] # limited to 10 players per board!
            pocketIndex = int(pos[2:])
            return self.pockets[pocketColor].getPieces()[pocketIndex]
        else:
            # on board
            fromField = int(pos)
            return self.fields[fromField]
            
    def move(self, move):        
        if isinstance(move, NullMove):
            return        

        move.simpleParse(self)
        #move.fullParse(self) # not needed here
        
        fromPiece = self.getPieceByPos(move.fromField)
        pocket = self.getPiecesPocket(move.fromField)

        # standard move
        fromPiece.moveCount = fromPiece.moveCount + 1
        # is it a capturing move?
        if not(self.fields[move.toField] is None):
            self.game.handleCaptureMove(move, self)
        self.fields[move.toField] = fromPiece
        if self.getPiecesPocket(move.fromField) is None:
            self.fields[move.fromField] = None
        if not(move.toPiece is None):
            if move.toPiece == '':
                self.fields[move.toField] = None # remove the piece
            else:
                self.fields[move.toField] = move.toPiece

        if not(pocket is None):
            pocket.remove(fromPiece)
                
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
    
    def drawCountRepetition(self):
        currPos = self.game.getPositionHash()
        try:
            self.positions[currPos] += 1            
        except KeyError:
            self.positions[currPos] = 1
        
    def isInCheck(self, player):
        logger.debug('is %s checked?' % player.color)
        kingPositions = self.findPieces(self.game.KING_PIECE_TYPES, player.color)
        if (len(kingPositions) != 1):
            return False
        logger.debug('kings: %s' % str([self.fieldToString(x) for x in kingPositions]))
            
        nextMoves = self.game.getPossibleMoves(self, checkTest=False, player=self.game.getNextPlayer(self, player), noDropMoves = True)
        # check all the moves for one which killed the last king
        targetFields = []
        for nextMove in nextMoves:
            targetFields.append(nextMove.toField)
        logger.debug('attacked fields: %s' % str([self.fieldToString(x) for x in targetFields]))
    
        selfInCheck = (len(kingPositions) > 0 and set(kingPositions).issubset(set(targetFields)))
        return selfInCheck
   
    def findPieces(self, pTypes, pColors):
        ''' returns list of requested pieces' positions '''
        result = []
        for i in range(len(self.fields)):
            piece = self.fields[i]
            if piece is None:
                continue
            if pTypes is None or piece.shortName in pTypes:
                if pColors is None or (not(piece.color is None) and piece.color in pColors):
                    result.append(i) # save the piece's position, not the piece itself!
                    #print(str(result))
        return result

    def findPlayersPieces(self, player):
        return self.findPieces(None, player.color)

    def __str__(self):
        return self.__unicode__()
        
    def __unicode__(self):
        # board
        board = ''
        for row in range(self.height):
            for col in range(self.width):
                piece = self.fields[row * self.width + col]
                if piece is None:
                    board = board + '|_'
                else: 
                    board = board + '|' + piece.getShortName()
            board = board + '|\n'
        # pockets
        pocketData = ''
        for color in self.game.COLORS:
            pocketData = pocketData + color + ':\n'
            pocketData = pocketData + 'captured: ' + str([piece.getShortName() for piece in self.capturePockets[color].getPieces()]) + '\n'
            pocketData = pocketData + 'pocket: ' + str([piece.getShortName() for piece in self.pockets[color].getPieces()]) + '\n'
        return board + '\n\n' + pocketData
    
    def __deepcopy__(self, memo):
            result = Board(self.game, self.width, self.height)
            result.moveHistory = copy.copy(self.moveHistory)
            for i in range(len(self.fields)):
                if self.fields[i] is None:
                    result.fields[i] = None
                else:
                    copiedPiece = copy.deepcopy(self.fields[i])
                    copiedPiece.board = result
                    result.fields[i] = copiedPiece
            # restore fields
            result.game = self.game;
            result.castlingsPossible = copy.copy(self.castlingsPossible);
            result.pockets = copy.deepcopy(self.pockets);
            result.capturePockets = copy.deepcopy(self.capturePockets);
            return result
