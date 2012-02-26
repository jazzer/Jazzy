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
from jazzy.logic.Pieces import *
import random

# http://en.wikipedia.org/wiki/Chess960
class Chess960Game(ClassicGame):
    meta = {'title': 'Chess960',
        'desc': 'Playing with a somewhat randomized starting position',
        'link': 'http://en.wikipedia.org/wiki/Chess960',
        'details': "Also known as Fischer Random Chess.",
        'players': 2} 
           
    def startInit(self):
        # find starting position
        id = random.randint(0, 959)
        print('Chess960 id: ' + str(id))
        emptyBaseline = 'abcdefgh'
        # using this algorithm: http://de.wikipedia.org/wiki/Chess960#IDs_f.C3.BCr_Startpositionen
        # 1. modulo 4, position of (white) bishop: 0=b, 1=d, 2=f, 3=h.
        step1 = id % 4
        positions = {0: 'b', 1: 'd', 2: 'f', 3: 'h'}
        baseline = emptyBaseline.replace(positions[step1], 'B');
        print('white bishop to ' + positions[step1] + " (" + str(step1) + ")")
        # 2. result modulo 4, position of (black) bishop: 0=a, 1=c, 2=e, 3=g.
        step2 = (id // 4) % 4
        positions = {0: 'a', 1: 'c', 2: 'e', 3: 'g'}
        baseline = baseline.replace(positions[step2], 'B');
        print('black bishop to ' + positions[step2] + " (" + str(step2) + ")")
        # 3. result modulo 6 = number of empty fields from left before the queen's position
        step3 = (id // 4 // 4) % 6
        baseline = self._replaceXthPos(baseline, emptyBaseline, step3, 'Q')
        # 4. by table
        step4 = id // 4 // 4 // 6 # yields 0-9
        table = {0: 'NNRKR', 
                 1: 'NRNKR',
                 2: 'NRKNR',
                 3: 'NRKRN',
                 4: 'RNNKR',
                 5: 'RNKNR',
                 6: 'RNKRN',
                 7: 'RKNNR',
                 8: 'RKNRN',
                 9: 'RKRNN'}
        for char in table[step4]:
            baseline = self._replaceXthPos(baseline, emptyBaseline, 0, char)
                        
        super(Chess960Game,self).startInit(baseline.lower() + '/pppppppp/8/8/8/8/PPPPPPPP/' + baseline)
        # TODO fix castling?
        
    def _replaceXthPos(self, text, emptyString, pos, newVal):
        targetChar = ''
        for char in text:
            if char in emptyString:
                pos = pos - 1
                if pos == -1:
                    targetChar = char
                    break                
        return text.replace(targetChar, newVal)

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
