/*!
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
*/



/* server settings */
var server_url = window.location.protocol + "//" + window.location.host + "/";
var myTurn = true;
var styleNames = 'light-wood,dark-wood,gray';
var boardStyleNames = 'classic,color';
var globalTurn = false;

if (typeof BoardStorage === 'function') {
	var boardStorage = new BoardStorage();
}


/* global variables

	DO NOT CHANGE ANYTHING BELOW HERE 
	UNLESS YOU KNOW WHAT YOU DO! */
var debugLevel = 1;
var gameId = undefined;
var mqId, availible_games, currSelectedGame, playerName
var activeJSONCall = false;
var styleNameArray = styleNames.split(",");
var boardStyleNameArray = boardStyleNames.split(",");
var selfPlayerIDs = '';
var currPlayer = new Object();
var myTurn = new Object();
var sock, game, ping;


function _debug(msg, level) {
	if (debugLevel >= level) {
		addServerMessage(msg);
	}
}


function _playInit() {
	// wait for jQuery and the DOM to be ready
	$(document).ready(function() {
		// which MessageQueue are we operating on? (essentially the player's ID)
		mqId = window.location.href.match(/[\dA-Fa-f]+$/);

		// show debug level in UI
		$('[name="debugLevel"]').attr('value', debugLevel);		

        // setup the SocketIO connection (preferrably WebSocket based)
        sock = new io.connect(server_url);
        game = new io.connect(server_url + 'game');
        ping = new io.connect(server_url + 'ping');

        // Establish event handlers
        sock.on('disconnect', function() {
            sock.socket.reconnect();
        });

        game.on('message', function(data) {
            console.info("got message: " + data);
            parseMQ(data);
        });

		// request current situation (enables returning after problems)
		game.send("getsit/" + mqId);
		// tell about your success
		addServerMessage("Finished setting up game.");
		
		// set button
		$("#btnDisconnect").toggle(
			function() {
				$(this).html('Connect');
                // TODO something like sock.disconnect();
			},function() {
				$(this).html('Disconnect');
                // TODO something like sock.reconnect();
			});

		// setup style chooser
		var targets = $('[name="style-chooser-main"]');
		for (styleIndex in styleNameArray) {
			targets.append($('<option>').text(styleNameArray[styleIndex]));
		}
        targets = $('[name="style-chooser-board"]');
		for (styleIndex in boardStyleNameArray) {
			targets.append($('<option>').text(boardStyleNameArray[styleIndex]));
		}
		$('select[name="style-chooser-main"]').change(function() {_changeStyle('main');});
		$('select[name="style-chooser-board"]').change(function() {_changeStyle('board');});
	});	
}

function _dataInit() {
	$(document).ready(function() {
		// hide all
		$('div[class^="data_content"]').children().remove().end().hide();
		// setup events
		$('div[id^="data__"]').toggle(function() {
			id = $(this).attr('id').replace(/^data__/, '');
			long_data = getLongData(id);
			// remove short
			$(this).find('[class^="inline_content"]').html('');
			// set long and show it
			$(this).find('[class^="data_content"]').html(long_data).toggleClass('data_content_empty').toggleClass('data_content').slideDown(500);
		}, function() {
			id = $(this).attr('id').replace(/^data__/, '');
			short_data = getShortData(id);	
			// set short
			$(this).find('[class^="inline_content"]').html(short_data);
			// hide long
			$(this).find('[class^="data_content"]').slideUp(500, function() { $(this).toggleClass('data_content_empty').toggleClass('data_content'); });
		}).click().click();
	});
}


