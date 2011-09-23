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

class _MultiboardGame(ClassicGame):
    ''' meta class for using more than one board with two players each '''

    def startInit(self, gameClassList=[]):
        # instantiate games, keep a list of them
        self.gameList = []
        for gameClass in gameClassList:
            pass
        # number boards (assign IDs)
        

class BughouseGame(_MultiboardGame):
    meta = {'title': 'Bughouse Chess',
            'desc': 'Four-player variant of Crazyhouse',
            'link': 'http://en.wikipedia.org/wiki/Bughouse_chess',
            'details': 'German: Tandemschach',
            'players': 2}
  
    def startInit(self, boardNo=2):
        pass