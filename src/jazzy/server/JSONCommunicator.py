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



import json
from jco.ServerRegistry import ServerRegistry

class JSONCommunicator():

    def __init__(self):
        pass

    @staticmethod
    def getGameList():
        registry = ServerRegistry()
        gameList = registry.getGameList()
        print("GameList: ", gameList)
        jsonObject = []
        for game in gameList:
            game_entry = {}
            game_entry['id'] = game.id
            game_entry['type'] = game.type
            game_entry['numPlayers'] = len(game.playerList)
            print("Game entry: ", game_entry)
            jsonObject.append(game_entry)
        return json.dumps(jsonObject, indent=2)     
    
    def getGameSituation(self):
        pass

    def doMove(self, param):
        pass
        
