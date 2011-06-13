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
from jazzy.logic.Pieces import *

class MicroGame(ClassicGame):    
    def startInit(self):
        super(MicroGame,self).startInit('knbr/p3/4/3P/RNBK')
        self.pieceMap['p'] = SlowPawn

class LosAlamosGame(ClassicGame):    
    def startInit(self):
        super(LosAlamosGame,self).startInit('rnqknr/pppppp/6/6/PPPPPP/RNQKNR')
        self.pieceMap['p'] = SlowPawn
