#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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


import time
#import http.server
import re
import inspect
from MessageHandler import MessageQueuePool
from GamePool import GamePool
from MessageHandler import Message
from jazzy.logic.Move import Move, NullMove
from Player import Player, Watcher
import json
from pprint import pprint 
import os, sys, copy, urllib2
from collections import OrderedDict
import gc
from jazzy.logic import DifferentSetupGames, DifferentPlayerGames, DifferentBoardGames, \
    DifferentPiecesGames, DifferentRulesGames, SmallerGames, BiggerGames, \
    HandicapGames, ClassicGame, TestGames
import logging
from os import path as op
import datetime
from tornado import web
from tornadio2 import SocketConnection, TornadioRouter, SocketServer


logger = logging.getLogger('jazzyLog')
handler = logging.StreamHandler(sys.stdout) 
frm = logging.Formatter('%(levelname)s: %(message)s') 
handler.setFormatter(frm)
logger.addHandler(handler) 
logger.setLevel(logging.ERROR)



PORT_NUMBER = 8090
ROOT_DIR = op.normpath(op.dirname(__file__) + "/../jsclient")
print 'root directory: ' + ROOT_DIR


# enable garbage collection
gc.enable()


# parse availible games
games = []
jsonGames = []
gameModules = OrderedDict([(ClassicGame, 'Classic Chess'),
               (DifferentSetupGames, 'Different Setup'),
               (SmallerGames, 'Smaller Games'),
               (BiggerGames, 'Bigger Games'),
               (DifferentRulesGames, 'Different Rules'),
               (DifferentPlayerGames, 'Different Players'),
               (DifferentPiecesGames, 'Different Pieces'),
               (DifferentBoardGames, 'Different Boards'),
               (HandicapGames, 'Handicap Games'),
               (TestGames, 'Test Games') # for debugging
               ])
for module in gameModules.keys():
    classes = inspect.getmembers(module, inspect.isclass(module))
    for name, obj in classes:
        if name.startswith('_'): # "games" starting with a dash are internal only
            continue
        try:
            if not(obj is dict) and (obj.__module__ == module.__name__):
                metaInfo = copy.copy(obj.meta)
                metaInfo['cat'] = gameModules[module]
                jsonGames.append(metaInfo)
                classMetaInfo = copy.copy(metaInfo)
                classMetaInfo['class'] = obj
                games.append(classMetaInfo)
        except AttributeError:
            pass
   
   
class GenericHandler():
    def sanitizeHTML(self, string):
        # TODO handle urlencoding here! possibly de- and reencode or filter 'bad' escape sequences? 
        result = re.sub(r'(<[^>]*>)', '', string)
        result = result.replace('%3C', '')
        result = result.replace('%3E', '')
        return result   
   
   
