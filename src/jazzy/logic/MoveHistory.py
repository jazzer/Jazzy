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


class MoveHistory(object):
    
    def __init__(self):
        self.moves = [];
        
     
        

class Move():
    def __init__(self, fromField, toField):
        self.fromField = fromField
        self.toField = toField
        #self.fromPiece 
        #self.takenPiece  
        #self.toPiece 
        self.str = ''
        self.annotation = None
        
    def parse(self, board):
        self.fromPiece = copy.deepcopy(board.fields[self.fromField])
        if self.fromPiece is None:
            return
        self.takenPiece = copy.deepcopy(board.fields[self.toField])
        # generate text representation
        pieceName = '' if self.fromPiece.shortName == 'p' else self.fromPiece.shortName.upper()
        moveOrCapture = '-' if self.takenPiece is None else 'x'
        annotation = '' if self.annotation is None else ' (' + self.annotation + ')' 
        self.str = pieceName + board.fieldToString(self.fromField) + moveOrCapture + board.fieldToString(self.toField) + annotation
        
    def __eq__(self, move2):
        return move2.fromField == self.fromField and move2.toField == self.toField

    def __hash__(self):
        return hash(str(self.fromField) + ":" + str(self.toField))
    
    def __str__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return str(self.fromField) + "-" + str(self.toField) + " (=" + self.str +")"