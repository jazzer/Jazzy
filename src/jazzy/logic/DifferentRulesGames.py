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

from jazzy.logic.ClassicGame import ClassicGame
import math
from jazzy.logic.GameOver import GameOver
from jazzy.logic.Move import Move, NullMove
from jazzy.logic.Pieces import Pawn
import copy

class ExtinctionGame(ClassicGame):  
    meta = {'title': 'Extinction Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Extinction_chess',
            'details': "",
            'players': 2}
    
    def getGameOverMessage(self):
        # player extincted?
        player = self.getNextCurrentPlayer(self.board)
        go = GameOver(self.board)
        if go.notRequiredPiecesLeft(self.USED_PIECES):
            return self._valueResult(player, 'Extincted')
        # default stuff
        return super(ExtinctionGame, self).getGameOverMessage()
        
    def _valueResult(self, player, msg):
        if msg == 'Extincted':
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
            return self._generateGameOverMessage(msg, result, winner)
        # default stuff
        return super(ExtinctionGame, self)._valueResult(player, msg)

class ForwardGame(ClassicGame):
    meta = {'title': 'Forward Chess',
            'desc': 'No piece can ever move backwards or sidewards. Forward only!',
            'link': '',
            'details': '',
            'players': 2}
    
    def startInit(self):
        super(ForwardGame, self).startInit()
        # castling options
        self.CASTLING = False # disable

    def filterMovesByRules(self, moveSet, board, player, noCastlingMoves=False):
        moveSet = super(ForwardGame, self).filterMovesByRules(moveSet, board, player, noCastlingMoves)
        # remove the bad moves
        for move in set(moveSet):
            dir = -1 if player.color == 'white' else 1
            fromRow = board.splitPos(move.fromField)[1] 
            toRow = board.splitPos(move.toField)[1]
            if (toRow - fromRow) * dir <= 0:
                moveSet.remove(move)            
        return moveSet



class DarkGame(ClassicGame):
    meta = {'title': 'Dark Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Dark_chess',
            'details': '',
            'players': 2} 
    def startInit(self):
        super(DarkGame, self).startInit()
        self.CHECK_FOR_CHECK = False
        self.NO_WATCHERS = True
        self.SHOW_LAST_MOVE = False
    
    def getFenPos(self, board, player):
        hiddenSet = set(range(board.width * board.height))
        print(str(hiddenSet))
        # my pieces are visible
        hiddenSet.difference_update(set(board.findPlayersPieces(player)))
        print(str(hiddenSet))
        # my target fields are visible
        moves = board.getPlayerMoves(player)
        for move in moves:
            if move.toField in hiddenSet:
                hiddenSet.remove(move.toField)
        print(str(hiddenSet))
        return self._getFenPosFiltered(board, player, list(hiddenSet))

    def move(self, move, board):
        super(DarkGame, self).move(move, board)
        # always reissue current situation as message to all players
        for player in self.players:
            sitMsg = self.getSituationMessage(player.mq)
            # issue the message to the player
            player.mq.addMsg(sitMsg)
        return []
    
    def getGameOverMessage(self):
        # king killed
        player = self.getNextCurrentPlayer(self.board)
        go = GameOver(self.board)
        if go.notRequiredPiecesLeft(self.KING_PIECE_TYPES):
            return self._valueResult(player, 'Extincted')
        # default stuff
        return super(DarkGame, self).getGameOverMessage()


class AtomicGame(ClassicGame):
    meta = {'title': 'Atomic Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Atomic_chess',
            'details': "",
            'players': 2}
    def startInit(self):
        super(AtomicGame, self).startInit()
        # settings
        self.CHECK_FOR_CHECK = False
        
    def getGameOverMessage(self):
        # king killed
        player = self.getNextCurrentPlayer(self.board)
        go = GameOver(self.board)
        if go.notRequiredPiecesLeft(self.KING_PIECE_TYPES):
            return self._valueResult(player, 'Extincted')
        # default stuff
        return super(AtomicGame, self).getGameOverMessage()
     
    def move(self, move, board):
        capture = True
        if board.fields[move.toField] is None:
            capture = False
        
        explosionMoves = super(AtomicGame, self).move(move, board)
        
        if not capture:
            return explosionMoves
        
        # create explosion moves
        target = move.toField
        for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
                # piece itself
                #if x == 0 and y == 0:
                #    continue
                # fields around it
                explosionTarget = board.moveByDirection(target, x, y)
                if explosionTarget is None:
                    continue
                if board.fields[explosionTarget] is None:
                    continue 
                if board.fields[explosionTarget].shortName in self.PAWN_PIECE_TYPES:
                    continue 
                move = Move(explosionTarget, explosionTarget)
                move.toPiece = '' # indicates that field will be cleared
                move.silent = True
                # execute on board
                board.move(move) 
                explosionMoves.append(move)
                 
        return explosionMoves


class MonochromaticGame(ClassicGame):  
    meta = {'title': 'Monochromatic Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Monochromatic_chess',
        'details': "",
        'players': 2}
    
    def startInit(self):
        super(MonochromaticGame, self).startInit()
        self.CASTLING = False
    
    def filterMovesByRules(self, moveSet, board, player, noCastlingMoves=False):
        return self.colorCheck(moveSet, board, player, noCastlingMoves, 1)
        
    def colorCheck(self, moveSet, board, player, noCastlingMoves, modulo):
        # keep what's in basic game
        moveSet = super(MonochromaticGame, self).filterMovesByRules(moveSet, board, player, noCastlingMoves)
        # filter our moves
        for move in set(moveSet):
            fromSplit = self.board.splitPos(move.fromField);
            toSplit = self.board.splitPos(move.toField);
            # Manhattan distance even or odd?
            if (math.fabs(fromSplit[0] - toSplit[0]) + math.fabs(fromSplit[1] - toSplit[1])) % 2 == modulo:
                moveSet.remove(move)
        return moveSet
    
    def _valueResult(self, player, msg):
        if msg == 'Stalemate':
            winner = self.getCurrentPlayer(self.board).mq.shortenedId
            result = '0-1' if player.color == self.COLORS[0] else '1-0'
            return self._generateGameOverMessage('No legal move', result, winner)
        # default stuff
        return super(ExtinctionGame, self)._valueResult(player, msg)



