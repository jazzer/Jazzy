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

class GamePool(object):
    
    def __init__(self):
        self.games = {};

    def add(self, game):
        self.games[game.id] = game
    
    
    def __unicode__(self):
        result = ""
        for game in self.games: 
            result = result + game.__unicode__()
        return result
        
    def __str__(self):
        return self.__unicode__()