class SocketHandler(GenericHandler):
    @classmethod
    def handle_input(self, message, gameConnection):
        print message
        params = message.split("/")
        print params
        if len(params) > 1:
            mq = mqPool.get(params[1])
        
        if mq is None:
            print 'Access to non-existing message queue: %s' % params[1]; 
            return ''
            
        # make sure this socket is tied to the message queue?
        mq.socket = gameConnection
            
        if (params[0] == 'post' and params[2] == 'move'):            
            # filter watchers attempting to post stuff
            if mq.watching or mq.game.finished == True:
                return
            # only allow current player to post his move
            if mq.game.getCurrentPlayer().mq != mq:
                mq.socket.send(Message('alert', {'msg': 'Not your turn.'}).data)
                return
            
            game = mq.game
            
            # find board
            originalFrom = params[3]
            originalTo = params[4]
            shortFrom = originalFrom.replace('board_', '').replace('_field', '_');
            shortTo = originalTo.replace('board_', '').replace('_field', '_');
            boardId = shortFrom.split('_')[0]
            targetBoard = mq.game.getBoard(boardId)
            
            # create move
            if  shortFrom.split('_')[1] == 'SHORTCASTLING' or  shortFrom.split('_')[1] == 'LONGCASTLING':
                # castling
                postedMove = Move(None, None)
                postedMove.annotation = shortFrom.split('_')[1]
            else:
                # standard move
                fromField = shortFrom.split('_')[1]
                toField = int(shortTo.split('_')[1])
                postedMove = Move(fromField, toField)
                # do we have a promotion option set?
                if len(params) > 5:
                    postedMove.toPiece = game.getPieceByString(params[5], game.board) 

            
            # check move for correctness
            isLegalMove = game.isLegalMove(postedMove, targetBoard)
            # parse move
            postedMove.simpleParse(targetBoard)
            postedMove.fullParse(targetBoard)
                            
            # put the message to all players
            if isLegalMove:
                # do we have to ask for promotion piece?
                if game.moveNeedsPromotion(postedMove, targetBoard):
                    msg = Message('promote', {'from': originalFrom, 'to': originalTo})
                    # add options
                    msg.data['options'] = game.getPromotionOptions(postedMove.fromPiece.color)
                    mq.socket.send(msg.data)
                else:
                    moves = game.move(postedMove, targetBoard)
                    
                    # analyze if game is over
                    result = game.getGameOverMessage()
                    if not(result is None):
                        game.finished = True
    
                    # post all the moves the particular game created
                    for move in moves:                    
                        if isinstance(move, NullMove):
                            data = {'from':-1, 'to':-1}
                            data['silent'] = True
                        else:
                            # normal move
                            #move.simpleParse(mq.game.board)
                            if move.board is None:
                                data = {'from': move.fromField, 'to': move.toField}
                            else:
                                data = {'from': str(move.board.id) + '_' + str(move.fromField), 'to': str(move.board.id) + '_' + str(move.toField)}
                                
                            if move.silent:
                                data['silent'] = True
                            if not(move.toPiece is None):
                                if move.toPiece == '':
                                    data['toPiece'] = ''
                                else:
                                    data['toPiece'] = move.toPiece.getShortName()
                        if not(game.getCurrentPlayer(game.board) is None) and not(game.finished):
                            data['currP'] = game.getCurrentPlayer(game.board).mq.shortenedId
                        mq.metagame.broadcastSocket(Message('move', data).data)
                        
                    mq.metagame.broadcastSocket(Message('movehist', {'user': mq.subject.name, 'str': postedMove.str}).data)
                    
                    # debug position
                    logger.debug(str(game.board))
                    
                    # resend parts of the board that have changed (not forced)
                    for player in mq.game.players:
                        sitMsg = mq.game.getSituationMessage(mq, player=player)
                        if not(sitMsg is None):
                            player.mq.addMsg(sitMsg)
                    # clear board
                    mq.game.board.resend = False # TODO generalize
                    
                    # distribute the game over message if there was one
                    if not(result is None):
                        mq.metagame.broadcastSocket(result.data)
                    
            else: 
                # not legal move
                msg = Message('alert', {'msg': 'Illegal move.'})
                mq.socket.send(msg.data)
                if game.DEBUG_LEGAL_MOVES_ON_ILLEGAL_MOVE:
                    msg = Message('srvmsg', {'msg': 'Possible moves are: ' + str(sorted(mq.game.possibleMoves, key=lambda move: [str(move.fromField), move.toField]))})
                    mq.socket.send(msg.data)
        
        elif (params[0] == 'getsit'):
            print mq.metagame.getSituationMessage(mq, force=True, init=True).data
            return mq.metagame.getSituationMessage(mq, force=True, init=True).data
        
        # draw claims
        elif params[0] == 'claim':
            # filter watchers attempting to post stuff
            if mq.watching:
                return
                
            if params[2] == 'repetition':                    
                if mq.game.isRepetitionDraw():
                    mq.metagame.broadcastSocket(mq.game._generateGameOverMessage('Draw by repetition upon player\'s request', '0.5-0.5', None))
                else:
                    mq.addMsg(Message('alert', {'msg': 'No draw by repetition. This position has been on board {0} times.'.format(mq.game.getRepetitionCount())})) 
                    
            if params[2] == 'xmoverule':
                if mq.game.isXMoveDraw():
                    mq.metagame.broadcastSocket(mq.game._generateGameOverMessage('Draw by {0} move rule upon player\'s request'.format(mq.game.DRAW_X_MOVES_VALUE), '0.5-0.5'))
                else:
                    mq.addMsg(Message('alert', {'msg': 'No draw by {0} move rule. Counter is at {1}.'.format(mq.game.DRAW_X_MOVES_VALUE, mq.game.board.drawXMoveCounter)}))
                    
        # messages about game end (resigning, draws) 
        elif (params[0] == 'end'):
            # only players please!
            if isinstance(mq.subject, Player):
                # player resigned
                if (params[2] == 'resign'):
                    result = '0-1' if mq.subject.color == 'white' else '1-0' 
                    winner = mq.game.getNextCurrentPlayer() if mq.game.getCurrentPlayer() == mq.subject else mq.game.getCurrentPlayer()
                    mq.metagame.distributeToAll(mq.game._generateGameOverMessage('Player resigned.', result, winner))
                # player is offering draw
                if (params[2] == 'draw-offer'):
                    agreeingPlayers = []
                    for player in mq.game.players:
                        if player.offeringDraw:
                            agreeingPlayers.append(player)
                    
                    # rule: you may not offer a draw when you are on the move!
                    if not(mq.subject.offeringDraw) and (len(agreeingPlayers) > 0 or mq.subject != mq.game.getCurrentPlayer()):
                        # keep the player's decision
                        mq.subject.offeringDraw = True
                        
                        # do all players agree?
                        agreeingPlayers = []
                        for player in mq.game.players:
                            if player.offeringDraw:
                                agreeingPlayers.append(player)
                                
                        if len(agreeingPlayers) == len(mq.game.players):
                            # finish the game
                            mq.metagame.distributeToAll(mq.game._generateGameOverMessage('Players agreed.', '0.5-0.5', None))
                        else:
                            # ask the other players
                            mq.metagame.distributeToAll(Message('draw-offer', {}), agreeingPlayers)
                    
            
        # transfer chat message     
        elif (params[0] == 'post' and params[2] == 'chat'):            
            # filter watchers attempting to post stuff
            if mq.watching:
                return
            
            # sanitize
            msg = params[3]
            msg = self.sanitizeHTML(msg)
                        
            mq.metagame.broadcastSocket(Message('chat', {'user': mq.subject.name, 'msg': msg}), [mq.subject])
            

