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


class ModernGame(ClassicGame):    
    meta = {'title': 'Modern Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Modern_chess',
            'details': "",
            'players': 2}
    def startInit(self):
        super(ModernGame, self).startInit('rnbqkibnr/ppppppppp/9/9/9/9/PPPPPPPPP/RNBIKQBNR')
        self.pieceMap['i'] = PrimeMinister


class CapablancaGame(ClassicGame):
    meta = {'title': 'Capablanca Chess',
           'desc': "",
           'link': 'http://en.wikipedia.org/wiki/Capablanca_chess',
           'details': "",
           'players': 2}       
    def startInit(self):
        super(CapablancaGame, self).startInit('rnibqkbhnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNIBQKBHNR')
        self.pieceMap['i'] = Archbishop
        self.pieceMap['h'] = Chancellor

 
class MilleniumGame(ClassicGame):    
    meta = {'title': 'Millenium Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Chess_variant#Chess_with_different_boards',
            'details': "",
            'players': 2}  
    def startInit(self):
        super(MilleniumGame, self).startInit('rnbqkbnrnbqkbnr/ppppppppppppppp/15/15/15/15/PPPPPPPPPPPPPPP/RNBQKBNRNBQKBNR')


class DoublewideGame(ClassicGame):  
    meta = {'title': 'Doublewide Chess',
            'desc': "",
            'link': 'http://en.wikipedia.org/wiki/Chess_variant#Chess_with_different_boards',
            'details': "",
            'players': 2}    
    def startInit(self):
        super(DoublewideGame, self).startInit('rnbqkbnrrnbqkbnr/pppppppppppppppp/16/16/16/16/PPPPPPPPPPPPPPPP/RNBQKBNRRNBQKBNR')

