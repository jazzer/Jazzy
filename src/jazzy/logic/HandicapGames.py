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

class HandicapPawnAndMoveGame(ClassicGame, object):
    meta = {'title': 'Handicap Pawn and Move',
            'desc': 'Handicap game where the stronger player plays black and without pawn f7. Otherwise Classic Chess rules as defined by FIDE apply.',
            'link': 'http://en.wikipedia.org/wiki/Chess_handicap',
            'details': 'The goal is to checkmate the king.',
            'players': 2}
     
    def startInit(self):
        super(HandicapPawnAndMoveGame, self).startInit('rnbqkbnr/ppppp1pp/8/8/8/8/PPPPPPPP/RNBQKBNR')

class HandicapKnightGame(ClassicGame, object):    
    meta = {'title': 'Handicap Knight',
            'desc': 'Handicap game where the stronger player plays white without knight b1. Otherwise Classic Chess rules as defined by FIDE apply.',
            'link': 'http://en.wikipedia.org/wiki/Chess_handicap',
            'details': 'The goal is to checkmate the king.',
            'players': 2}
    
    def startInit(self):
        super(HandicapKnightGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R1BQKBNR')
        
class HandicapRookGame(ClassicGame, object):    
    meta = {'title': 'Handicap Rook',
            'desc': 'Handicap game where the stronger player plays white without rook a1. Otherwise Classic Chess rules as defined by FIDE apply.',
            'link': 'http://en.wikipedia.org/wiki/Chess_handicap',
            'details': 'The goal is to checkmate the king.',
            'players': 2}

    def startInit(self):
        super(HandicapRookGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR')
        
class HandicapQueenGame(ClassicGame, object):    
    meta = {'title': 'Handicap Queen',
            'desc': 'Handicap game where the stronger player plays white without his queen. Otherwise Classic Chess rules as defined by FIDE apply.',
            'link': 'http://en.wikipedia.org/wiki/Chess_handicap',
            'details': 'The goal is to checkmate the king.',
            'players': 2}
 
    def startInit(self):
        super(HandicapQueenGame, self).startInit('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR')