function _changeStyle(type, value) {
	var target;
	if (type == 'main') {
		target = $('[name^="style-chooser-main"]');
	} else {
		target = $('[name^="style-chooser-board"]')
	}
	// unload old and reload new css file
	if (value != undefined) {
		newStyleFile = target.val(value);
	}
	value = target.val();
	var newStyleFile = 'css/' + target.val() + '-' + type + '.css';

	// already loaded?
	if ($('link[href="css/' + newStyleFile + '"]').size() > 0) return;

	// actually change the css file parsed
	for (styleIndex in styleNameArray) {
		// remove
		$('link[href="css/' + styleNameArray[styleIndex] + '-' + type + '.css"]').remove();
	}
	// set new style
	$('head').append($('<link>').attr({'type': 'text/css', 'rel': 'stylesheet', 'href': newStyleFile}));
	
	// repaint boards if style changed
    var boards = $('.board');
    boards.each(function() {
        var boardId = $(this).attr('id').replace(/^board_/, '');
        var thisBoard = boardStorage.getBoard(boardId);

        thisBoard.pullStyles();
        window.setTimeout(function() {
            thisBoard.repaintFull();
        }, 300);
    });
}


function getLongData(type) {
	return "THESE ARE THE LONG DATA FOR " + type;
}

function getShortData(type) {
	return "short data for " + type;
}

function watchGame() {
	joinOrWatchGame('watch');
}

function joinGame() {
	joinOrWatchGame('join');
}

function joinOrWatchGame(messageType) {
	$(function() {
		gameId = window.location.href.match(/[\dA-Fa-f]+$/);
		serverCall(messageType + "/" + gameId, function(data) {
			mqId = data['mqId'];
			if (mqId != undefined) {
				location.href = server_url + 'play.html?' + mqId;
			} else {
				$('#messages').append($('<span>').addClass('message').html(data['msg']));
			}		
		}, false, true);	
	});
}

function load_availible_games() {
	$(function() {
		serverCall("getgames", function(data) {
			// save data
			availible_games = data;
			// build category list
			buildCategories();
		}, false, true);		
	});
}



function buildCategories() {
	if (availible_games == undefined) {
		return;
	}
	target = $('#gameSelection_step1');
	target.empty();
	// find categories
	categories = new Object();
	for (gameId in availible_games) {
		game = availible_games[gameId];
		categories[game['cat']] = 1; // using it as a set basically
	}
	
	// add them
	for (cat in categories) {
		entry = $('<div>').addClass('entry').html(cat);
		entry.click(function() {showGames($(this).html());}); // TODO setup function
		target.append(entry);
	}
}

// show games of selected category
function showGames(cat) {
	target = $('#gameSelection_step2');
	target.empty();
	
	// loop games
	for (gameId in availible_games) {
		game = availible_games[gameId];
		if (game['cat'] == cat) {
			entry = $('<div>').addClass('entry').html(game['title']);
			entry.click(function() {showDetails($(this).html());}); // TODO setup function
			target.append(entry);
		}
	}
}

// show game details
function showDetails(game) {
	target = $('#gameSelection_step3');
	target.empty();
	
	// loop games
	for (gameId in availible_games) {
		loopGame = availible_games[gameId];
		if (game == loopGame['title']) {
			target.html(loopGame['title']+'<br/>'+loopGame['desc']+'<br/>'+loopGame['details']+'<br/><a href="'+loopGame['link']+'">More...</a>');
			break;
		}
	}

	currSelectedGame = game;
}




function postMove(from, to, promotion) {
	// post move to server and wait for message queue containing it (means move was okay)!
	var url = 'post/' + mqId + '/move/' + shortenFieldString(from) + '/' + shortenFieldString(to);
	if (promotion != undefined) {
		url += '/' + promotion
	}
	game.send(url);
}

function _shortCastling(boardId) {
	postMove(boardId + "_SHORTCASTLING", "")
}
function _longCastling(boardId) {
	postMove(boardId + "_LONGCASTLING", "")
}




function addServerMessage(msg) {
	// sanitize?
	var messageDiv = $("<span>").addClass("message").html(_getTime(false) + msg + "<br/>");
	$("#messages").append(messageDiv).scrollTop(100000000);
}

