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

import copy

class Move():
    def __init__(self, fromField, toField):
        try:
            self.fromField = int(fromField)
        except (ValueError, TypeError):
            self.fromField = fromField
            
        self.toField = toField
        self.fromPiece = None
        self.takenPiece = None  
        self.toPiece = None 
        self.str = ''
        self.annotation = None
        self.silent = False
        self.player = None
        self.isCheck = False
        self.board = None
        self.parsed = None
        
        
    def simpleParse(self, board, force=False):
        if self.fromField is None or self.toField is None:
            return
        if not (self.parsed is None) and not(force):
            return
        
        if board.getPieceByPos(self.fromField) is None:
            pass
        self.fromPiece = copy.deepcopy(board.getPieceByPos(self.fromField))
        self.takenPiece = copy.deepcopy(board.getPieceByPos(self.toField))
        
        self.parsed = board    
            
    def fullParse(self, board):
        if self.fromPiece is None:
            return # something is wrong
        
        # generate text representation
        if self.annotation == 'SHORTCASTLING':
            self.str = 'O-O'
        elif self.annotation == 'LONGCASTLING':
            self.str = 'O-O-O'
        else:
            pieceName = '' if self.fromPiece.shortName == 'p' else self.fromPiece.shortName.upper()
            moveOrCapture = '-' if self.takenPiece is None else 'x'
            annotation = '' if self.annotation is None else ' (' + self.annotation + ')' 
            fromFieldString = board.fieldToString(self.fromField) if board.getPiecesPocket(self.fromField) is None else '@'
            self.str = pieceName + fromFieldString + moveOrCapture + board.fieldToString(self.toField) + annotation
                        
    def __eq__(self, move2):
        return move2.fromField == self.fromField and move2.toField == self.toField and move2.annotation == self.annotation

    def __hash__(self):
        return hash(str(self.fromField) + ":" + str(self.toField) + ">" + str(self.annotation))
    
    def __str__(self):
        return self.__unicode__()
    
    def __repr__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return str(self.fromField) + "-" + str(self.toField) + " (=" + self.str + ")"
    
    
class NullMove():
    def __init__(self):
        pass
    
    def __str__(self):
        return self.__unicode__()
    
    def __repr__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return '-'
