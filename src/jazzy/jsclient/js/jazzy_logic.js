/*
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
*/



/* server settings */
var server_url = self.location.protocol + "//" + self.location.host + "/";
/* timing */
var base_interval = 1000;
var max_interval = 15000;
var interval_factor = 1.4;

if (BoardStorage !== undefined) {
	var boardStorage = new BoardStorage();
}


/* global variables

	DO NOT CHANGE ANYTHING BELOW HERE 
	UNLESS YOU KNOW WHAT YOU DO! */
var debugLevel = 1;
var refreshInterval = 2;
var sinceLastRefresh = 0;
var gameId = undefined;
var mqId = undefined;
var lastParsedMsg = undefined;
var activeJSONCall = false;
var currPlayer = undefined;
var availible_games = undefined;
var currSelectedGame = undefined;
var unsuccessfulServerCallCounter = -1;



function _debug(msg, level) {
	if (debugLevel >= level) {
		addServerMessage(msg);
	}
}


function _playInit() {
	// wait for jQuery and the DOM to be ready
	$(document).ready(function() {
		// which MessageQueue are we operating on?
		mqId = window.location.href.match(/[\dA-Fa-f]+$/);

		// show debug level in UI
		$('[name="debugLevel"]').attr('value', debugLevel);		

		// request current situation (enables returning after problems)
		serverCall("getsit/" + mqId, function(data) {parseMQ(data);}, false, true);	
		//lastParsedMsg = undefined;
		// tell about your success
		addServerMessage("Finished setting up game.");

		// make sure to keep up to date
		setTimeout("refresh()", base_interval);
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
		//alert(game['cat']);
		categories[game['cat']] = 1; // using it as a set basically
	}
	
	// add them
	for (cat in categories) {
		//alert(cat);
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
		//alert(game['cat']);
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


function buildClassicBoard(cols, rows, flippedParam) {
	if (cols == board_cols && rows == board_rows && flippedParam == flipped) {
		return;
	}

	// create a new board
	$("#board").empty();
	var counter = 0;
	board_cols = cols;
	board_rows = rows;
	flipped = flippedParam;
	fields = board_cols * board_rows;
	for (var row = 1; row <= rows; row++) {
		for (var col = 1; col <= cols; col++) {
			var field = $("<div>");
			// color scheme (lower right field is white!)
			fieldPos = col+row + (flipped ? 0 : (cols+rows) % 2)
			field.addClass("field");
			if (fieldPos % 2 == 0) {
				field.addClass("light");
			} else {
				field.addClass("dark");
			}
			if (counter % cols == 0) {
				field.addClass("clear_row");
			}
			// id
			if (!flipped) {
				field.attr('id', 'field'+counter);
			} else {
				field.attr('id', 'field'+(fields-counter-1));
			}
			// set events for drag and drop
			if (!isWatching) {
				field.mousedown(function() {_dnd_down($(this))});
				field.mouseup(function() {_dnd_up($(this))});
				field.click(function() {_dnd_click($(this))});
			}
			
			// append it to the board			
			$("#board").append(field);

			counter++;
		}
	}

	// correct the board div's size
	var field_width = $("#field0").width();
	$("#board").css("width", field_width*cols);
	var field_height = $("#field0").height();
	$("#board").css("height", field_height*rows);
	
	_debug("Created board of size " + board_cols + "x" + board_rows, 3);
}



function postMove(from, to, promotion) {
	console.debug(from + "\n" + to);	
	// post move to server and move only upon response (means move was okay)!
	var url = 'post/' + mqId + '/move/' + from + '/' + to;
	if (promotion != undefined) {
		url += '/' + promotion
	}
	serverCall(url, function(data) {parseMQ(data);}, true, true);
}

function _shortCastling() {
	postMove("SHORT_CASTLING", "")
}
function _longCastling() {
	postMove("LONG_CASTLING", "")
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
	serverCall('post/' + mqId + '/chat/' + encodeURIComponent(msg), function(data) {parseMQ(data);}, true, true);
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





// jQuery communication
function refresh() {
	sinceLastRefresh++;
	if (refreshInterval > sinceLastRefresh) {
		//return;
	}
	_debug("Refreshed state.", 5);
	
	// do the call here and set changed approprietly
	getMQ();
	
	//sinceLastRefresh = 0;	
}


function createGame() {
	if (currSelectedGame == undefined) { return; }
	$(function() {
		$("#created_links").html();
		type = currSelectedGame;
		createNewGameIds(type);
		var your_link = server_url + 'play.html?' + mqId;
		var their_link = server_url + 'join.html?' + gameId;
		var watch_link = server_url + 'watch.html?' + gameId;
		$("#created_links").html('<b><h3>Your link:</h3> <a href="'+your_link+'">'+your_link+'</a></b><h3>Link for other players:</h3><a href="'+their_link+'">'+their_link+'</a><h3>Watch Game:</h3><a href="'+watch_link+'">'+watch_link+'</a>');
	});
}

function createNewGameIds(type) {
	// sanitize!?
	$.ajax({
		url: server_url + "new/" + type + "/" + new Date().getTime(),
		async: false,
		dataType: 'json',
		success: function(data){
			mqId = data['mqId'];
			gameId = data['gameId'];
		}
	});
}


function serverCall(relUrl, successFunc, asnycValue, preventCaching) {
	var callUrl = relUrl + ackString();
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

function ackString() {
	if (lastParsedMsg == undefined) {
		return '';
	}
	var result = "/ack/" + lastParsedMsg;
	lastParsedMsg = undefined;
	return result;

}

function getMQ() {
	if (activeJSONCall || mqId == undefined) {
		_debug("getMQ aborted (" + activeJSONCall + ")", 5);
		return;
	}
	activeJSONCall = true;

	// don't forget to acknowledge!
	var jsonUrl = server_url + "getmq/" + mqId + ackString() + "/" + new Date().getTime();
	// retrieve (plus possibly acknowledge last)
	_debug("now checking url " + jsonUrl, 5);
			
	$.getJSON(jsonUrl, function(data) {
		parseMQ(data);
		activeJSONCall = false;
		setTimeout("refresh()", refreshInterval);
	}).error(function (xhr, ajaxOptions, thrownError){
			activeJSONCall = false;
			recalcInterval(false);
			setTimeout(function(){refresh();}, refreshInterval);
			_debug("json error: " + xhr.status + " " + ajaxOptions + " " + thrownError, 5);
		});
}

function recalcInterval(success) {
	if (success) {
		refreshInterval = base_interval;
	} else {
		refreshInterval = Math.min(max_interval, refreshInterval * interval_factor);
	}
}

function parseCurrPlayer(currPlayerValue) {
	if (currPlayerValue == undefined) {
		return;
	}

	currPlayer = currPlayerValue;
	if (!myTurn && currPlayer == mqId.toString().substring(0, 10)) {
		document.title = "[DING] " + document.title;
		myTurn = true;
	} 
	else if (myTurn && currPlayer != mqId.toString().substring(0, 10)) {
		document.title = document.title.replace(/\[DING\] /, "");
		myTurn = false;
	}
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
	return fString.replace(/^board/, "").replace(/_field/, "_");
}
function lengthenFieldString(fString) {
	return fString.replace(/^/, "board").replace(/_/, "_field");
}



function parseMQ(data) {
	// did we receive messages? if so, keep checking frequently
	recalcInterval(data.length > 0);

	if (data.length > 0) {
		_debug("Received message queue: " + JSON.stringify(data, null, '\t'), 2);
	}
	
	// check if someone already parsed this
	for (var i=0;i<data.length;i++) {
		if (lastParsedMsg == data[i]['mid']) {
			return;
		}
	}
	
	for (var i=0;i<data.length;i++) {
		mtype = data[i]['mtype'];
		switch (mtype) {
			case "move":
				silent = data[i]['silent'] == true?true:false;				
				move(data[i]['from'], data[i]['to'], data[i]['toPiece'], silent); 
				parseCurrPlayer(data[i]['currP']);
				// TODO add ['check'] in server and client -> play sound (don't set when game is finished)
				break;
			case "movehist":
				addServerMessage(data[i]['user'] + " played <b>" + data[i]['str'] + "</b>"); 
				break;
			case "promote":
				// get options, offer, get decision and resend move
				var selectionDiv = $('<div>').html('Select which piece to promote to:<br/><br/>');
				for (elem in data[i]['options']) {
					piece = data[i]['options'][elem];					
					pieceDiv = getPieceDiv(piece).addClass('promotion_piece');
					// add events
					pieceDiv.bind("click", { Param1: data[i]['from'], Param2: data[i]['to'], Param3: piece }, function(event){
						postMove(event.data.Param1, event.data.Param2, event.data.Param3);
						// remove dialog
						$.modal.close();
					});
					// add to parent div
					selectionDiv.append(pieceDiv);
				}
				// call modally
				selectionDiv.modal();				
				break;
			case "chat":
				addChatMessage(data[i]['user'], decodeURIComponent(data[i]['msg'])); 
				break;
			case "gameover":
				goMsg = "Game finished. Result: " + data[i]['result'] + " (" + data[i]['msg'] + ")"
				addServerMessage(goMsg);
				setTimeout(function () { alert(goMsg); }, 1000);
				// TODO play sound 
				break;
			case "gamesit":
				// build the board
				boardId = data[i]['board_id'];		
				boardSize = data[i]['board_size'].split('x');		
				board = boardStorage.newBoard(boardId, boardSize[0], boardSize[1]);
				console.debug(board);
				board.flipped = data[i]['flipped'];
				// fix highlight
				board.highlight_clear();
				if (data[i]['lmove_from'] != undefined && data[i]['lmove_to'] != undefined) {
					highlight_move(lengthenFieldString(data[i]['lmove_from']), lengthenFieldString(data[i]['lmove_to']));
				}
				
				// load the position
				board.loadFen(data[i]['fen']);
				// check if it's my turn
				parseCurrPlayer(data[i]['currP']);
				break;
			case "srvmsg":
				addServerMessage(data[i]['msg']);
				break; 
			case "alert":
				alert(data[i]['msg']);
				break; 
			}		

		lastParsedMsg = data[i]['mid'];
		_debug("parsed message with id " + lastParsedMsg, 4);
	}	
}