function addChatMessage(user, msg) {
	// sanitize?
	var messageDiv = $("<span>");
	if (user == "_") {
		messageDiv.addClass("chat_self");
		messageDiv.html(_getTime() + msg + "<br/>");
	} else {
		messageDiv.addClass("chat_other");
		messageDiv.html(_getTime() + '<span class="chat_username">' + user + '</span>' + msg + "<br/>");
	}
	$("#chat_history").append(messageDiv).scrollTop(100000000);
}

function sendChat() {
	var msg = $('input[name="chatmsg"]').attr('value');
	if (msg === '') return; 
	$('input[name="chatmsg"]').attr('value', '');
	addChatMessage("_", msg);
	// send the message to the server for distribution
	game.send('post/' + mqId + '/chat/' + encodeURIComponent(msg));
}

function _getTime(doShort) {
	// default doShort to "true"
	if (arguments.length == 0) {
		doShort = true;
	}

	var result = '<span class="time">';
	var now = new Date();
	if (now.getHours() < 10) { result = result + '0'; }
	result = result + now.getHours() + ':';
	if (now.getMinutes() < 10) { result = result + '0'; }
	result = result + now.getMinutes();
	if (!doShort) {
		result = result + ':';
		if (now.getSeconds() < 10) { result = result + '0'; }
		result = result + now.getSeconds();
	}
	return result + "</span>";
}




function createGame() {
	if (currSelectedGame == undefined) { return; }
	serverCall('new/' + currSelectedGame, function(data) { follow(data); }, true, true);
}


function serverCall(relUrl, successFunc, asnycValue, preventCaching) {
	var callUrl = relUrl;
	if (preventCaching) {
		callUrl = callUrl + "/" + new Date().getTime();
	}
	$.ajax({
		url: server_url + callUrl,
		async: asnycValue,
		dataType: 'json',
		success: function(input) {
			successFunc(input);
		}
	});
}

function _repetition() {
	// claim threefold repetition
	game.send("claim/" + mqId + "/repetition");
}
function _xMoveRule() {
	// claim threefold repetition
	game.send("claim/" + mqId + "/xmoverule");
}


function updateOverview() {
	$(document).ready(function() {
		window.setInterval("showSlots()", 5000);
		showSlots();
	});
}

function showSlots()  {
	gameId = window.location.href.match(/[\dA-Fa-f]+$/);
	serverCall('getslots/' + gameId, function(data) {
		var target = $('#slots').empty();
		for (var i=0;i<data.length;i++) {
			var slotDiv = $('<div>').addClass('slot-box');
			if (data[i]['open'] === true) {
				slotContent = '<div class="slot-desc">{0}</div><div class="slot-pname">{1}</div>'.format(data[i]['desc'], data[i]['pname']);
				slotDiv.addClass('slot-open');
				// add joining event
				slotDiv.data('joinId', data[i]['joinId']);
				slotDiv.click(function(joinId) {
					serverCall('join/' + gameId + '/' + $(this).data('joinId') + '/' + getPlayerName(), function(data) { follow(data);}, true, true);
				});
			} else {
				slotContent = '<div class="slot-desc">{0}</div><div class="slot-pname"></div>'.format(data[i]['desc']);
				slotDiv.addClass('slot-taken');
			}
			// put to DOM
			target.append(slotDiv.html(slotContent));
		}
	}, true, true);
}


function follow(data) {
	if (data['msg'] !== undefined) {
		$.prompt(data['msg']);
	} else {
		// follow the link sent by the server
		window.location = data['link'];
	}
}


