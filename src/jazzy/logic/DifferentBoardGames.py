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

class CylindricGame(ClassicGame):    
    def endInit(self):
        # do the normal things
        super(CylindricGame, self).endInit()
        # change something
        self.board.LIMIT_LEFT_RIGHT = False

class HoleGame(ClassicGame):    
    def startInit(self):
        # do the normal things
        super(HoleGame, self).startInit()
        # change something
        self.BLOCKED_FIELDS = [27, 28, 35, 36] # d4, d5, e4, e5
