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

class HandycapPawnAndMoveGame(ClassicGame):
     def startInit(self):
        super(HandycapPawnAndMoveGame, self).startInit('rnbqkbnr/ppppp1pp/8/8/8/8/PPPPPPPP/RNBQKBNR')

class HandycapKnightGame(ClassicGame):    
    def startInit(self):
        super(HandycapKnightGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBNR')
        
class HandycapRookGame(ClassicGame):    
    def startInit(self):
        super(HandycapRookGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR')
        
class HandycapQueenGame(ClassicGame):    
    def startInit(self):
        super(HandycapQueenGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR')
