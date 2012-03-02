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

class CylinderGame(ClassicGame, object):    
    meta = {'title': 'Cylinder Chess',
            'desc': 'Playing on a cylindrical board',
            'link': 'http://en.wikipedia.org/wiki/Cylinder_chess',
            'details': 'The cylindrical board enables you to move pieces through the right border to the left side and vice versa.',
            'players': 2}
   
    def endInit(self):
        # do the normal things
        super(CylinderGame, self).endInit()
        # change something
        self.board.LIMIT_LEFT_RIGHT = False

class HoleGame(ClassicGame, object): 
    meta = {'title': 'Hole Chess',
            'desc': 'Playing on a board without center fields',
            'link': '#own_idea',
            'details': 'No piece can be placed on the fields e4, d4, e5, or d5. Giving check "through" those fields is possible though.',
            'players': 2}
       
    def startInit(self):
        # do the normal things
        super(HoleGame, self).startInit()
        # change something
        self.BLOCKED_FIELDS = [27, 28, 35, 36] # d4, d5, e4, e5
