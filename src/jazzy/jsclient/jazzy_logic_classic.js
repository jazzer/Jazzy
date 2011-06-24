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



/* settings */
var gameType = "classic";
var board_cols = 0;
var board_rows = 0;
var flipped = false;
/* sprites generated using http://csssprites.com/ */
var piece_sprite_url = "/img/pieces/48px/sprite48.png";
var piece_order = "kqrbnpcih";
var piece_width = 48;
/* server settings */
var server_url = self.location.protocol + "//" + self.location.host;
/* timing */
var base_interval = 1000;
var max_interval = 15000;
var interval_factor = 1.4;


/* global variables

	DO NOT CHANGE ANYTHING BELOW HERE 
	UNLESS YOU KNOW WHAT YOU DO! */
var dragSource = undefined;
var debugLevel = 3;
var refreshInterval = 2;
var sinceLastRefresh = 0;
var fields = board_cols*board_rows;
var gameId = undefined;
var mqId = undefined;
var lastParsedMsg = undefined;
var activeJSONCall = false;
var dnd_clicked = false;
var currPlayer = undefined;
var myTurn = false;
var isWatching = false;



function _debug(msg, level) {
	if (debugLevel >= level) {
		addServerMessage(msg);
	}
}


function _playInit() {
	// wait for jQuery and the DOM to be ready
	$(document).ready(function() {
		// prevent auto-dragging in Firefox
		$(document).bind("dragstart", function(e) {
    		if (e.target.nodeName.toLowerCase() == "div") {
				return false;
			}
		});

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
		});
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
				location.href = server_url + '/play.html?' + mqId;
			} else {
				$('#messages').append($('<span>').addClass('message').html(data['msg']));
			}		
		}, false, true);	
	});
}

