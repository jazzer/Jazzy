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
from jazzy.logic.DifferentRulesGames import CrazyhouseGame
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
            id += 1

        self.id = uuid.uuid4().hex

       
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

    def getSlotsMessageData(self):
        slotList = []
        for game in self.gameList:
            newList = game.getSlotsMessageData()
            for entry in newList:
                entry['desc'] = 'Board %s, %s' % (str(game.board.id), entry['desc'])
            slotList += newList
        return slotList

    def getSituationMessage(self, mq, force=False, player=None):
        return super(_MultiboardGame, self).getSituationMessage(mq, force, player)


class BughouseGame(_MultiboardGame):
    meta = {'title': 'Bughouse Chess',
            'desc': 'Four-player variant of Crazyhouse',
            'link': 'http://en.wikipedia.org/wiki/Bughouse_chess',
            'details': 'German: Tandemschach',
            'players': 2}
  
    def startInit(self, boardCount=2):
        gameList = []
        for _ in range(boardCount):
            gameList.append(CrazyhouseGame())
        super(BughouseGame, self).startInit(gameList)
        
    def handleCaptureMove(self, move, board):
        return super(BughouseGame, self).handleCaptureMove(move, board)
