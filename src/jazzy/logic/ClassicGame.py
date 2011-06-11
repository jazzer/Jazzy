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
from jazzy.server.MessageHandler import Message
from jazzy.logic.MoveHistory import MoveHistory

class ClassicGame():
    
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.players = []
        self.moveHistory = MoveHistory()
        self.board = Board(self, width=8, height=8)
        self.currentPlayerId = 0
        self.possibleMoves = None
        self.board.loadFenPos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        
        # settings
        self.NUM_PLAYERS = 2
        self.COLORS = ['white', 'black']
        
       
    def move(self, move):
        self.board.move(move)
        # next players turn
        self.currentPlayerId = (self.currentPlayerId + 1) % self.NUM_PLAYERS
        # calc possible moves for the next round
        self.possibleMoves = None
        self.parsePossibleMoves(self.getCurrentPlayer())
        return [move]
        
        
    def addPlayer(self, player):
        player.game = self
        player.color = self.COLORS[len(self.players)]
        self.players.append(player)
        
    def getCurrentPlayer(self):
        if len(self.players) == 0:
            return None
        if len(self.players) < self.currentPlayerId + 1:
            return None
        return self.players[self.currentPlayerId]

    def getNextPlayer(self, player):
        for i in range(len(self.players)):
            if self.players[i] == player:
                return self.players[(i + 1) % len(self.players)]
        
    def getSituationMessage(self, mq):
        flipped = True if mq.player.color == 'black' else False
        data = {'fen': mq.game.board.getFenPos(),
                'board_size': str(mq.game.board.width) + 'x' + str(mq.game.board.height),
                'flipped': flipped}
        # add last move if applicable    
        if len(self.moveHistory.moves) > 0:
            lastMove = self.moveHistory.moves[-1];
            data['lmove_from'] = lastMove.fromField
            data['lmove_to'] = lastMove.toField
        # add current player if applicable    
        if not(self.getCurrentPlayer() is None):
            data['currP'] = self.getCurrentPlayer().mq.shortenedId
        return Message("gamesit", data)
        
    
    def setPawnSpeed(self, START_BOOST, NORMAL_SPEED):
        pawn_pos_set = self.board.findPieces('p', {'white', 'black'})
        for pawn_pos in pawn_pos_set:
            self.board.fields[pawn_pos].START_BOOST = START_BOOST
            self.board.fields[pawn_pos].NORMAL_SPEED = NORMAL_SPEED
    
    
    def parsePossibleMoves(self, player):
        if player is None or not(self.possibleMoves is None):
            return
        
        moveSet = self.findAllPieceMoves()
        # filter
        moveSet = self.filterMovesByRules(moveSet, player)
        moveSet = self.filterMovesToCheck(moveSet, player)
        print("I think you can move like this: " + str(moveSet))
        self.possibleMoves = moveSet
    
    def findAllPieceMoves(self):
        # get all the player's pieces
        pieces = self.board.findPlayersPieces(self.players[self.currentPlayerId])
        # get all their candidate moves
        moveSet = set()
        for pos in pieces:
            results = self.board.fields[pos].getPossibleMoves(pos)
            print(str(results))
            moveSet |= self.board.fields[pos].getPossibleMoves(pos)
        return moveSet
        
    def filterMovesByRules(self, moveSet, player):
        # add (!) castling options here
        # add promotion variants
        # add en passant moves
        return moveSet

    def filterMovesToCheck(self, moveSet, player):
        # TODO filter moves to check and such
        return moveSet
        
        for move in set(moveSet): # work on a copy to be able to remove inside
            print('filtering ' + str(move))
            # create a board copy for analysis purposes
            whatIfBoard = copy.deepcopy(self.board)
            whatIfBoard.move(move)
            #print("what if? \n" + whatIfBoard.__unicode__())
            # did the player stay in check?
            otherPlayer = self.getNextPlayer(player)
            kings = whatIfBoard.findPieces("k", player.color)
            targets = whatIfBoard.getPlayerTargets(otherPlayer)
            selfInCheck = (len(kings) > 0 and kings.issubset(targets))
            if selfInCheck:
                moveSet.remove(move)
                print('THAT WOULD BE CHECK!')
                
        return moveSet
        
    def isLegalMove(self, move, sentPlayer):
        return True
        self.parsePossibleMoves(sentPlayer)
        if (move) in self.possibleMoves:
            return True
        return False
    
    def __unicode__(self):
        return "[Game] id=%s, type=%s" % (self.id, self.gameType)
        
    def __str__(self):
        return self.__unicode__()
    
    
def enum(**enums):
    return type('Enum', (), enums)   