function load_availible_games() {
	$(function() {
		serverCall("getgames", function(data) {
			list = $('[name="gametype"]');
			for (i in data) {
				list.append($("<option>").attr('value', i).html(data[i]));
			}
		}, false, true);		
	});
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

function _dnd_down(thisElement) {
	if (myTurn && thisElement.children().length > 0 && !dnd_clicked) {	
		dragSource = thisElement.attr('id').replace(/^field/, "");
		thisElement.addClass('highlight_input_move_from');
	}	
}
function _dnd_up(thisElement) {
	if (dragSource == undefined || dnd_clicked) {
		return;
	}
	dropTarget = thisElement.attr('id').replace(/^field/, "");
	if (!isNaN(dragSource) && !isNaN(dropTarget) && dragSource != dropTarget) {
		postMove(dragSource, dropTarget);
	} 

	$("#field" + dragSource).removeClass('highlight_input_move_from');
	dragSource = undefined; // this operation has been handled
}

function postMove(from, to, promotion) {
	// post move to server and move only upon response (means move was okay)!
	var url = 'post/' + mqId + '/move/' + from + '/' + to;
	if (promotion != undefined) {
		url += '/' + promotion
	}
	serverCall(url, function(data) {parseMQ(data);}, true, true);
}

function _dnd_click(thisElement) {
	if (dragSource == undefined) {
		_dnd_down(thisElement);
		dnd_clicked = true;
	} else {
		dnd_clicked = false;
		_dnd_up(thisElement);
	}
}



function loadFen(fenString) {
	// clear board
	$("#board").children('div[id^="field"]').children().remove();

	// create new pieces
	_debug("Loading FEN position: " + fenString, 3);
	cleanFen = _lengthenFen(fenString).replace(/\//g, "");
	chars = cleanFen.split("");

	for (var i = 0; i < chars.length; i++) {
		$("#field"+i).append(getPieceDiv(chars[i]));
	}
}

function getPieceDiv(pieceType) {
	if (pieceType == '') {
		return '';
	}

	// find right sprite and display it
	var pos = piece_order.indexOf(pieceType.toLowerCase())*2;
	// filter empty fields
	if (pos < 0) {
		return '';
	}

	if (pieceType == pieceType.toLowerCase()) {
		// black piece
		pos = pos + 1;
	}

	var pieceDiv = $("<div>");
	pieceDiv.css({'background-image': "url(" + server_url + piece_sprite_url + ")", 'background-color': "transparent", 'background-repeat': "no-repeat", 'height': piece_width, 'width': piece_width, 'background-position': "-0px -" + (pos*piece_width) + "px" });
	return pieceDiv
}


function _lengthenFen(fenString) {
	var replacement = "__";
	for (var i=2; i <= board_cols; i++) {
		replacement = replacement + "_";
	}
	for (var i=board_cols; i >= 2; i--) {
		var re = new RegExp(i, "g");
		fenString = fenString.replace(re, replacement.substring(0,i));
	}
	return fenString;
}

function _shortenFen(fenString) {
	var searchString = "_"
	for (var i=2; i <= board_cols; i++) {
		searchString = searchString + "_"
	}
	for (var i=board_cols; i >= 2; i--) {
		var re = new RegExp(searchString.substring(0, i), "g");
		fenString = fenString.replace(re, i);
	}

	return fenString;
}


function move(from, to, toPiece, silent) {
	// sanitize input?
	// without animation: $("#field" + from).children().detach().appendTo($("#field" + to).children().remove().end());
	if (from == -1) {
		return;
	}

	// animate the move
	fromField = $("#field" + from);
	toField = $("#field" + to);	
	isCapture = (toField.children().length > 0);
	isPiece = (fromField.children().length > 0);

	if (!isPiece) {
		return;
	}
	
	toField.children().css({'z-index': '2', 'position': 'absolute'}).fadeOut(400, function() {
		$(this).remove();
	});
		
	fromField.children().css({position: 'absolute',
				'z-index': 1,
				left: fromField.offset().left,
				top: fromField.offset().top})
		.animate({ 
				left: toField.offset().left,
				top: toField.offset().top
	    	}, 400, "swing", function() {
			// finished the move action, now do the promotion if requested
			if (toPiece != undefined) {
				$(this).fadeOut(400).parent().append(getPieceDiv(toPiece)).fadeIn(400);
			}
		});
	fromField.children().detach().prependTo(toField);

	if (!silent) {
		// highlight
		highlight_move(from, to);
		// sound
		if (isCapture) {
			playSound('media/capture');
		} else {
			playSound('media/move');
		}
	}

	// reset click event memory
	dragSource = undefined;
	dnd_clicked = false;
}

function playSound(url) {
	var audio = new Audio();
	audio.src = url+".ogg";
	audio.play();
}


function highlight_clear() {
	//var re = new RegExp("highlight_
	$("#board").children('div[id^="field"]').each(function() {
		$(this)[0].className = $(this)[0].className.replace(/highlight_[^ ]*/, ""); 
	});
}

function highlight(fieldNo, descr) {
	$("#field" + fieldNo).addClass("highlight_" + descr);
}

function highlight_move(from, to) {
	highlight_clear();	
	highlight(from, 'move_from');
	highlight(to, 'move_to');
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
	$('input[name="chatmsg"]').attr('value', '');
	addChatMessage("_", msg);
	// send the message to the server for distribution
	serverCall('post/' + mqId + '/chat/' + msg, function(data) {parseMQ(data);}, true, true);
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
	$(function() {
		$("#created_links").html();
		type = $('[name="gametype"]').children(":selected").attr('value');
		createNewGameIds(type);
		var your_link = server_url + '/play.html?' + mqId;
		var their_link = server_url + '/join.html?' + gameId;
		var watch_link = server_url + '/watch.html?' + gameId;
		$("#created_links").html('<b>Your link: <a href="'+your_link+'">'+your_link+'</a></b><br/>Link for other players: <a href="'+their_link+'">'+their_link+'</a><br/>Watch: <a href="'+watch_link+'">'+watch_link+'</a>');
	});
}

function createNewGameIds(type) {
	// sanitize!?
	$.ajax({
		url: server_url + "/new/" + type + "/" + new Date().getTime(),
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
		url: server_url + "/" + callUrl,
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
	return "/ack/" + lastParsedMsg;

}

function getMQ() {
	if (activeJSONCall || mqId == undefined) {
		_debug("getMQ aborted (" + activeJSONCall + ")", 5);
		return;
	}
	activeJSONCall = true;

	// don't forget to acknowledge!
	var jsonUrl = server_url + "/getmq/" + mqId + ackString() + "/" + new Date().getTime();
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
				addChatMessage(decodeURIComponent(data[i]['user']), decodeURIComponent(data[i]['msg'])); 
				break;
			case "gameover":
				goMsg = "Game finished. Result: " + data[i]['result'] + " (" + data[i]['msg'] + ")"
				addServerMessage(goMsg);
				setTimeout(function () { alert(goMsg); }, 1000);
				// TODO play sound 
				break;
			case "gamesit":
				// build the board
				boardSize = data[i]['board_size'].split('x');
				buildClassicBoard(boardSize[0], boardSize[1], data[i]['flipped']);
				// fix highlight
				highlight_clear();
				if (data[i]['lmove_from'] != undefined && data[i]['lmove_to'] != undefined) {
					highlight_move(data[i]['lmove_from'], data[i]['lmove_to']);
				}
				
				// load the position
				loadFen(data[i]['fen']);
				// check if it's my turn
				parseCurrPlayer(data[i]['currP']);
				break;
			case "srvmsg":
				addServerMessage(data[i]['msg']);
				break; 
			}		

		lastParsedMsg = data[i]['mid'];
		_debug("parsed message with id " + lastParsedMsg, 4);
	}	
}









