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
from jazzy.logic import DifferentSetupGames, DifferentPlayerGames, DifferentBoardGames, \
    DifferentPiecesGames, DifferentRulesGames, SmallerGames, BiggerGames, \
    HandicapGames, ClassicGame, TestGames
import logging

logger = logging.getLogger('jazzyLog')
handler = logging.StreamHandler(sys.stdout) 
frm = logging.Formatter('%(levelname)s: %(message)s') 
handler.setFormatter(frm)
logger.addHandler(handler) 
logger.setLevel(logging.ERROR)


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
        
        

# server part
class JazzyHandler(http.server.BaseHTTPRequestHandler):
    def output(self, myString):
        self.wfile.write(bytes(repr(myString), 'UTF-8'))

    def output_raw(self, myString):
        if isinstance(myString, str):
            self.wfile.write(bytes(myString, 'UTF-8'))
    
    def sanitizeHTML(self, string):
        # TODO handle urlencoding here! possibly de- and reencode or filter 'bad' escape sequences? 
        result = re.sub(r'(<[^>]*>)', '', string)
        result = result.replace('%3C', '')
        result = result.replace('%3E', '')
        return result
        
    def sendMQ(self, params):
        mq = mqPool.get(params[1])
        if mq is None:
            return json.dumps([])
        return json.dumps(mq.msgs)
    
    def distributeToAll(self, game, msg, filterPlayers=[]):
        for player in game.getAllPlayers() + game.getAllWatchers():
            if not (player in filterPlayers):
                player.mq.addMsg(msg)
        
            
    def serveStaticText(self, file):
        print("serving " + file + " statically as text from " + os.path.abspath(STATIC_SERVE_BASE + file))
        real_file = re.sub("\?.*", '', file)
        try:
            a_file = open(STATIC_SERVE_BASE + real_file, encoding='utf-8')
            a_string = a_file.read()
    
            self.send_response(200)
            #self.send_header("Content-type", "text/html")
            self.end_headers()
    
            self.output_raw(a_string)
        except IOError:
            print('Could not serve that file. Not found!')

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
        if not(re.match('.+\.[ico|png|jpg|gif|ogg|mp3](\?[0-9a-fA-F]*)?', self.path) is None):
            self.serveStaticBinary(self.path)
            return
        if not(re.match('.+\.[html|js|css](\?[0-9a-fA-F]*)?', self.path) is None):
            self.serveStaticText(self.path)
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
            # can't answer if mq is not transferred (e.g. because it is yet unknown)
            if mq is None and not(params[0] in {'new', 'join', 'watch', 'getgames', 'getslots', 'admin'}):
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
            originalFrom = params[3]
            originalTo = params[4]
            shortFrom = originalFrom.replace('board_', '').replace('_field', '_');
            shortTo = originalTo.replace('board_', '').replace('_field', '_');
            boardId = shortFrom.split('_')[0]
            targetBoard = game.getBoard(boardId)
            
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
                    msg = Message('promote', {'from': originalFrom, 'to': originalTo})
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
                        self.distributeToAll(game, Message('move', data))
                        
                    self.distributeToAll(game, Message('movehist', {'user': mq.subject.name, 'str': postedMove.str}))
                    
                    # debug position
                    print(str(game.board))
                    
                    # resend parts of the board that have changed (not forced)
                    for player in mq.game.players:
                        sitMsg = mq.game.getSituationMessage(mq, player=player)
                        if not(sitMsg is None):
                            player.mq.addMsg(sitMsg)
                    # clear board
                    mq.game.board.resend = False # TODO generalize
                    
                    # distribute the game over message if there was one
                    if not(result is None):
                        self.distributeToAll(game, result)
                    
                    jsonoutput = self.sendMQ(params)
            else: 
                # not legal move
                msg = Message('alert', {'msg': 'Illegal move.'})
                mq.addMsg(msg)
                if game.DEBUG_LEGAL_MOVES_ON_ILLEGAL_MOVE:
                    msg = Message('srvmsg', {'msg': 'Possible moves are: ' + str(sorted(mq.game.possibleMoves, key=lambda move: [str(move.fromField), move.toField]))})
                    mq.addMsg(msg)
                jsonoutput = self.sendMQ(params)
        
        # draw claims
        elif params[0] == 'claim':
            # filter watchers attempting to post stuff
            if mq.watching:
                return
                
            if params[2] == 'repetition':                    
                if mq.game.isRepetitionDraw():
                    self.distributeToAll(mq.game, mq.game._generateGameOverMessage('Draw by repetition upon player\'s request', '0.5-0.5', None))
                else:
                    mq.addMsg(Message('alert', {'msg': 'No draw by repetition. This position has been on board {0} times.'.format(mq.game.getRepetitionCount())})) 
                    
            if params[2] == 'xmoverule':
                if mq.game.isXMoveDraw():
                    self.distributeToAll(mq.game, mq.game._generateGameOverMessage('Draw by {0} move rule upon player\'s request'.format(mq.game.DRAW_X_MOVES_VALUE), '0.5-0.5'))
                else:
                    mq.addMsg(Message('alert', {'msg': 'No draw by {0} move rule. Counter is at {1}.'.format(mq.game.DRAW_X_MOVES_VALUE, mq.game.board.drawXMoveCounter)}))
            
            jsonoutput = self.sendMQ(params)
        
        # messages about game end (resigning, draws) 
        elif (params[0] == 'end'):
            # only players please!
            if isinstance(mq.subject, Player):
                # player resigned
                if (params[2] == 'resign'):
                    result = '0-1' if mq.subject.color == 'white' else '1-0' 
                    winner = mq.game.getNextCurrentPlayer() if mq.game.getCurrentPlayer() == mq.subject else mq.game.getCurrentPlayer()
                    self.distributeToAll(mq.game, mq.game._generateGameOverMessage('Player resigned.', result, winner))
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
                            self.distributeToAll(mq.game, mq.game._generateGameOverMessage('Players agreed.', '0.5-0.5', None))
                        else:
                            # ask the other players
                            self.distributeToAll(mq.game, Message('draw-offer', {}), agreeingPlayers)
                    
            
        # transfer chat message     
        elif (params[0] == 'post' and params[2] == 'chat'):            
            # filter watchers attempting to post stuff
            if mq.watching:
                return
            
            # sanitize
            msg = params[3]
            msg = self.sanitizeHTML(msg)
                        
            self.distributeToAll(mq.game, Message('chat', {'user': mq.subject.name, 'msg': msg}), [mq.subject])
            jsonoutput = self.sendMQ(params)

        # starting a new game (e.g. /new/classic)
        elif (params[0] == 'new'):
            # find game
            input = urllib.parse.unquote(params[1])
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
                # nicely say hello (next time)
                self.distributeToAll(game, Message('srvmsg', {'msg': 'Welcome to the server!'}))
                self.distributeToAll(game, Message('srvmsg', {'msg': 'We are playing ' + selectedGame['title'] + ', see ' + selectedGame['link']}))
                #except Exception:
                #    jsonoutput = json.dumps({'msg': 'Invalid game name.'})
                    
        elif (params[0] == 'getsit'):
            jsonoutput = json.dumps([mq.game.getSituationMessage(mq, force=True).data])

        elif (params[0] == 'getslots'):     
            try:    
                game = gamePool.games[params[1]]
            except KeyError:
                return
            jsonoutput = json.dumps(game.getSlotsMessageData())
            
        elif (params[0] == 'join'): 
            # message format: /join/[gameId]/[shortened mqId]
            # find the player targeted
            try:    
                game = gamePool.games[params[1]]
                targetPlayer = None
                for player in game.players:
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
                    jsonoutput = json.dumps({'link': 'play.html?' + player.mq.id})
                    self.distributeToAll(game, Message('srvmsg', {'msg': 'Player joined.'}))
                    # taken slot now
                    targetPlayer.dummy = False
                    

        elif (params[0] == 'watch'):
            game = gamePool.games[params[1]]
            if game.NO_WATCHERS:
                jsonoutput = json.dumps([Message('srvmsg', {'msg': 'No watchers allowed.'}).data])
            else:
                mq = self.createWatcher(game)
                jsonoutput = json.dumps({'mqId': mq.id})
                self.distributeToAll(mq.game, Message('srvmsg', {'msg': 'Watcher joined.'}), [mq.subject])
         
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
    gamePool = GamePool()
    mqPool = MessageQueuePool()

    # start serving    
    httpd = http.server.HTTPServer((HOST_NAME, PORT_NUMBER), JazzyHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
