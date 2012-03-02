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

import uuid
import copy
import re
from jazzy.logic.Board import Board
from jazzy.server.MessageHandler import Message
from jazzy.logic.Move import NullMove
from jazzy.server.Player import Player
from jazzy.logic.GameOver import GameOver
from jazzy.logic.Pieces import *
import logging

logger = logging.getLogger('jazzyLog')


class ClassicGame():
    meta = {'title': 'Classic Chess',
            'desc': 'Classic Chess as defined by FIDE',
            'link': 'http://en.wikipedia.org/wiki/Chess',
            'details': 'The goal is to checkmate the king.',
            'players': 2}
 
    def __init__(self):
        self.startInit()
        self.endInit()
    
    def startInit(self, fenPos='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'):
        # settings        
        # players
        self.NUM_PLAYERS = 2
        self.COLORS = ['white', 'black']

        # general settings
        self.CHECK_FOR_CHECK = True
        self.PROMOTION = True
        self.EN_PASSANT = True
        self.NO_WATCHERS = False
        self.SHOW_LAST_MOVE = True
        self.CAN_PROMOTE_TO_KING = False

        # castling options
        self.CASTLING = True
        self.CASTLING_FROM_CHECK = False
        self.CASTLING_THROUGH_CHECK = False
        self.CASTLING_TO_CHECK = False
        self.CASTLING_MULTIPLE_TIMES = False
        self.CASTLING_IF_KING_HAS_MOVED = False
        self.CASTLING_IF_ROOK_HAS_MOVED = False
        
        # draw options
        self.DRAW_X_MOVES = True
        self.DRAW_X_MOVES_VALUE = 50
        self.DRAW_REPETITION = True
        self.DRAW_REPETITION_VALUE = 3
        
        # crazyhouse
        self.USE_POCKET = False
        self.USE_CRAZYHOUSE_POCKET = False
        self.DROP_NO_PAWN_TO_PROMOTION_FIELDS = True
        self.DROP_NO_CHECKMATE = True # TODO implement
        self.DROP_NO_CHECK = False # TODO implement
                
        # global board settings
        self.BLOCKED_FIELDS = []
        
        # piece settings
        self.PAWN_PIECE_TYPES = ['p']
        self.KING_PIECE_TYPES = ['k']
        self.PIECE_MAP = {'k': King, 'q': Queen, 'r': Rook, 'b': Bishop, 'n': Knight, 'p': Pawn}
        self.USED_PIECES = self.PIECE_MAP.keys()
        # end of settings
        
        
        # handle fen
        self.fenPos = fenPos
        self.inferBoardSize(); 
        
        # setup code
        self.id = uuid.uuid4().hex
        self.players = []
        self.watchers = []
        self.possibleMoves = None
        self.xMoveDrawCounter = 0

        # Debugging
        self.DEBUG_LEGAL_MOVES_ON_ILLEGAL_MOVE = True

        # internal stuff
        self.joinedPlayers = 0
        self.finished = False
            
    def endInit(self):
        # create board if it has not yet been done (by overloading and because of special needs)
        if not hasattr(self, 'board') or self.board == None:
            self.board = Board(self, width=self.board_width, height=self.board_height)
        
        # load position
        self.board.loadFenPos(self.fenPos)

        # promotion settings
        self.promotionFields = {'white': self.board.getRankFields(0), 'black': self.board.getRankFields(self.board_height - 1)}
        self.allPromotionFields = self.promotionFields['white'] + self.promotionFields['black']
        self.possiblePromotionPieces = self.USED_PIECES.difference(self.PAWN_PIECE_TYPES)
        if not self.CAN_PROMOTE_TO_KING:
            self.possiblePromotionPieces.difference_update(self.KING_PIECE_TYPES)
        self.possiblePromotionPieces = list(self.possiblePromotionPieces)    
        
        # castling information
        self.castlingPositions = {} # dictionary of lists (keys = color strings)
        #self.castlingPieces = {} # dictionary of lists (keys = color strings)
        self.castlingTargetPositions = {} # dictionary of lists (keys = color strings)
        for color in self.COLORS:
            # king
            kingsPos = self.board.findPieces(['k'], [color])
            if kingsPos is None or len(kingsPos) > 1:
                self.board.castlingsPossible[color] = [False, False]
                kingPos = None
            else:
                kingPos = kingsPos[0]
            # rook
            rooksPos = self.board.findPieces(['r'], [color])         
            kingRookPos = None
            queenRookPos = None
            for rookPos in rooksPos:
                if self.board.splitPos(rookPos)[0] > self.board.width / 2:
                    kingRookPos = rookPos
                else:
                    queenRookPos = rookPos
            if kingRookPos == None:
                self.board.castlingsPossible[color][0] = False
            if queenRookPos == None:
                self.board.castlingsPossible[color][1] = False
                    
            self.castlingPositions[color] = [kingPos, kingRookPos, queenRookPos] # [0]: king, [1] king side rook, [2] queen side rook
            #self.castlingPieces[color] = [None if x is None else self.board.fields[x] for x in self.castlingPositions[color]]
    
            kingShort = self.board.addPos(self.board.splitPos(kingPos), [2, 0])
            rookShort = self.board.addPos(kingShort, [-1, 0])
            kingLong = self.board.addPos(self.board.splitPos(kingPos), [-2, 0])
            rookLong = self.board.addPos(kingLong, [1, 0])
            self.castlingTargetPositions[color] = [self.board.mergePos(kingShort[0], kingShort[1]),
                                                   self.board.mergePos(rookShort[0], rookShort[1]),
                                                   self.board.mergePos(kingLong[0], kingLong[1]),
                                                   self.board.mergePos(rookLong[0], rookLong[1])] # [0]: king for short, [1] rook for short, [2]: king for long, [3] rook for long
        
        # pre-create players
        self.createPlayers()
        
        # draw preparations
        if self.DRAW_REPETITION:
            self.board.drawCountRepetition()
            
        # metagame
        self.metagame = self
        self.board.metagame = self
   
    def distributeToAll(self, msg, filterPlayers=[]):
        for player in self.getAllPlayers() + self.getAllWatchers():
            if not (player in filterPlayers):
                player.mq.addMsg(msg)
    
    def broadcastSocket(self, msg, filterPlayers=[]):
        for player in self.getAllPlayers() + self.getAllWatchers():
            if not (player in filterPlayers):
                try:
                    player.mq.socket.send(msg)
                except AttributeError:
                    pass # player is not yet connected
    
    def getAllPlayers(self):
        ''' also returns all players from sub-games '''
        return self.players    

    def getAllWatchers(self):
        ''' also returns all players from sub-games '''
        return self.watchers    
    
    def getAllBoards(self):
        return [self.board]
        
    def createPlayers(self):
        # all of them will be dummys at first and filled via the slot mechanism
        flipStatus = False # it's fine for "white" players
        while len(self.players) < self.NUM_PLAYERS:
            player = Player()
            player.flipBoard = flipStatus
            flipStatus = not flipStatus
            mq = player.mq
            self.addPlayer(player)
            # backlinks for the MQ
            mq.subject = player
            mq.game = self
            mq.metagame = self
        
    def inferBoardSize(self):
        # get board's height
        self.board_height = self.fenPos.count('/') + 1
        # get board's width
        chars = list(self.fenPos[:self.fenPos.find('/') + 1])
        width = len(chars)
        addValue = 0
        for char in chars:
            if re.match('\d', char):
                addValue = addValue * 10 + int(char)
            elif addValue != 0:
                width += addValue - 1
                addValue = 0
                            
        self.board_width = width - 1
        
    def getPieceByString(self, string, board):
        if not(string.lower() in self.PIECE_MAP):
            return None
        
        pieceClass = self.PIECE_MAP[string.lower()]
        if string == string.lower(): # meaning: if string is lowercase
            color = 'black'
        else:
            color = 'white'
        
        return pieceClass(color, board)
    
    def moveNeedsPromotion(self, move, board):
        # castling move or anything else really special?
        if move.fromField is None:
            return False
        # already defined promotion type?
        if not(move.toPiece is None):
            return False
        # not even a pawn?
        if not(move.fromPiece.shortName.lower() in self.PAWN_PIECE_TYPES):
            return False
        # isn't target a promotion field?
        if not(move.toField in self.promotionFields[move.fromPiece.color]):
            return False
        
        return True
       
    def move(self, move, board, preGeneratePossibleMoves=True, noHandleCapture=False):
        moves = [move]

        # castling moves first
        cType = -1
        if move.annotation == 'SHORTCASTLING':
            cType = 0
        elif move.annotation == 'LONGCASTLING':
            cType = 1
        if cType != -1:
            # TODO fix to work with Chess960 
            # (move might hide one of the pieces, use setPiece feature)
            
            # generate moves
            color = self.getCurrentPlayer(board).color
            kingMove = Move(self.castlingPositions[color][0], self.castlingTargetPositions[color][cType * 2])
            rookMove = Move(self.castlingPositions[color][1 + cType], self.castlingTargetPositions[color][cType * 2 + 1])
            moves = [kingMove, rookMove]
            # mark done
            if not self.CASTLING_MULTIPLE_TIMES:
                board.castlingsPossible[color] = [False, False]

        # delegate the actual moving to the board we are operating on
        board.moveHistory.append(move)
        for xMove in moves:
            # annotate with current player
            if not isinstance(xMove, NullMove):
                xMove.player = self.getCurrentPlayer(board)
                xMove.simpleParse(board)
                xMove.fullParse(board)        
            board.move(xMove, noHandleCapture)
        # TODO parse check here?
        
        # parse additional draw conditions
        # x moves rule
        if self.DRAW_X_MOVES:
            board.drawXMoveCounter += 1
            if (move.annotation is None) and ((move.fromPiece.getShortName().lower() in self.PAWN_PIECE_TYPES) or not(move.takenPiece is None)):
                board.drawXMoveCounter = 0
            
        # repetition
        if self.DRAW_REPETITION:
            board.drawCountRepetition()
        
        
        if isinstance(move, NullMove):
            return moves
        
        if board == self.board and preGeneratePossibleMoves:
            # generate possible moves for the next round
            self.possibleMoves = None
            self.parsePossibleMoves()
        
        # bind to board
        for move in moves:
            move.board = self.board
            
        # reject all non-used draw offers (auto-decline)
        for player in self.players:
            player.offeringDraw = False
            
        return moves
        
    def handleCaptureMove(self, move, board):
        # put the piece to the capturePocket
        board.capturePockets[self.getLastCurrentPlayer(board).color].add(board.fields[move.toField])
        
        if self.USE_POCKET and self.USE_CRAZYHOUSE_POCKET:
            self._putPieceToPocket(board.fields[move.toField], board.pockets[self.getLastCurrentPlayer(board).color], flipColor=True)

    def _putPieceToPocket(self, originalPiece, targetPocket, flipColor=False):
        # and copy the piece with inverted color to the pocket
        freshPiece = copy.copy(originalPiece)
        if flipColor:
            freshPiece.color = 'white' if freshPiece.color == 'black' else 'black'
        freshPiece.board = None
        
        # make sure the pawn is slow no matter where it is put // TODO rule check!
        if isinstance(freshPiece, Pawn):
            freshPiece.endInit() # important to make him look the other side
            freshPiece.moveCount = 1
            freshPiece.changedSpeed = False
       
        targetPocket.add(freshPiece)
     
        
    def addPlayer(self, player):
        player.game = self
        player.color = self.COLORS[self.joinedPlayers]
        print(self.joinedPlayers)
        self.players.append(player)
        self.joinedPlayers += 1
    
    def addWatcher(self, watcher):
        self.watchers.append(watcher)
        
    def getPromotionOptions(self, color):
        if color == 'white':
            return [x.upper() for x in self.sortPieceList(self.possiblePromotionPieces)]
        else:
            return self.sortPieceList(self.possiblePromotionPieces)
                        
    def getSlotsMessageData(self):
        slotList = []
        for i in range(len(self.players)):
            player = self.players[i]
            playerDict = dict()
            playerDict['open'] = player.dummy
            playerDict['desc'] = self.COLORS[i]
            playerDict['pname'] = '' if player.dummy else player.name
            playerDict['joinId'] = player.mq.shortenedId
            slotList.append(playerDict)
        return slotList
    
    def getPocketMessage(self, onlyNew=True):
        if not self.USE_POCKET:
            return None
        if onlyNew and not self.board.pockets['white'].dirty and not self.board.pockets['black'].dirty:
            return None
        result = {}
        data = {'board_id': self.board.id}
        data['pockets'] = ''.join([piece.getShortName() for piece in self.board.pockets['white'].getPieces()]) + ',' + ''.join([piece.getShortName() for piece in self.board.pockets['black'].getPieces()])
        result['0'] = data
        return Message('gamesit', result)
    
    def getSituationMessage(self, mq, force=False, player=None, init=False):
        if player is None:
            subject = mq.subject
        else:
            subject = player            
            
        result = {}
        send = False
        counter = 0 # this code is prepared for multi-board games, but it is not used

        # check boards
        data = {'board_id': self.board.id}
        flipTotal = subject.flipBoard != subject.game.board.inherentlyFlipped
        if force or self.board.resend:
            send = True
            data['flipped'] = flipTotal != self.board.inherentlyFlipped
            data['fen'] = self.getFenPos(self.board, mq.subject)
            data['board_size'] = str(self.board.width) + 'x' + str(self.board.height)
            # add players
            if init:
                playerData = ''
                # collect all players for bottom pocket ("white")
                bottomPlayers = filter(lambda player: not player.flipBoard, self.players)
                for player in bottomPlayers:
                    playerData += '%s:%s,' % (player.name, player.mq.shortenedId)
                playerData = playerData[:-1] + '/'
                # collect all players for top pocket ("schwarz")
                topPlayers = filter(lambda player: player.flipBoard, self.players)
                for player in topPlayers:
                    playerData += '%s:%s,' % (player.name, player.mq.shortenedId)
                playerData = playerData[:-1]
                # add players to the board data
                data['players'] = playerData  # format: name:id,name:id/name:id,name:id
            
            # add current player if applicable    
            if not(self.getCurrentPlayer(self.board) is None):
                data['currP'] = self.getCurrentPlayer(self.board).mq.shortenedId

            # add last move if applicable    
            if len(self.board.moveHistory) > 0 and self.SHOW_LAST_MOVE:
                # TODO select last non-NullMove
                lastMove = self.board.moveHistory[-1];
                if not isinstance(lastMove, NullMove):
                    if lastMove.board is None:
                        data['lmove_from'] = lastMove.fromField
                        data['lmove_to'] = lastMove.toField
                    else:                    
                        data['lmove_from'] = str(lastMove.board.id) + '_' + str(lastMove.fromField)
                        data['lmove_to'] = str(lastMove.board.id) + '_' + str(lastMove.toField)
        
        # pockets
        for key in self.board.pockets:
            pocket = self.board.pockets[key]
            if force or self.board.resend or pocket.dirty:
                send = True
                data['pockets'] = ''.join([piece.getShortName() for piece in self.board.pockets['white'].getPieces()]) + ',' + ''.join([piece.getShortName() for piece in self.board.pockets['black'].getPieces()])
        for key in self.board.capturePockets:
            capturePocket = self.board.capturePockets[key]
            if force or self.board.resend or capturePocket.dirty:
                send = True
                data['capturePockets'] = ''.join([piece.getShortName() for piece in self.board.capturePockets['white'].getPieces()]) + ',' + ''.join([piece.getShortName() for piece in self.board.capturePockets['black'].getPieces()])
                    
        result[str(counter)] = data
        counter += 1
        
        if init:
            result['gameId'] = self.id
            # add ownPlayers
            result['playerSelf'] = mq.shortenedId + ',' + ','.join(mq.subject.aliases)

        if send:
            return Message('gamesit', result)
        return None
    
    def isRepetitionDraw(self):
        if not self.DRAW_REPETITION:
            return
        return self.getRepetitionCount() >= self.DRAW_REPETITION_VALUE

    def getRepetitionCount(self):
        currPos = self.getPositionHash()
        try:
            return self.board.positions[currPos]
        except KeyError:
            return 0
    
    def getPositionHash(self):
        # TODO include player's turn, castling options, en passant options in the dict's key
        return self.getFenPos(self.board, self.players[0])
    
    def isXMoveDraw(self):
        if not self.DRAW_REPETITION:
            return
        return self.board.drawXMoveCounter >= self.DRAW_X_MOVES_VALUE
        
    def getGameOverMessage(self):
        player = self.getNextCurrentPlayer()
        go = GameOver(self.board)
        if go.noLegalMove():
            if go.inCheck():
                return self._valueResult(player, 'Checkmate')
            else:
                return self._valueResult(player, 'Stalemate')
            
            # TODO 50 moves, repetition
            
        return None
    
    def _valueResult(self, player, msg):
        if msg == 'Checkmate':
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
        elif msg == 'Extincted':
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
        elif msg == 'Stalemate':
            winner = ''
            result = '0.5-0.5'
        
        return self._generateGameOverMessage(msg, result, winner)
            
    def _generateGameOverMessage(self, msg, result, winner):
        # build message
        if not(msg is None):
            return Message('gameover', {'winner': winner, 'msg': msg, 'result': result})
       
    def sortPieceList(self, pieceList):
        return sorted(pieceList, key=lambda piece: self.PIECE_MAP[piece](None, self.board).value, reverse=True)
        
    def getCurrentPlayer(self, board=None):
        if board == None:
            board = self.board        
        return self.players[len(board.moveHistory) % self.NUM_PLAYERS]

    def getNextCurrentPlayer(self, board=None):
        if board == None:
            board = self.board        
        return self.players[(len(board.moveHistory) + 1) % self.NUM_PLAYERS]

    def getLastCurrentPlayer(self, board):
        return self.players[((len(board.moveHistory) - 1) + self.NUM_PLAYERS) % self.NUM_PLAYERS]

    def getNextPlayer(self, board, player):
        found = False
        for pos in range(len(self.players)):
            if self.players[pos] == player:
                found = True
                break
            
        if not found:
            return None
        return self.players[(pos + 1) % self.NUM_PLAYERS]    

    def getNextColor(self, color):
        found = False
        for pos in range(len(self.COLORS)):
            if self.COLORS[pos] == color:
                found = True
                break
            
        if not found:
            return None
        return self.COLORS[(pos + 1) % len(self.COLORS)]    
        
    def parsePossibleMoves(self, force=False):
        if force:
            self.possibleMoves = None
            
        if self.getCurrentPlayer(self.board) is None:
            return
        elif not(self.possibleMoves is None):
            return        
        
        moveSet = self.getPossibleMoves(self.board, checkTest=self.CHECK_FOR_CHECK)
        
        # debug
        #for move in moveSet:
        #    move.simpleParse(self.board)
        #    move.fullParse(self.board)
        #print("I think current player could move like this: " + str(moveSet))
        
        self.possibleMoves = moveSet
        
    def getPossibleMoves(self, board, checkTest=True, player=None, noCastlingMoves=False, noDropMoves=False):
        if not checkTest:
            oldLogLevel = logger.level
            logger.setLevel(logging.ERROR)
        logger.debug('getPossibleMoves')
        # default
        if player is None:
            player = self.getCurrentPlayer(board)
        logger.debug('Player: %s' % player.color)
            
        moveSet = self.findAllPieceMoves(board, player, noDropMoves)
        # materialize
        logger.debug('Unfiltered moves generated:')
        for move in moveSet:
            move.simpleParse(board)
            move.fullParse(board)        
            logger.debug(move.str)
            
        # filter
        moveSet = self.filterMovesByRules(moveSet, board, player, noCastlingMoves)
        logger.debug('After filtering by rules: %s' % str([move.str for move in moveSet]))
        if checkTest:
            moveSet = self.filterMovesToCheck(moveSet, board, player)
            logger.debug('After check filter: %s' % str([move.str for move in moveSet]))
        logger.debug('=============')
        if not checkTest:
            logger.setLevel(oldLogLevel)
        return moveSet
    
    def findAllPieceMoves(self, board, player, noDropMoves=False):
        # get all the player's pieces
        pieces = board.findPlayersPieces(player)
        # get all their candidate moves
        moveSet = set()
        for pos in pieces:
            moveSet |= board.fields[pos].getPossibleMoves(pos)
            
        if self.USE_POCKET and not noDropMoves:
            moveSet = moveSet.union(self.createPocketMoves(board, player))
            
        return moveSet
    
    def createPocketMoves(self, board, player):
        moveSet = set()
        # generate all moves from pocket
        playersPocket = board.pockets[player.color]
        colNo = self.COLORS.index(player.color)
        # find all empty fields on board
        emptyFields = []
        for i in range(len(self.board.fields)):
            if self.board.fields[i] is None:
                emptyFields.append(i)
        
        # create the move objects
        for i in range(len(playersPocket.getPieces())):
            for j in emptyFields:
                if self.DROP_NO_PAWN_TO_PROMOTION_FIELDS:
                    # filter posing pawns to promotion fields
                    if (playersPocket.getPieces()[i].shortName in self.PAWN_PIECE_TYPES) and (j in self.allPromotionFields):
                        continue
                moveSet.add(Move('p' + str(colNo) + str(i), j))
        return moveSet
    
    def parseCastling(self, moveSet, board, player):
        if True in board.castlingsPossible[player.color]:
            # has the king moved already?
            kingPiece = board.fields[self.castlingPositions[player.color][0]]
            if not(kingPiece is None) and kingPiece.moveCount > 0 and not self.CASTLING_IF_KING_HAS_MOVED:
                # destroys both castling possibilities!
                board.castlingsPossible[player.color] = [False, False]
                return moveSet       
                        
            # short / long
            for cType in [0, 1]:
                if board.castlingsPossible[player.color][cType]:
                    good = True
                    # has the rook moved already?
                    rookPiece = board.fields[self.castlingPositions[player.color][1 + cType]]
                    if not(rookPiece is None) and rookPiece.moveCount > 0 and not self.CASTLING_IF_ROOK_HAS_MOVED:
                        # destroys this castling possibility!
                        board.castlingsPossible[player.color][cType] = False
                        good = False
                    # any relevant field non-empty?
                    if good:
                        # relevant fields are any between rook's and king's start and target fields
                        leftPos = min(self.castlingPositions[player.color][0],
                                      self.castlingPositions[player.color][1 + cType],
                                      self.castlingTargetPositions[player.color][2 * cType],
                                      self.castlingTargetPositions[player.color][2 * cType + 1])
                        rightPos = max(self.castlingPositions[player.color][0],
                                      self.castlingPositions[player.color][1 + cType],
                                      self.castlingTargetPositions[player.color][2 * cType],
                                      self.castlingTargetPositions[player.color][2 * cType + 1])
                        # check them for emptiness (moving rook being there is okay [Chess960!])
                        for pos in range(leftPos, rightPos + 1):
                            if not (board.fields[pos] is None) and pos != self.castlingPositions[player.color][0] and pos != self.castlingPositions[player.color][1 + cType]: # empty, king, rook
                                good = False
                                break

                    # fields for king checked?          
                    if good and True:
                        # get all attacked fields
                        opponentMoves = self.getPossibleMoves(board, False, self.getNextPlayer(board, player), noCastlingMoves=True, noDropMoves=True)
                        opponentAttackedFields = set()
                        for oMove in opponentMoves:
                            opponentAttackedFields.add(oMove.toField)
                        
                        # get fields king will cross (including start and end)
                        kingPos = self.castlingPositions[player.color][0]
                        kingTargetPos = self.castlingTargetPositions[player.color][2 * cType]
                        leftPos = min(kingPos, kingTargetPos)
                        rightPos = max(kingPos, kingTargetPos)
                        
                        # compare
                        for pos in range(leftPos, rightPos + 1):
                            if pos in opponentAttackedFields:
                                # test which type of check has happened and obey settings
                                if pos == kingPos and not self.CASTLING_FROM_CHECK:
                                    good = False
                                    break
                                elif pos == kingTargetPos and not self.CASTLING_TO_CHECK:
                                    good = False
                                    break
                                elif not self.CASTLING_THROUGH_CHECK:
                                    good = False
                                    break
                    
                    # good!
                    if good:
                        move = Move(None, None)
                        move.annotation = 'SHORTCASTLING' if cType == 0 else 'LONGCASTLING'
                        moveSet.add(move)
        
        return moveSet

    def parsePromotion(self, moveSet, board, player):
        resultSet = copy.copy(moveSet)
        for move in moveSet:
            if self.moveNeedsPromotion(move, board):
                for toPiece in self.getPromotionOptions(player.color):
                    promotionMove = copy.copy(move)
                    promotionMove.toPiece = toPiece
                    resultSet.add(promotionMove)        
        return resultSet

    def parseEnPassant(self, moveSet, board, player):
        return moveSet
        
    def filterMovesByRules(self, moveSet, board, player, noCastlingMoves=False):
        # add (!) castling options here
        if self.CASTLING and not noCastlingMoves:
            self.parseCastling(moveSet, board, player)
        # add promotion variants
        if self.PROMOTION:
            self.parsePromotion(moveSet, board, player)
        # add en passant moves
        if self.EN_PASSANT:
            self.parseEnPassant(moveSet, board, player)
        # adhere to blocking status of fields
        for move in set(moveSet):
            if move.toField in self.BLOCKED_FIELDS:
                moveSet.remove(move)
        return moveSet

    def filterMovesToCheck(self, moveSet, board, player):
        for move in set(moveSet): # work on a copy to be able to remove inside
            logger.debug('Testing move %s for check' % move.str)
            # no more tests for castling (it has already been filtered for moving into check!)
            if not(move.annotation is None) and 'CASTLING' in move.annotation:
                continue
            
            move.simpleParse(self.board)
            #print('filtering ' + str(move))
            # create a board copy for analysis purposes
            whatIfBoard = copy.deepcopy(self.board)
            logger.debug('board vs. whatIfBoard:\n%s\n\n%s' % (str(board), str(whatIfBoard)))
            self.move(move, whatIfBoard, noHandleCapture=True)
            logger.debug('whatIfBoard after:\n%s' % str(whatIfBoard))
            #print("what if? \n" + whatIfBoard.__unicode__())
            # did the player stay in check?            
            if whatIfBoard.isInCheck(player):
                logger.debug('still in check -> removing move %s from the list' % move.str)
                moveSet.remove(move)
            else:
                logger.debug('not in check -> keeping move %s in the list' % move.str)
        return moveSet
            
    def getBoard(self, boardId):
        if str(self.board.id) == str(boardId):
            return self.board
        return None 
    
    def isLegalMove(self, move, boardId=None):
        self.parsePossibleMoves()
        if self.possibleMoves is None:
            return False
        if move in self.possibleMoves:
            return True
        
        return False
    
    def getFenPos(self, board, player):
        return self._getFenPosFiltered(board, player, [])

    def _getFenPosFiltered(self, board, player, hiddenList):
        fenString = ''
        # build
        for row in range(board.height):
            for col in range(board.width):
                pos = row * board.width + col
                piece = board.fields[pos]
                if piece is None or pos in hiddenList:
                    fenString = fenString + '_'
                else:
                    fenString = fenString + piece.getShortName()
            fenString = fenString + '/'
        # shorten
        for length in range(board.width, 0, -1):
            fenString = fenString.replace(('_' * length), str(length))
            
        return fenString[:-1]
    
    def __unicode__(self):
        return "[Game] id=%s, type=%s" % (self.id, self.gameType)
        
    def __str__(self):
        return self.__unicode__()
    
