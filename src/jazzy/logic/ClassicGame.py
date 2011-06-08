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

import uuid
import copy
from jazzy.logic.Board import Board

class ClassicGame():
    
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.players = []
        self.board = Board(self, width=8, height=8)
        self.board.loadFenPos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        self.currentPlayer = 0
        # settings
        self.NUM_PLAYERS = 2
        self.COLORS = ['white', 'black']
        
    def move(self, fromField, toField):
        self.board.move(fromField, toField)
        # next players turn
        self.currentPlayer = (self.currentPlayer + 1) % self.NUM_PLAYERS
        return [{'from': fromField, 'to': toField}]
        
        
    def addPlayer(self, player):
        player.game = self
        player.color = self.COLORS[len(self.players)]
        self.players.append(player)
        
    def getNextPlayer(self, player):
        for i in range(len(self.players)):
            if self.players[i] == player:
                return self.players[(i+1) % len(self.players)]
        
    def getCurrentState(self):
        pass
    
    def isLegalMove(self, fromField, toField, sentPlayer):
        # TODO generate meaningful messages here!
        piece = self.board.fields[fromField]
        
        # not from empty field
        if piece is None:
            return False
        # is it even current player's piece?
        if piece.color != sentPlayer.color or piece.color != self.COLORS[self.currentPlayer]:
            return False
        # can piece move like that?
        if not (toField in piece.getTargets(fromField)):
            return False
        
        # create a board copy for analysis purposes
        whatIfBoard = copy.deepcopy(self.board)
        whatIfBoard.move(fromField, toField)
        #print("what if? \n" + whatIfBoard.__unicode__())
        # did the player stay in check?
        otherPlayer = self.getNextPlayer(sentPlayer)
        kings = whatIfBoard.findPieces("k", sentPlayer.color)
        targets = whatIfBoard.getPlayerTargets(otherPlayer)
        selfInCheck = (len(kings) > 0 and kings.issubset(targets))
        if selfInCheck:
            return False
                
        return True
    
    def __unicode__(self):
        return "[Game] id=%s, type=%s" % (self.id, self.gameType)
        
    def __str__(self):
        return self.__unicode__()
    
    
def enum(**enums):
    return type('Enum', (), enums)   
