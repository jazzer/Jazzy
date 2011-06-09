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
from jazzy.logic.HandycapGames import *
from MessageHandler import Message
from jazzy.logic.MoveHistory import Move
from jazzy.logic.MoveHistory import MoveHistory
from Player import Player
import json
import os

HOST_NAME = '' # public!
PORT_NUMBER = 8090
STATIC_SERVE_BASE = "../jsclient"

availible_games = {'Classic': {'class': ClassicGame, 'desc': 'Classic Chess'},
                   'Cylindric': {'class': CylindricGame, 'desc': 'Cylindric Chess'},
                   'Pawn': {'class': PawnGame, 'desc': 'Pawn Chess'},
                   'Los_Alamos': {'class': LosAlamosGame, 'desc': 'Los Alamos'},
                   'Handycap_Queen': {'class': HandycapQueenGame, 'desc': 'Handcap (White without Queen)'},
                   'Handycap_Rook': {'class': HandycapRookGame, 'desc': 'Handcap (White without rook a1)'},
                   'Handycap_Knight': {'class': HandycapKnightGame, 'desc': 'Handcap (White without knight b1)'},
                   'Handycap_PawnAndMove': {'class': HandycapPawnAndMoveGame, 'desc': 'Handcap (Black without pawn f7)'},
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
        for player in game.players:
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
        print("serving binary " + file + " statically from " + os.path.abspath(STATIC_SERVE_BASE + file))
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
        mq.player = player
        mq.game = game
        return mq
    
    def do_GET(self):
        """Respond to a GET request."""
        # examine string
        params = self.path.split("/")[1:]
        print(self.path)
        print(params)
        if len(params) > 1:
            mq = mqPool.get(params[1])
        
        jsonoutput = {}
        
        # serving static content?
        #if re.match('[a-zA-Z0-9_-]+\.[html|js|css|ico](\?\d*)?', params[0]):
        if re.match('[^\.]+\.[html|js|css](\?\d*)?', self.path):
            self.serveStaticText(self.path)
            return
        if re.match('[^\.]+\.[ico|png|jpe?g|gif](\?\d*)?', self.path):
            self.serveStaticBinary(self.path)
            return

        # dynamic content!
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        
        # retrieve the MessageQueue (/getmq/191 
        if (params[0] == 'getmq'):
            jsonoutput = self.sendMQ(params)

        # acknowledge reception of messages from the queue
        elif (params[0] == 'ackmq'):
            # search for the message
            found = False
            for i in range(0, len(mq.msgs)):
                #print("comparing " + mq.msgs[i]['mid'] + " to " + params[2])
                if mq.msgs[i]['mid'] == params[2]:
                    #print("found acked msg. at pos " + str(i))
                    found = True;
                    break;
            # delete parsed ones
            if found:
                mq.msgs = mq.msgs[i + 1:]
            
            # send the current MQ (now without acked stuff) to use bandwidth efficiently
            jsonoutput = self.sendMQ(params)
            
        elif (params[0] == "post" and params[2] == "move"):            
            game = mq.game
            fromField = int(params[3])
            toField = int(params[4])
            postedMove = Move(fromField, toField)
            # check move for correctness
            isLegalMove = game.isLegalMove(postedMove, mq.player)
            # TEMP TODO
            game.parsePossibleMoves(game.getCurrentPlayer())
            
            # put the message to all players
            if isLegalMove:
                postedMove.parse(mq.game.board)
                game.moveHistory.moves.append(postedMove)
                moves = game.move(postedMove)
                for move in moves:
                    move.parse(mq.game.board)
                    data = {'from': move.fromField, 'to': move.toField}
                    if not(game.getCurrentPlayer() is None):
                        data['currP'] = game.getCurrentPlayer().mq.shortenedId
                    self.distributeToAll(game, Message('move', data))
                    self.distributeToAll(game, Message('movehist', {'user': mq.player.name, 'str': move.str}))
            
            # TODO check if the game is over
                
            jsonoutput = self.sendMQ(params)
            
        # transfer chat message     
        elif (params[0] == "post" and params[2] == "chat"):            
            self.distributeToAll(mq.game, Message('chat', {'user': mq.player.name, 'msg': params[3]}), filter_player=mq.player)
                

        # starting a new game (e.g. /new/classic)
        elif (params[0] == "new"):
            gameClass = availible_games[params[1]]['class'] # create desired game
            game = gameClass()
            mq = self.createPlayer(game)
            # generate answer
            jsonoutput = json.dumps({'gameId': game.id, 'mqId': mq.id})
            # nicely say hello (next time)
            mq.addMsg(Message("srvmsg", {'msg': 'Welcome to the server!'}))
            mq.addMsg(Message("srvmsg", {'msg': 'We are playing ' + availible_games[params[1]]['desc']}))            

        elif (params[0] == "getsit"):
            jsonoutput = json.dumps([mq.game.getSituationMessage(mq).data])
        
        elif (params[0] == "join"):
            game = gamePool.games[params[1]]
            mq = self.createPlayer(game)
            jsonoutput = json.dumps({'mqId': mq.id})
            self.distributeToAll(mq.game, Message('srvmsg', {'msg': 'Player joined.'}), mq.player)
         
        elif (params[0] == 'getgames'):
            jsonoutput = json.dumps(availible_games_json)
            
        else:
            jsonoutput = json.dumps({})
        print(jsonoutput)
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
