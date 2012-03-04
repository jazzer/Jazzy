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

import logging
from datetime import datetime, timedelta

logger = logging.getLogger('jazzyLog')


class Clock(object):
    def __init__(self):
        self.time_controls = []
        self.completed_move_counter = 0
        self.last_started = None
        self.is_active = False
        self.current_time_control = None
        self.current_time_control_index = None
        self.was_expired = False
    
    def addTimeControl(self, time_control):
        self.time_controls.append(time_control)
        if self.current_time_control is None:
            self.current_time_control_index = 0
            self.current_time_control = self.time_controls[self.current_time_control_index]
            
    def isExpired(self):
        return self.was_expired or self.current_time_control.time_left <= timedelta(seconds=0)
    
    def penalty(self, timedelta_value):
        self.bonus(-timedelta_value)
        
    def bonus(self, timedelta_value):
        if self.current_time_control is None:
            return
        self.current_time_control.time_left += timedelta_value
    
    def getRemainingTime(self):
        if self.current_time_control is None:
            return timedelta.max # make sure to handle this as unlimited client side
        # subtract time that has passed (if active) 
        if self.is_active and not(self.last_started is None):
            remaining = self.current_time_control.time_left - (datetime.now() - self.last_started)
            return remaining
        else:
            return self.current_time_control.time_left
    
    def nextMove(self):
        if self.current_time_control is None:
            return
        self.last_started = datetime.now()
        self.is_active = True
        self.was_expired = False
        
    def stop(self):
        if self.current_time_control is None or not self.is_active:
            return
        self.completed_move_counter += 1
        self.current_time_control.time_left = self.getRemainingTime()
        # check if time's up and remember that (for enabling claiming even on
        # time controls that add time per completed move)
        if self.isExpired():
            self.was_expired = True            
        # add time per move
        self.current_time_control.time_left += self.current_time_control.time_per_move

        self.is_active = False
        self.last_started = None
        # did we just finish a time control? then activate next time control
        if self.current_time_control.moves != 0 and self.current_time_control.moves == self.completed_move_counter:
            last_time_control = self.current_time_control
            self.current_time_control_index += 1
            self.current_time_control = self.time_controls[self.current_time_control_index]
            # transfer remaining time?
            if last_time_control.transfer:
                self.bonus(last_time_control.time_left)
            
    def __str__(self):
        return self.__unicode__()
    def __unicode__(self):
        diff = self.getRemainingTime()
        # handle negative times
        if diff.days >= 0:
            return '%s' % round(diff.seconds + diff.microseconds*1E-6, 2)
        else:
            return '%s' % round((diff.seconds-86400) + diff.microseconds*1E-6, 2)


class TimeControl(object):    
    def __init__(self, fixed_time, time_per_move, moves, transfer=True):
        self.fixed_time = fixed_time
        self.time_per_move = time_per_move
        self.moves = moves
        self.transfer = transfer
        # calculate
        self.time_left = fixed_time
        
    def __str__(self):
        return self.__unicode__()
    def __unicode__(self):
        return 'TimeControl: %s fixed, %s per move, %s moves' % (self.fixed_time, self.time_per_move, self.moves)
        
        
class UnlimitedClock(Clock, object):
    pass

class BlitzClock(Clock, object):
    def __init__(self):
        super(BlitzClock, self).__init__()
        # add the specific time controls
        self.addTimeControl(TimeControl(timedelta(minutes=2), timedelta(seconds=30), 0)) # all moves in 5 minutes

class TraditionalClock(Clock, object):
    def __init__(self):
        super(BlitzClock, self).__init__()
        # add the specific time controls
        self.addTimeControl(TimeControl(timedelta(hours=2), timedelta(seconds=0), 40, transfer=True)) # first 40 moves in 2 bours
        self.addTimeControl(TimeControl(timedelta(minutes=60), timedelta(seconds=0), 0)) # 1 hour for all the rest
                