function _parseCurrPlayer(currPlayerValue, boardId) {
	if (currPlayerValue == undefined) {
		return;
	}

	currPlayer[boardId] = currPlayerValue;
	myTurn[boardId] = selfPlayerIDs.indexOf(currPlayerValue) != -1;

	// lock board if not my turn 
	// (prevents some nasty bugs when sending moves 
	// before receiving the last one of your opponent)
	if (myTurn[boardId]) {
		boardStorage.getBoard(boardId).unlock();
	} else {
		boardStorage.getBoard(boardId).lock();
	}

	// set styles
	// clear board
	$('[id^="' + boardId + '_p"]').removeClass('player-curr');
	// set new
	$('[id$="_p' + currPlayerValue +'"]').addClass('player-curr');

	// nowhere current player?
	var globalTurn = false;
	for (thisBoardTurn in myTurn) {
		if (myTurn[thisBoardTurn]) {
			globalTurn = true;
			break;
		}
	}
	// set favicon accordingly
	if (globalTurn) {
		_setFavicon('red');		
	} else {
		_setFavicon('green');		
	}
}

function _setFavicon(name) {
    // update
    result = $('link[rel="icon"]').remove();
    result.attr('href', 'img/favicon/' + name + '.gif');
    $('head').append(result);
}

function _changeDebugLevel() {
	$(function() {
		debugLevel = $('[name="debugLevel"]').attr('value');
	});
}

function makeWatching() {
	isWatching = true;
	// remove events (have already been set)
	$("div[id^='field']").unbind();
}


function shortenFieldString(fString) {
	if (fString === undefined) { return undefined; }
	return fString.replace(/^board_/, "").replace(/_field/, "_");
}
function lengthenFieldString(fString) {
	if (fString === undefined) { return undefined; }
	return fString.replace(/_/, "_field").replace(/^/, "board_");
}

// handle click to "resign" button in UI
// send corresponding message to the server
function _resign() {
	var confirmed = $.prompt("Do you really want to resign?", { buttons: { Yes: true, No: false }, focus: 1 });
	if (confirmed) {
		game.send("end/" + mqId + "/resign");
	}
}

// handle click to "offer draw" button in UI
// send corresponding message to the server
function _offerDraw() {
	if (myTurn) {
		$.prompt("You can only offer draw on your opponent's turn.");
		return;
	}
	var confirmed = confirm("Do you really want to offer a draw?", { buttons: { Yes: true, No: false }, focus: 1 });
	if (confirmed) {
		game.send("end/" + mqId + "/draw-offer");
	}
}

function _fillPocket(position, content, board) {
    // TODO reenable
	//var pocketId = position=='top'?'1':'0';
	//var position = (position=='top' && !board.flipped) || (position=='bottom' && board.flipped)?'top':'bottom';
	//var pocket = $('#' + position + '-pocket-board_' + board.id).empty();
	//for (var i=0; i<content.length; i++) {
	//	var pieceDiv = board.getPieceDiv(content.charAt(i));
	//	var fieldDiv = $('<div>').addClass('field').attr('id', 'board_' + board.id + '_fieldp' + pocketId + i).append(pieceDiv);
	//   add click events
	//  _addEvents(fieldDiv, board);
	//	pocket.append(fieldDiv);
	//}
}

function _parseBoardPlayers(players, targetBoard) {
	// format players: name:id,name:id/name:id,name:id
	var playerArray = players.toString().split(/[,/]/);
	var myBoard = false;
	for (i in playerArray) {
		var playerID = playerArray[i].split(':')[1];
		if (selfPlayerIDs.search(playerID) !== -1) {
			myBoard = true;
			break;
		}
	}
	// set style
	var board = $('#board_' + targetBoard.id + '-frame');
	board.removeClass('board-mine').removeClass('board-notmine');
	if (myBoard) {
		board.addClass('board-mine');
		$('#board_' + targetBoard.id + '-controls').show();
	} else {
		board.addClass('board-notmine');
		$('#board_' + targetBoard.id + '-controls').hide();
		targetBoard.lock();
	}
}

