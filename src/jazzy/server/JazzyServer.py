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
from MessageHandler import MessageQueuePool
from GamePool import GamePool
from jazzy.logic.DifferentBoardGames import *
from jazzy.logic.DifferentPiecesGames import *
from jazzy.logic.DifferentSetupGames import *
from jazzy.logic.DifferentRulesGames import *
from jazzy.logic.SmallerGames import *
from jazzy.logic.HandicapGames import *
from MessageHandler import Message
from jazzy.logic.MoveHistory import Move
from jazzy.logic.MoveHistory import MoveHistory
from Player import Player, Watcher
import json
import os
from jazzy.logic.DifferentRulesGames import MonochromaticGame
import gc

HOST_NAME = '' # public!
PORT_NUMBER = 8090
STATIC_SERVE_BASE = "../jsclient"

# enable garbage collection
gc.enable()

availible_games = {'Classic': {'class': ClassicGame, 'desc': 'Classic Chess'},
                   'Cylindric': {'class': CylindricGame, 'desc': 'Cylindric Chess'},
                   'Pawn': {'class': PawnGame, 'desc': 'Pawn Chess'},
                   'Los_Alamos': {'class': LosAlamosGame, 'desc': 'Los Alamos'},
                   'Micro': {'class': MicroGame, 'desc': 'Micro chess'},
                   'Legan': {'class': LeganGame, 'desc': 'Legan chess'},
                   'Berolina': {'class': BerolinaGame, 'desc': 'Berolina chess'},
                   'Extinction': {'class': ExtinctionGame, 'desc': 'Extinction chess'},
                   'Checkless': {'class': ChecklessGame, 'desc': 'Checkless chess'},
                   'Anti': {'class': AntiGame, 'desc': 'Antichess'},
                   'Atomic': {'class': AtomicGame, 'desc': 'Atomic chess'},
                   'Monochromatic': {'class': MonochromaticGame, 'desc': 'Monochromatic chess'},
                   'Bichromatic': {'class': BichromaticGame, 'desc': 'Bichromatic chess'},
                   'Handicap_Queen': {'class': HandicapQueenGame, 'desc': 'Handicap (White without Queen)'},
                   'Handicap_Rook': {'class': HandicapRookGame, 'desc': 'Handicap (White without rook a1)'},
                   'Handicap_Knight': {'class': HandicapKnightGame, 'desc': 'Handicap (White without knight b1)'},
                   'Handicap_PawnAndMove': {'class': HandicapPawnAndMoveGame, 'desc': 'Handicap (Black without pawn f7)'},
                   'Coin': {'class': CoinGame, 'desc': 'Coin Chess'}}
availible_games_json = {}
for key in availible_games.keys():
    availible_games_json[key] = availible_games[key]['desc']
    

class MyHandler(http.server.BaseHTTPRequestHandler):
    def output(self, myString):
        self.wfile.write(bytes(repr(myString), 'UTF-8'))

    def output_raw(self, myString):
        self.wfile.write(bytes(myString, 'UTF-8'))
    
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
        #print("serving " + file + " statically from " + os.path.abspath(STATIC_SERVE_BASE + file))
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
            if mq is None and not(params[0] in {'new', 'join', 'watch', 'getgames'}):
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
                
        
        # retrieve the MessageQueue (/getmq/191 
        if (params[0] == 'getmq'):
            jsonoutput = self.sendMQ(params)
            
        elif (params[0] == 'post' and params[2] == 'move'):            
            # filter watchers attempting to post stuff
            if mq.watching or mq.game.finished == True:
                return
            
            game = mq.game
            fromField = int(params[3])
            toField = int(params[4])
            postedMove = Move(fromField, toField)
            # check move for correctness
            isLegalMove = game.isLegalMove(postedMove)
            
            # put the message to all players
            if isLegalMove:
                postedMove.parse(mq.game.board)
                game.moveHistory.moves.append(postedMove)
                
                moves = game.move(postedMove, game.board)
                
                # analyze if game is over
                result = game.getGameOverMessage()
                if not(result is None):
                    game.finished = True

                # post all the move the particular game created
                for move in moves:
                    move.parse(mq.game.board)
                    data = {'from': move.fromField, 'to': move.toField}
                    if not(game.board.getCurrentPlayer() is None and not(game.finished)):
                        data['currP'] = game.board.getCurrentPlayer().mq.shortenedId
                    self.distributeToAll(game, Message('move', data))
                self.distributeToAll(game, Message('movehist', {'user': mq.subject.name, 'str': postedMove.str}))
                
                # distribute the game over message if there was one
                if not(result is None):
                    self.distributeToAll(game, result)
            # TODO check if the game is over
                
            jsonoutput = self.sendMQ(params)
            
        # transfer chat message     
        elif (params[0] == 'post' and params[2] == 'chat'):            
            # filter watchers attempting to post stuff
            if mq.watching:
                return
            
            self.distributeToAll(mq.game, Message('chat', {'user': mq.subject.name, 'msg': params[3]}), filter_player=mq.subject)
                

        # starting a new game (e.g. /new/classic)
        elif (params[0] == 'new'):
            gameClass = availible_games[params[1]]['class'] # create desired game
            game = gameClass()
            mq = self.createPlayer(game)
            # generate answer
            jsonoutput = json.dumps({'gameId': game.id, 'mqId': mq.id})
            # nicely say hello (next time)
            mq.addMsg(Message('srvmsg', {'msg': 'Welcome to the server!'}))
            mq.addMsg(Message('srvmsg', {'msg': 'We are playing ' + availible_games[params[1]]['desc']}))            

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
            mq = self.createWatcher(game)
            jsonoutput = json.dumps({'mqId': mq.id})
            self.distributeToAll(mq.game, Message('srvmsg', {'msg': 'Watcher joined.'}), mq.subject)
         
        elif (params[0] == 'getgames'):
            jsonoutput = json.dumps(availible_games_json)
            
        else:
            jsonoutput = json.dumps({})
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
