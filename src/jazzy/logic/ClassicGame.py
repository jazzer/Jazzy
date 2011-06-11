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
from jazzy.server.Player import Player
from jazzy.logic.GameOver import GameOver

class ClassicGame():
    
    def __init__(self):
        self.startInit()        
        self.endInit()
    
    def startInit(self):
        # settings
        self.NUM_PLAYERS = 2
        self.COLORS = ['white', 'black']
        self.CHECK_FOR_CHECK = True
        
        # setup code
        self.id = uuid.uuid4().hex
        self.players = []
        self.watchers = []
        self.moveHistory = MoveHistory()
        self.board_width = 8
        self.board_height = 8
        self.fenPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        self.currentPlayerId = 0
        self.possibleMoves = None
        self.kingPieceTypes = {'k'}
        self.joinedPlayers = 0
    
    def endInit(self):
        self.board = Board(self, width=self.board_width, height=self.board_height)
        # pregenerate players to avoid nasty errors before all players have joined
        for i in range(self.NUM_PLAYERS):
            player = Player()
            player.color = self.COLORS[i]
            self.players.append(player)            
        # load position
        self.board.loadFenPos(self.fenPos)
       
    def move(self, move, board):
        # delegate the actual moving to the board we are operating on
        board.move(move)
        # next player's turn on that board
        board.moveCount = board.moveCount + 1
        self.currentPlayerId = board.moveCount % self.NUM_PLAYERS

        if board == self.board:
            # calc possible moves for the next round
            self.possibleMoves = None
            self.parsePossibleMoves()
        return [move]
        
        
    def addPlayer(self, player):
        player.game = self
        player.color = self.COLORS[self.joinedPlayers]
        self.players[self.joinedPlayers] = player
        self.joinedPlayers = self.joinedPlayers + 1
    
    def addWatcher(self, watcher):
        self.watchers.append(watcher)
        
        
    def getSituationMessage(self, mq):
        if mq.watching:
            flipped = False
        else:
            flipped = True if mq.subject.color == 'black' else False
            
        data = {'fen': mq.game.board.getFenPos(),
                'board_size': str(mq.game.board.width) + 'x' + str(mq.game.board.height),
                'flipped': flipped}
        # add last move if applicable    
        if len(self.moveHistory.moves) > 0:
            lastMove = self.moveHistory.moves[-1];
            data['lmove_from'] = lastMove.fromField
            data['lmove_to'] = lastMove.toField
        # add current player if applicable    
        if not(self.board.getCurrentPlayer() is None):
            data['currP'] = self.board.getCurrentPlayer().mq.shortenedId
        return Message("gamesit", data)
        
    
    def setPawnSpeed(self, START_BOOST, NORMAL_SPEED):
        pawn_pos_set = self.board.findPieces('p', set(self.COLORS))
        for pawn_pos in pawn_pos_set:
            self.board.fields[pawn_pos].START_BOOST = START_BOOST
            self.board.fields[pawn_pos].NORMAL_SPEED = NORMAL_SPEED
    
    def getGameOverMessage(self):
        player = self.board.getNextCurrentPlayer()
        msg = None
        go = GameOver(self.board)
        if go.noLegalMove():
            if go.inCheck():
                msg = 'Checkmate'
                winner = player.mq.shortenedId
                result = '1-0' if player.color == self.COLORS[0] else '0-1'
            else:
                msg = 'Stalemate'
                winner = ''
                result = '0.5-0.5'
        
        # TODO 50 moves, repetition
        
        # build message
        if not(msg is None):
            return Message('gameover', {'winner': winner, 'msg': msg, 'result': result})
            
        return None
    
    def parsePossibleMoves(self):
        if self.board.getCurrentPlayer() is None:
            return
        elif not(self.possibleMoves is None):
            return        
        
        moveSet = self.getPossibleMoves(self.board, checkTest=self.CHECK_FOR_CHECK)
        print("I think current player could move like this: " + str(moveSet))
        self.possibleMoves = moveSet
        
    def getPossibleMoves(self, board, checkTest=True, player=None):
        # default
        if player is None:
            player = board.getCurrentPlayer()
            
        moveSet = self.findAllPieceMoves(board, player)
        # filter
        moveSet = self.filterMovesByRules(moveSet, board, player)
        if checkTest:
            moveSet = self.filterMovesToCheck(moveSet, board, player)
        return moveSet
    
    def findAllPieceMoves(self, board, player):
        # get all the player's pieces
        pieces = board.findPlayersPieces(player)
        # get all their candidate moves
        moveSet = set()
        for pos in pieces:
            moveSet |= board.fields[pos].getPossibleMoves(pos)
        return moveSet
        
    def filterMovesByRules(self, moveSet, board, player):
        # add (!) castling options here
        # add promotion variants?
        # add en passant moves
        return moveSet

    def filterMovesToCheck(self, moveSet, board, player):
        for move in set(moveSet): # work on a copy to be able to remove inside
            move.parse(self.board)
            #print('filtering ' + str(move))
            # create a board copy for analysis purposes
            whatIfBoard = copy.deepcopy(self.board)
            self.move(move, whatIfBoard)
            #print("what if? \n" + whatIfBoard.__unicode__())
            # did the player stay in check?            
            if whatIfBoard.isInCheck(player):
                moveSet.remove(move)                
        return moveSet
            
    def isLegalMove(self, move):
        self.parsePossibleMoves()
        if self.possibleMoves is None:
            return False
        if move in self.possibleMoves:
            return True
        return False
    
    def __unicode__(self):
        return "[Game] id=%s, type=%s" % (self.id, self.gameType)
        
    def __str__(self):
        return self.__unicode__()
    
    
def enum(**enums):
    return type('Enum', (), enums)   