function _fillPlayers(position, content, board) {
	var position = (position=='top' && !board.flipped) || (position=='bottom' && board.flipped)?'top':'bottom';
	var playerHostDiv = $('#' + position + '-players-' + board.id).empty();
	var playerSplit = content.split(',');
	for (var i=0; i<playerSplit.length; i++) {
		var playerData = playerSplit[i].split(':');
		var playerDiv = $('<div>').addClass('btn player').attr('id', board.id + '_p' + playerData[1]).html(playerData[0]).attr('title', playerData[1]); // [0] = name, [1] = ID
		// add click events
		playerHostDiv.append(playerDiv);
		// highlight if it's yourself
		if (selfPlayerIDs.search(playerData[1]) !== -1) {
			playerDiv.addClass('player-me');
		}
	}
}


function parseMQ(data) {
    if (data === undefined || data === null) {return;}

	if (data.length > 0) {
		_debug("Received message queue: " + JSON.stringify(data, null, '\t'), 2);
	}
	
	for (var i=0;i<data.length;i++) {
		mtype = data[i]['mtype'];
		switch (mtype) {
			case "move":
				silent = data[i]['silent'] == true?true:false;
				boardId = data[i]['from'].replace(/_.*/, '');
				board = boardStorage.getBoard(boardId);
				board.move(lengthenFieldString(data[i]['from']), lengthenFieldString(data[i]['to']), data[i]['toPiece'], silent); 
				_parseCurrPlayer(data[i]['currP'], boardId);
				// TODO add ['check'] in server and client -> play sound (don't set when game is finished)
				break;
			case "movehist":
				addServerMessage(data[i]['user'] + " played <b>" + data[i]['str'] + "</b>"); 
				break;
			case "promote":
				boardId = data[i]['from'].replace(/_.*/, '');
				// get options, offer, get decision and resend move
				var selectionDiv = $('<div>').html('Select which piece to promote to:<br/><br/>');
                var counter = 0;
				for (elem in data[i]['options']) {
					piece = data[i]['options'][elem];					
					board = boardStorage.getBoard(boardId);
					pieceDiv = board.getPieceDiv(piece).addClass('promotion_piece');
					// add events
					pieceDiv.bind("click", { Param1: data[i]['from'], Param2: data[i]['to'], Param3: piece }, function(event){
						postMove(event.data.Param1, event.data.Param2, event.data.Param3);
						// remove dialog
						$.modal.close();
					});
                    counter++;
					// add to parent div
					selectionDiv.append(pieceDiv);
				}
                // call modally
				selectionDiv.css('minimum-height', board.pieceImg.width*counter).modal();				
				break;
			case "chat":
				addChatMessage(data[i]['user'], decodeURIComponent(data[i]['msg']));
				playSound('media/chat-message');
				break;
			case "gameover":
				goMsg = "Game finished.\nResult: " + data[i]['result'] + "\n" + data[i]['msg'];
				addServerMessage(goMsg);
				setTimeout(function () { $.prompt(goMsg); }, 1000);
				// TODO play sound 
				break;
			case "gamesit":
				var j = -1;
				// save own IDs
				if (data[i]['playerSelf'] !== undefined) {
					selfPlayerIDs = data[i]['playerSelf'];
				}
				while (true) {
					j++
					// build the board
					try {
						var test = data[i][j]['board_id'];
					} catch (e) {
						break;
					}
					var boardId = data[i][j]['board_id'];		
					if (data[i][j]['board_size'] !== undefined) {
						boardSize = data[i][j]['board_size'].split('x');
						board = boardStorage.newBoard(boardId, boardSize[0], boardSize[1], data[i][j]['flipped']);	
						// load the position
						board.loadFen(data[i][j]['fen']);
						// fix highlight
						board.highlightClear();
						if (data[i][j]['lmove_from'] !== undefined && data[i][j]['lmove_to'] != undefined) {
							board.highlight(lengthenFieldString(data[i][j]['lmove_from']), highlightType.LAST_MOVE);
							board.highlight(lengthenFieldString(data[i][j]['lmove_to']), highlightType.LAST_MOVE);
						}
					}
					if (data[i][j]['players'] !== undefined) {
						var players = data[i][j]['players'].split('/');						
						var targetBoard = boardStorage.getBoard(boardId);
						_parseBoardPlayers(players, targetBoard);
						_fillPlayers('top', players[1], targetBoard);
						_fillPlayers('bottom', players[0], targetBoard);
					}
					if (data[i][j]['pockets'] !== undefined) {
						pockets = data[i][j]['pockets'].split(',');
						var targetBoard = boardStorage.getBoard(boardId);
						_fillPocket('top', pockets[1], targetBoard);
						_fillPocket('bottom', pockets[0], targetBoard);
					}
					if (data[i][j]['capturePockets'] !== undefined) {
						// TODO implement filling (#27 on GitHub)
					}
					if (data[i][j]['currP'] !== undefined) {
						// check if it's my turn
						_parseCurrPlayer(data[i][j]['currP'], boardId);
					}
				}
				if (data[i]['gameId'] !== undefined) {
					// add the appropriate link to the game's overview page
					$('#menu_game').children('a').attr('href', 'game.html?' + data[i]['gameId']);
				}
				break;
			case "srvmsg":
				addServerMessage(data[i]['msg']);
				break;
			case "setname":
				$('[id$="_p' + data[i]['id'] + '"]').html(data[i]['name']);
				break;
			case "draw-offer":
				var confirmed = confirm("Your opponent is offering a draw. Do you accept?", { buttons: { Yes: true, No: false }, focus: 1 });
				if (confirmed) {
					game.send("end/" + mqId + "/draw-offer");
				}
				break;
			case "alert":
				$.prompt(data[i]['msg']);
				break; 
			}		

		lastParsedMsg = data[i]['mid'];
		_debug("parsed message with id " + lastParsedMsg, 4);
	}	
}


