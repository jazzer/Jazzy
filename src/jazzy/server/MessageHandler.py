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



import uuid

class Message(object):

    def __init__(self, type, params):
        self.data = params
        self.data['mtype'] = type
        self.data['mid'] = uuid.uuid4().hex
        print("built msg: " + str(self.data))
        
    def __str__(self):
        return self.__unicode__()
    
    def __repr__(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return str(self.data)




class MessageQueue(object):

    def __init__(self):
        self.id = uuid.uuid4().hex
        self.shortenedId = self.id[0:10]
        self.msgs = []
        self.watching = False
        # self.subject (Player or Watcher)
        # self.game
        
    def addMsg(self, message):
        self.msgs.append(message.data)
        
    def __unicode__(self):
        return self.msgs
    
    def __str__(self):
        return self.__unicode__()
        
        


class MessageQueuePool(object):
    
    def __init__(self):
        self.mqs = {};

    def add(self, mqObject):
        self.mqs[mqObject.id] = mqObject;
        
    def get(self, mqId):
        if not (mqId in self.mqs):
            return None 
        return self.mqs[mqId]
    
    def __unicode__(self):
        return "MessageQueuePool"
        
    def __str__(self):
        return self.__unicode__()

