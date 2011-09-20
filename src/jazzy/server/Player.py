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



from MessageHandler import MessageQueue

class Player():

    def __init__(self):
        self.mq = MessageQueue()
        self.name = "John Doe"
        self.offeringDraw = False
        self.pocket = Pocket()
        self.capturePocket = Pocket()
        
    def __unicode__(self):
        return "[Player]"
    
    def __str__(self):
        return self.__unicode__()
    
    
class Watcher():
    def __init__(self):
        self.mq = MessageQueue()
        self.mq.watching = True
        self.name = "John Doe"
        
    def __unicode__(self):
        return "[Watcher]"
    
    def __str__(self):
        return self.__unicode__()  
    
    
class Pocket():
    def __init__(self):
        self.pieces = []
        self.dirty = False
        
    def getPieces(self):
        return sorted(self.pieces, key=lambda piece: piece.value())
    
    def contains(self, pieceName):
        for piece in self.pieces:
            if piece.shortName == pieceName:
                return True
        return False
    
    # no guarantee which one is removed from the pocket
    def remove(self, pieceName):
        for piece in self.pieces:
            if piece.shortName == pieceName:
                self.pieces.remove(piece)
                return True
        return False
        
    def add(self, piece):
        self.pieces.append(piece)
        self.dirty = True
        