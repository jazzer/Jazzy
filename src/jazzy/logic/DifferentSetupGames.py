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

# http://en.wikipedia.org/wiki/Legan_chess
class LeganGame(ClassicGame):
    meta = {'title': 'Legan Chess',
        'desc': 'Playing on a board rotated by 45 degrees',
        'link': 'http://en.wikipedia.org/wiki/Legan_chess',
        'details': "The inital position is adapted so that every player starts from one corner. Pawn movements are adjusted, so that they move towards each other. Promotion is possible in the enemy's corner.",
        'players': 2} 
           
    def startInit(self):
        super(LeganGame,self).startInit('knbrp3/bqpp4/npp5/rp1p3P/p3P1PR/5PPN/4PPQB/3PRBNK')
        self.PIECE_MAP['p'] = LeganPawn
        self.promotionFields = [[0, 1, 2, 3, 8, 16, 24], [39, 47, 55, 60, 61, 62, 63]]
        self.CASTLING = False

class PawnGame(ClassicGame):
    meta = {'title': 'Pawn Chess',
            'desc': 'Trying to get pawns promoted',
            'link': '',
            'details': 'The player who first gets one of his pawns promoted, wins.',
            'players': 2}

    def startInit(self):
        super(PawnGame,self).startInit('8/pppppppp/8/8/8/8/PPPPPPPP/8')
        self.CASTLING = False
        # TODO game over handling!        