function getPlayerName() {
	if (playerName !== undefined) {
		return playerName;
	}
	// search for saved old name
	try {
		var support = 'localStorage' in window && window['localStorage'] !== null;
	} catch (e) {
		// no support for local storage
		_askName();
		return undefined;
	}
	var oldName = window.localStorage.getItem('jazzy-player-name');
	if (oldName === null) {
		_askName();
		return undefined;
	}
	return oldName;
}

function _askName() {
	var txt = 'Please enter your name:<br /><input type="text" id="alertName" name="alertName" value="John Doe" />';
	$.prompt(txt, {
		callback: _lS_nameCallback,
		buttons: { Ok: true }
	});
}

function _lS_nameCallback(v,m,f){
	an = m.children('#alertName');

	if(f.alertName == ""){
		an.css("border","solid #ff0000 1px");
		return false;
	}
	playerName = f.alertName; // save globally
	window.localStorage.setItem('jazzy-player-name', playerName);
	return true;
}



// convience methods

function isArray(obj){return(typeof(obj.length)=="undefined")?false:true;}

// Inspired by http://bit.ly/juSAWl
// Augment String.prototype to allow for easier formatting.  This implementation 
// doesn't completely destroy any existing String.prototype.format functions,
// and will stringify objects/arrays.
String.prototype.format = function(i, safe, arg) {

  function format() {
    var str = this, len = arguments.length+1;

    // For each {0} {1} {n...} replace with the argument in that position.  If 
    // the argument is an object or an array it will be stringified to JSON.
    for (i=0; i < len; arg = arguments[i++]) {
      safe = typeof arg === 'object' ? JSON.stringify(arg) : arg;
      str = str.replace(RegExp('\\{'+(i-1)+'\\}', 'g'), safe);
    }
    return str;
  }

  // Save a reference of what may already exist under the property native.  
  // Allows for doing something like: if("".format.native) { /* use native */ }
  format.native = String.prototype.format;

  // Replace the prototype property
  return format;
}();
