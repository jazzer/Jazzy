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



import time
import http.server
import re
import inspect
from MessageHandler import MessageQueuePool
from GamePool import GamePool
from MessageHandler import Message
from jazzy.logic.Move import Move, NullMove
from Player import Player, Watcher
import json
from pprint import pprint 
import os, sys, copy, urllib
from collections import OrderedDict
import gc
from jazzy.test.Test import Test
from jazzy.logic import DifferentSetupGames, DifferentBoardGames, \
    DifferentPiecesGames, DifferentRulesGames, SmallerGames, BiggerGames, \
    HandicapGames, ClassicGame, TestGames

HOST_NAME = '' # public!
PORT_NUMBER = 8090
STATIC_SERVE_BASE = "../jsclient"

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
               (DifferentPiecesGames, 'Different Pieces'),
               (DifferentBoardGames, 'Different Boards'),
               (HandicapGames, 'Handicap Games'),
               (TestGames, 'Test Games') # for debugging
               ])
for module in gameModules.keys():
    classes = inspect.getmembers(module, inspect.isclass(module))
    for name, obj in classes:
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
        
        

# server part
class MyHandler(http.server.BaseHTTPRequestHandler):
    def output(self, myString):
        self.wfile.write(bytes(repr(myString), 'UTF-8'))

    def output_raw(self, myString):
        if isinstance(myString, str):
            self.wfile.write(bytes(myString, 'UTF-8'))
    
    def sanitizeHTML(self, string):
        # TODO handle urlencoding here! possibly de- and reencode or filter 'bad' escape sequences? 
        return re.sub(r'(<[^>]*>)', '', string)
    
    def sendMQ(self, params):
        mq = mqPool.get(params[1])
        if mq is None:
            return json.dumps([])
        return json.dumps(mq.msgs)
    
    def distributeToAll(self, game, msg, filter_player=None):
        for player in game.players + game.watchers:
            if player != filter_player:
                player.mq.addMsg(msg)
        
            
    def serveStaticText(self, file):
        print("serving " + file + " statically from " + os.path.abspath(STATIC_SERVE_BASE + file))
        real_file = re.sub("\?.*", '', file)
        a_file = open(STATIC_SERVE_BASE + real_file, encoding='utf-8')
        a_string = a_file.read()

        self.send_response(200)
        #self.send_header("Content-type", "text/html")
        self.end_headers()

        self.output_raw(a_string)


    def serveStaticBinary(self, file):
        #print("serving binary " + file + " statically from " + os.path.abspath(STATIC_SERVE_BASE + file))
        self.send_response(200)
        #self.send_header("Content-type", "text/html")
        self.end_headers()

        try:
            real_file = file #re.sub("^/", '', file)
            fo = open(STATIC_SERVE_BASE + real_file, "rb")
            while True:
                buffer = fo.read(4096)
                if buffer:
                    self.wfile.write(buffer)
                else:
                    break
            fo.close()
        except IOError:
            print('Could not serve that file. Not found!')

    def createPlayer(self, game):
        player = Player()
        mq = player.mq
        mqPool.add(mq)            
        game.addPlayer(player)
        gamePool.add(game)
        # backlinks for the MQ
        mq.subject = player
        mq.game = game
        return mq

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
    
    def do_GET(self):
        """Respond to a GET request."""
        # examine string
        params = self.path.split("/")[1:]
        #print(self.path)
        #print(params)
        
        # -----------------------
        # serving static content?
        #------------------------
        if re.match('[^\.]+\.[html|js|css](\?\d*)?', self.path):
            self.serveStaticText(self.path)
            return
        if re.match('[^\.]+\.[ico|png|jpe?g|gif|ogg|mp3](\?\d*)?', self.path):
            self.serveStaticBinary(self.path)
            return
        
        # -----------------------
        # dynamic content
        # -----------------------
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        jsonoutput = {}
        if len(params) > 1:
            mq = mqPool.get(params[1])
            # can't answer if mq is unknown
            if mq is None and not(params[0] in {'new', 'join', 'watch', 'getgames', 'admin'}):
                return

        # check if there is an acknowledgement included starting at an arbitrary index
        for i in range(0, len(params)):
            if (params[i] == 'ack'):
                # search for the message
                found = False
                for j in range(0, len(mq.msgs)):
                    #print("comparing " + mq.msgs[i]['mid'] + " to " + params[2])
                    if mq.msgs[j]['mid'] == params[i + 1]:
                        #print("found acked msg. at pos " + str(i))
                        found = True;
                        break;
                # delete parsed ones
                if found:
                    mq.msgs = list(mq.msgs[j + 1:])
                
        
        # retrieve the MessageQueue (/getmq/191 ...)
        if (params[0] == 'getmq'):
            jsonoutput = self.sendMQ(params)
            
        elif (params[0] == 'post' and params[2] == 'move'):            
            # filter watchers attempting to post stuff
            if mq.watching or mq.game.finished == True:
                return
            # only allow current player to post his move
            if mq.game.getCurrentPlayer().mq != mq:
                msg = Message('alert', {'msg': 'Not your turn.'})
                mq.addMsg(msg)
                return
            
            game = mq.game
            
            # find board
            p3 = params[3].replace('board_', '').replace('_field', '_');
            p4 = params[4].replace('board_', '').replace('_field', '_');
            boardId = p3.split('_')[0]
            targetBoard = game.getBoard(boardId)
            
            # create move
            if  p3.split('_')[1] == 'SHORTCASTLING' or  p3.split('_')[1] == 'LONGCASTLING':
                # castling
                postedMove = Move(None, None)
                postedMove.annotation = p3.split('_')[1]
            else:
                # standard move
                fromField = int(p3.split('_')[1])
                toField = int(p4.split('_')[1])
                postedMove = Move(fromField, toField)
                # do we have a promotion option set?
                if len(params) > 5 and params[5] != 'ack':
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
                    msg = Message('promote', {'from': postedMove.fromField, 'to': postedMove.toField})
                    # add options
                    msg.data['options'] = game.getPromotionOptions(postedMove.fromPiece.color)
                    jsonoutput = json.dumps([msg.data])
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
                            move.simpleParse(mq.game.board)
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
                        self.distributeToAll(game, Message('move', data))
                        
                    self.distributeToAll(game, Message('movehist', {'user': mq.subject.name, 'str': postedMove.str}))
                    
                    # debug position
                    print(str(game.board))
                    
                    # distribute the game over message if there was one
                    if not(result is None):
                        self.distributeToAll(game, result)
                    
                    jsonoutput = self.sendMQ(params)
            else: 
                # not legal move
                msg = Message('alert', {'msg': 'Illegal move.'})
                jsonoutput = json.dumps([msg.data])
                
            
        # transfer chat message     
        elif (params[0] == 'post' and params[2] == 'chat'):            
            # filter watchers attempting to post stuff
            if mq.watching:
                return
            
            # sanitize
            msg = params[3]
            msg = self.sanitizeHTML(msg)
                        
            self.distributeToAll(mq.game, Message('chat', {'user': mq.subject.name, 'msg': msg}), filter_player=mq.subject)
                

        # starting a new game (e.g. /new/classic)
        elif (params[0] == 'new'):
            # find game
            input = urllib.parse.unquote(params[1])
            selectedGame = None
            print(input)
            for game in games:
                if game['title'] == input:
                    selectedGame = game 
            if selectedGame == None:
                jsonoutput = json.dumps([{'msg': 'No valid game: ' + input}])
            else:
                # create desired game
                game = selectedGame['class']()
                mq = self.createPlayer(game)
                # generate answer
                jsonoutput = json.dumps({'gameId': game.id, 'mqId': mq.id})
                # nicely say hello (next time)
                mq.addMsg(Message('srvmsg', {'msg': 'Welcome to the server!'}))
                mq.addMsg(Message('srvmsg', {'msg': 'We are playing ' + selectedGame['title'] + ', see ' + selectedGame['link']}))            


        elif (params[0] == 'getsit'):
            jsonoutput = json.dumps([mq.game.getSituationMessage(mq).data])
        
        elif (params[0] == 'join'):
            game = gamePool.games[params[1]]
            # check if more players are accepted for the game
            if (len(game.players) >= game.NUM_PLAYERS):
                jsonoutput = json.dumps({'msg': 'Sorry. Game is already full.'})
            
            mq = self.createPlayer(game)
            jsonoutput = json.dumps({'mqId': mq.id})
            self.distributeToAll(mq.game, Message('srvmsg', {'msg': 'Player joined.'}), mq.subject)

        elif (params[0] == 'watch'):
            game = gamePool.games[params[1]]
            if game.NO_WATCHERS:
                jsonoutput = json.dumps([Message('srvmsg', {'msg': 'No watchers allowed.'}).data])
            else:
                mq = self.createWatcher(game)
                jsonoutput = json.dumps({'mqId': mq.id})
                self.distributeToAll(mq.game, Message('srvmsg', {'msg': 'Watcher joined.'}), mq.subject)
         
        elif (params[0] == 'getgames'):
            jsonoutput = json.dumps(jsonGames)
        
        # admin panel functions
        # TODO check permissions (via some token output on server startup?)
        elif params[0] == 'admin':
            if params[1] == 'runtests':
                test = Test();
                jsonoutput = json.dumps({'log': test.runTestGames()})          
            
        else:
            jsonoutput = json.dumps([])
        #print(jsonoutput)
        self.output_raw(jsonoutput)
                       
        
if __name__ == '__main__':
    # prepare for the first games to be started 
    gamePool = GamePool();
    mqPool = MessageQueuePool();

    # start serving    
    httpd = http.server.HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