class HTTPJSONHandler(GenericHandler, web.RequestHandler):
    def createWatcher(self, game):
        watcher = Watcher()
        mq = watcher.mq
        mqPool.add(mq)            
        game.addWatcher(watcher)
        gamePool.add(game)
        # backlinks for the MQ
        mq.subject = watcher
        mq.game = game
        return mq
    
    def get(self, path):
        """Respond to a GET request."""
        # examine string
        params = path.split("/")
        print(path)
        #print(params)
        
        # -----------------------
        # dynamic content
        # -----------------------
        jsonoutput = {}
        if len(params) > 1:
            mq = mqPool.get(params[1])
            # can't answer if mq is not transferred (e.g. because it is yet unknown)
            if mq is None and not(params[0] in {'new', 'join', 'watch', 'getgames', 'getslots', 'admin'}):
                return
        # starting a new game (e.g. /new/classic)
        if (params[0] == 'new'):
            # find game
            input = urllib2.unquote(params[1])
            selectedGame = None
            print(input)
            for game in games:
                if game['title'] == input:
                    selectedGame = game 
            if selectedGame == None or selectedGame['class'].__name__.startswith('_'): # "games" starting with a dash are internal only 
                jsonoutput = json.dumps([{'msg': 'No valid game: ' + input}])
            else:
                # create desired game
                #try:
                game = selectedGame['class']()
                gamePool.add(game)
                for player in game.getAllPlayers():
                    mqPool.add(player.mq)
                # generate answer
                jsonoutput = json.dumps({'link': 'game.html?' + game.id})
                    
        elif (params[0] == 'getslots'):     
            try:    
                game = gamePool.games[params[1]]
            except KeyError:
                return
            jsonoutput = json.dumps(game.getSlotsMessageData())
            
        elif (params[0] == 'join'): 
            # message format: /join/[gameId]/[shortened mqId]/[playerName]
            # playerName starting with "bot:" indicates non-human player
            
            # find the player targeted
            try:    
                game = gamePool.games[params[1]]
                targetPlayer = None
                for player in game.getAllPlayers():
                    if player.mq.shortenedId == params[2]:
                        targetPlayer = player
                        break
            except KeyError:
                    jsonoutput = json.dumps({'msg': 'Invalid game ID.'})
            
            if targetPlayer is None:
                jsonoutput = json.dumps({'msg': 'Invalid slot ID.'})
            else:
                if not targetPlayer.dummy:
                    jsonoutput = json.dumps({'msg': 'Slot is taken.'})
                else:
                    playerName = params[3] if len(params) > 3 else ''
                    if playerName.startswith('bot:'):
                        playerName = playerName.replace('bot:', '')
                        # exchange the pregenerated player for the bot
                        # keep mq and all links in both directions
                        bot = playerName()
                        targetPlayer.mq.subject = bot
                        bot.mq = targetPlayer.mq
                        targetPlayer = bot
                        jsonoutput = json.dumps({'msg': 'Added %s.' % playerName})
                    else:
                        jsonoutput = json.dumps({'link': 'play.html?' + player.mq.id})
                    if playerName != '':
                        player.name = playerName
                    game.distributeToAll(Message('srvmsg', {'msg': 'Player %s joined.' % playerName}))
                    game.distributeToAll(Message('setname', {'name': playerName, 'id': player.mq.shortenedId}), [player])
                    # slot is taken now
                    targetPlayer.dummy = False
                    

        elif (params[0] == 'watch'):
            game = gamePool.games[params[1]]
            if game.NO_WATCHERS:
                jsonoutput = json.dumps([Message('srvmsg', {'msg': 'No watchers allowed.'}).data])
            else:
                mq = self.createWatcher(game)
                jsonoutput = json.dumps({'mqId': mq.id})
                mq.metagame.distributeToAll(Message('srvmsg', {'msg': 'Watcher joined.'}), [mq.subject])
         
        elif (params[0] == 'getgames'):
            jsonoutput = json.dumps(jsonGames)
        
        # admin panel functions
        # TODO check permissions (via some token output on server startup?)
        elif params[0] == 'admin':
            if params[1] == 'runtests':
                #test = Test();
                jsonoutput = json.dumps({'log': test.runTestGames()})          
            
        else:
            jsonoutput = json.dumps([])
        #print(jsonoutput)
        self.write(jsonoutput)

        