class BichromaticGame(MonochromaticGame):    
    meta = {'title': 'Biochromatic Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Monochromatic_chess',
        'details': "",
        'players': 2}
        
    def filterMovesByRules(self, moveSet, board, player, noCastlingMoves=False):
        return self.colorCheck(moveSet, board, player, noCastlingMoves, 0)
        
        
 

class ChecklessGame(ClassicGame):    
    meta = {'title': 'Checkless Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Checkless_chess',
        'details': "",
        'players': 2} 
    def getGameOverMessage(self):
        result = super(ChecklessGame, self).getGameOverMessage()
        if result is None:
            player = self.getNextCurrentPlayer(self.board)
            go = GameOver(self.board)
            if go.inCheck():
                msg = 'Check without mate'
                winner = self.getCurrentPlayer(self.board).mq.shortenedId
                result = '0-1' if player.color == self.COLORS[0] else '1-0'
                return self._generateGameOverMessage(msg, result, winner)
            else:
                return None
        return result
    

class AntiGame(ClassicGame): 
    meta = {'title': 'Anti Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Antichess',
        'details': "",
        'players': 2} 
    # check is not important here
    def startInit(self):
        # default
        super(AntiGame, self).startInit()
        # change
        self.CHECK_FOR_CHECK = False
        self.CASTLING_FROM_CHECK = True
        self.CASTLING_THROUGH_CHECK = True
        self.CASTLING_TO_CHECK = True
        self.CAN_PROMOTE_TO_KING = True
        
    # force capturing if possible
    def filterMovesByRules(self, moveSet, board, player, noCastlingMoves = False):
        # default
        moveSet = super(AntiGame, self).filterMovesByRules(moveSet, board, player, noCastlingMoves)
        # change
        captureMoves = []
        for move in moveSet:
            if not(board.fields[move.toField] is None):
                captureMoves.append(move)
        if len(captureMoves) > 0:
            return set(captureMoves)
        # default
        return moveSet
     
    # you won if you lost all your pieces
    def getGameOverMessage(self):
        player = self.getCurrentPlayer(self.board)
        go = GameOver(self.board)
        if go.noPiecesLeft():
            msg = 'No pieces left'
            winner = player.mq.shortenedId
            result = '1-0' if player.color == self.COLORS[0] else '0-1'
            return self._generateGameOverMessage(msg, result, winner)
        elif go.noLegalMove():
            msg = 'No legal move'
            winner = ''
            result = '0.5-0.5'
            return self._generateGameOverMessage(msg, result, winner)
        return None
        

class MarseillaisGame(ClassicGame): 
    meta = {'title': 'Marseillais Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Marseillais_chess',
        'details': "",
        'players': 2}   
    def move(self, move, board):
        moveList = super(MarseillaisGame, self).move(move, board)

        print(str(board.moveHistory))
        insertMove = True
        if len(board.moveHistory) == 1:
            insertMove = False
        else:
            # don't insert a NullMove if not both last moves have been made by the same player
            if isinstance(board.moveHistory[-1], NullMove) or isinstance(board.moveHistory[-2], NullMove):
                insertMove = False
            elif board.moveHistory[-1].player == board.moveHistory[-2].player:
                insertMove = False
            # don't insert a NullMove if the last move has created check
            if not isinstance(board.moveHistory[-1], NullMove) and board.isInCheck(self.getNextPlayer(board, board.moveHistory[-1].player)):
                insertMove = False

        if insertMove:
            nullMove = NullMove()
            board.game.move(nullMove, board)
            moveList.append(nullMove)
        
        # recalc possible moves for the next round
        self.possibleMoves = None
        
        return moveList


class AndernachGame(ClassicGame):  
    meta = {'title': 'Andernach Chess',
        'desc': "",
        'link': 'http://en.wikipedia.org/wiki/Andernach_chess',
        'details': "",
        'players': 2}  
    def move(self, move, board):
        moveList = super(AndernachGame, self).move(move, board, preGeneratePossibleMoves=False)
        # flip color
        if not(move.takenPiece is None):
            board.fields[move.toField].setColor(self.getNextColor(board.fields[move.toField].color))
            # make sure to have new color rendered
            move.toPiece = copy.deepcopy(board.fields[move.toField])
            
        if board == self.board:
            # calc possible moves for the next round
            self.possibleMoves = None
            self.parsePossibleMoves()
        return moveList

class CrazyhouseGame(ClassicGame):  
    meta = {'title': 'Crazyhouse Chess',
        'desc': "rather Loop Chess (see Wikipedia article) right now",
        'link': 'http://en.wikipedia.org/wiki/Crazyhouse',
        'details': "",
        'players': 2}
    
    def startInit(self, fenPos=''):
        super(CrazyhouseGame, self).startInit()

        # crazyhouse
        self.USE_POCKET = True
        self.USE_CRAZYHOUSE_POCKET = True
        self.DROP_NO_PAWN_TO_PROMOTION_FIELDS = True
        self.DROP_NO_CHECKMATE = True
        self.DROP_NO_CHECK = False
