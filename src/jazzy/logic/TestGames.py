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

class CastlingTestGame(ClassicGame):    
    meta = {'title': 'Castling Tests',
            'desc': '',
            'link': '',
            'details': '',
            'players': 2}
   
    def startInit(self):
        # do the normal things
        super(CastlingTestGame, self).startInit('r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R')
