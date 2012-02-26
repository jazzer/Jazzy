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

from jazzy.logic.ClassicGame import ClassicGame
from jazzy.server.MessageHandler import Message
import uuid

class _MultiboardGame(ClassicGame):
    ''' meta class for using more than one board with two players each '''

    def startInit(self, gameList=[]):
        #super(_MultiboardGame, self).startInit()
        self.gameList = gameList
        # assign IDs to boards
        id = 1
        for game in self.gameList:
            game.board.id = id
            game.metagame = self
            game.board.metagame = self
            id += 1

        self.id = uuid.uuid4().hex
        
        # set metagame
        for player in self.getAllPlayers():
            player.mq.metagame = self

       
    def endInit(self):
        pass
    
    def getAllPlayers(self):
        playerList = []
        for game in self.gameList:
            playerList += game.getAllPlayers()
        return playerList

    def getAllWatchers(self):
        watcherList = []
        for game in self.gameList:
            watcherList += game.getAllWatchers()
        return watcherList
    
    def getAllBoards(self):
        boardList = []
        for game in self.gameList:
            boardList += game.getAllBoards()
        return boardList

    def getSlotsMessageData(self):
        slotList = []
        for game in self.gameList:
            newList = game.getSlotsMessageData()
            for entry in newList:
                entry['desc'] = 'Board %s, %s' % (str(game.board.id), entry['desc'])
            slotList += newList
        return slotList

    def getSituationMessage(self, mq, force=False, player=None, init=False):
        gameSitMsg = Message('gamesit', {})
        boardCounter = 0
        for game in self.gameList:
            subMsg = game.getSituationMessage(mq, force, player, init)
            gameSitMsg.data[str(boardCounter)] = subMsg.data['0']
            boardCounter += 1
        gameSitMsg.data['gameId'] = self.id
        gameSitMsg.data['playerSelf'] = ','.join(mq.subject.aliases + [mq.shortenedId])
        return gameSitMsg


    def getCurrentPlayer(self, board=None):
        for game in self.gameList:
            if game.board == board:
                return game.getCurrentPlayer(board)
        return None
    
    def getNextCurrentPlayer(self, board=None):
        for game in self.gameList:
            if game.board == board:
                return game.getCurrentPlayer(board)
        return None

    def getLastCurrentPlayer(self, board):
        for game in self.gameList:
            if game.board == board:
                return game.getLastCurrentPlayer(board)
        return None
    
    def getNextPlayer(self, board, player):
        for game in self.gameList:
            if game.board == board:
                return game.getNextPlayer(board, player)
        return None
    
    def getBoard(self, boardId):
        for game in self.gameList:
            foundBoard = game.getBoard(boardId)
            if not(foundBoard is None):
                return foundBoard
        return None 

    

class BughouseGame(_MultiboardGame):
    meta = {'title': 'Bughouse Chess',
            'desc': 'Four-player variant of Crazyhouse',
            'link': 'http://en.wikipedia.org/wiki/Bughouse_chess',
            'details': 'German: Tandemschach',
            'players': 2}
  
    def startInit(self, boardCount=2):
        gameList = []
        for i in range(boardCount):
            game = _SingleBughouseGame()
            if i % 2 == 1:
                game.board.inherentlyFlipped = True
            gameList.append(game)
        super(BughouseGame, self).startInit(gameList)
        

class _SingleBughouseGame(ClassicGame):

    def startInit(self):
        super(_SingleBughouseGame, self).startInit()
        self.USE_POCKET = True # important!

    def handleCaptureMove(self, move, board):
        # take care of capturePocket
        super(_SingleBughouseGame, self).handleCaptureMove(move, board)

        originalPiece = board.fields[move.toField]
        # find the board next to mine on the right (wrapped)
        boards = self.metagame.getAllBoards()
        for i in range(len(boards)):
            if boards[i].id == board.id:
                targetBoard = boards[(i+1) % len(boards)]
                break
        targetPocket = targetBoard.pockets[originalPiece.color]
        self._putPieceToPocket(originalPiece, targetPocket, flipColor=False)
        board.game.distributeToAll(Message('srvmsg', {'msg': "putting it to board %s" % targetBoard.id}))
        
        # we interfered with another games, that sure has implications:
        targetBoard.game.possibleMoves = None # so that the player can instantly use it
        #targetBoard.game.parsePossibleMoves(force=True) # alternative
        # the pocket needs to be resent for everyone
        msg = targetBoard.game.getPocketMessage()
        if not (msg is None):
            for player in self.metagame.getAllPlayers():
                player.mq.addMsg(msg)