# server part
class GameConnection(SocketConnection):
    def on_open(self, info):
        self.send(Message('srvmsg', {'msg': 'Welcome to the server!'}).data)
        
    def on_message(self, message):
        self.send(SocketHandler.handle_input(message, self))

    def on_close(self):
        pass


class PingConnection(SocketConnection):
    def on_open(self, info):
        print 'Ping', repr(info)

    def on_message(self, message):
        pass       



class IndexHandler(web.RequestHandler):
    """Serve the index file"""
    def get(self):
        self.render(ROOT_DIR + '/new.html')

class RouterConnection(SocketConnection):
    __endpoints__ = {'/game': GameConnection,
                     '/ping': PingConnection}

    def on_open(self, info):
        print 'Router', repr(info)
   
        

                       


# Create tornadio server
jazzyRouter = TornadioRouter(RouterConnection)

# Create socket application
application = web.Application(
    jazzyRouter.apply_routes([(r"/", IndexHandler),
                              (r"/(.*\.(js|html|css|ico|gif|jpe?g|png|ogg|mp3))", web.StaticFileHandler, {"path": ROOT_DIR}),
                              (r"/([^(socket.io)].*)", HTTPJSONHandler)]),
    flash_policy_port = 843,
    flash_policy_file = op.join(ROOT_DIR, '/other/flashpolicy.xml'),
    socket_io_port = PORT_NUMBER,
    debug=True
)
        
if __name__ == "__main__":
    # prepare for the first games to be started 
    gamePool = GamePool()
    mqPool = MessageQueuePool()

    # create and start tornadio server
    SocketServer(application)
