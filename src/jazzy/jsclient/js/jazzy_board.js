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

/* sprites generated using http://csssprites.com/ */
var piece_sprite_url = "img/pieces/48px/sprite48.png";
var piece_order = "kqrbnpcih";
var piece_width = 48;
var server_url = self.location.protocol + "//" + self.location.host + "/";
var board_cols = 0;
var board_rows = 0;
var flipped = false;
var dnd_clicked = false;
var dragSource = undefined;


/* BoardStorage class */
function BoardStorage() {
	this.boards = new Object();
}

BoardStorage.prototype.newBoard = function(id, width, height, flipped) {
	myboard = new Board(id, width, height, flipped);
	this.boards[id] = myboard;
	return myboard;
}

BoardStorage.prototype.getBoard = function(id) {
	if (this.boards[id] !== undefined) {
		return this.boards[id];
	}
	return undefined;
}


/* Board class */
function Board(id, width, height, flipped) {
	this.id = id;
	this.width = width;
	this.height = height;
	this.flipped = flipped;
	this.isWatching = false;
	this.locked = false;
	this.myTurn = true;	

	this.build();
}


Board.prototype.lock = function() {
	this.locked = true;
}
Board.prototype.unlock = function() {
	this.locked = false;
}

Board.prototype.build = function() {
	// create a new board
	var boardId = "board_" + this.id;
	var board = this;
	//console.debug(board);

	$("#" + boardId).parent().remove();
	boardDiv = $('<div>').attr('id', boardId).addClass('board');
	var counter = 0;
	var rows = this.height;
	var cols = this.width;
	var fields = cols*rows;
	for (var row = 1; row <= rows; row++) {
		for (var col = 1; col <= cols; col++) {
			var field = $("<div>");
			// color scheme (lower right field is white!)
			fieldPos = col+row + (this.flipped ? 0 : (cols+rows) % 2)
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
			if (!this.flipped) {
				field.attr('id', boardId + '_field' + counter);
			} else {
				field.attr('id', boardId + '_field' + (fields-counter-1));
			}
			// set events for drag and drop
			_addEvents(field, board);
			
			// append it to the board
			boardDiv.append(field);

			counter++;
		}
	}

	// pockets
	topPocket = $('<div>').attr('id', 'top-pocket-' + boardId).addClass('pocket').addClass('top-pocket');
	bottomPocket = $('<div>').attr('id', 'bottom-pocket-' + boardId).addClass('pocket').addClass('bottom-pocket');

	// buttons for castling
	outerDiv = $('<div>').append('Pocket: ').append(topPocket).append(boardDiv).append('Pocket: ').append(bottomPocket).append('<div class="roundbutton" onclick="_shortCastling(\'' + boardId + '\');">O-O</div> <div class="roundbutton" onclick="_longCastling(\'' + boardId + '\');">O-O-O</div><br /><br />');
			
	$("#boards").append(outerDiv);

	// correct the board div's size
	var field_width = $("#" + boardId + "_field0").width();
	boardDiv.css("width", field_width*cols);
	var field_height = $("#" + boardId + "_field0").height();
	boardDiv.css("height", field_height*rows);
}


Board.prototype.loadFEN = function(fenString) {
	var boardId = "board_" + this.id;
	
	// clear board
	$("div[id^='" + boardId + "_field']").children().remove();

	// create new pieces
	cleanFen = _lengthenFen(fenString, this.width).replace(/\//g, "");
	chars = cleanFen.split("");

	for (var i = 0; i < chars.length; i++) {
		$("#" + boardId + "_field"+i).append(this.getPieceDiv(chars[i]));
	}
}

Board.prototype.getPieceDiv = function(pieceType) {
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
	var url = server_url == 'file:///' ? piece_sprite_url:server_url + piece_sprite_url;
	pieceDiv.css({'background-image': "url(" + url + ")", 'background-color': "transparent", 'background-repeat': "no-repeat", 'height': piece_width, 'width': piece_width, 'background-position': "-0px -" + (pos*piece_width) + "px" });
	return pieceDiv
}


Board.prototype.move = function(from, to, toPiece, silent) {
	// sanitize input?
	// without animation: $("#field" + from).children().detach().appendTo($("#field" + to).children().remove().end());
	if (from == -1) {
		return;
	}
	if (silent === undefined) { silent = false; }

	// animate the move
	fromField = $("#" + from);
	toField = $("#" + to);	
	isCapture = (toField.children().length > 0);
	isPiece = (fromField.children().length > 0);

	if (!isPiece) {
		return;
	}	

	// clear target field
	toField.children().css({'z-index': '2'}).fadeOut(400, function() {
		$(this).remove();
	});

	outerThis = this;
	// move animation
	fromField.children().css({position: 'relative',
				'z-index': 1,
				left: 0,
				top: 0})
		.animate({ 
				left: toField.offset().left-fromField.offset().left,
				top: toField.offset().top-fromField.offset().top
	    	}, 400, "swing", function() {
			// finished the move action, now do the promotion if requested
			if (toPiece != undefined) {
				$(this).fadeOut(400).parent().append(outerThis.getPieceDiv(toPiece)).fadeIn(400);
			}
			// eventually set the piece to new field
			fromField.children().css({top: 0, left: 0}).detach().prependTo(toField);
		});

	if (!silent) {
		// highlight
		//if (from.startsWith('p')) {
			this.highlight_move(from, to);
		//} else {
			highlight(to, 'move_to');
		//}
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

Board.prototype.highlight_move = function(from, to) {
	this.highlight_clear();	
	highlight(from, 'move_from');
	highlight(to, 'move_to');
}

Board.prototype.highlight_clear = function() {
	var boardId = "board_" + this.id;
	$("#" + boardId).find('div[id*="field"]').each(function() {
		$(this)[0].className = $(this)[0].className.replace(/highlight_[^ ]*/, "");
	});
}



function _dnd_down(thisElement, board) {
	if (!board.locked && board.myTurn && thisElement.children().length > 0 && !dnd_clicked) {	
		dragSource = thisElement.attr('id');
		thisElement.addClass('highlight_input_move_from');
	}	
}

function _dnd_up(thisElement) {
	//console.debug("up at " + thisElement.attr('id'));
	//console.debug(dragSource);
	if (dragSource == undefined || dnd_clicked) {
		return;
	}
	dropTarget = thisElement.attr('id');
	//console.debug(dropTarget);
	if (dropTarget !== undefined && dragSource != dropTarget) {
		postMove(dragSource, dropTarget);
	} 

	$("#" + dragSource).removeClass('highlight_input_move_from');
	dragSource = undefined; // this operation has been handled
}


function _dnd_click(thisElement, board) {
	if (dragSource == undefined) {
		_dnd_down(thisElement, board);
		dnd_clicked = true;
	} else {
		dnd_clicked = false;
		_dnd_up(thisElement);
	}
}

function _lengthenFen(fenString, maxVal) {
	var replacement = "__";
	for (var i=2; i <= maxVal; i++) {
		replacement = replacement + "_";
	}
	for (var i=maxVal; i >= 2; i--) {
		var re = new RegExp(i, "g");
		fenString = fenString.replace(re, replacement.substring(0,i));
	}
	return fenString;
}

function _shortenFen(fenString, maxVal) {
	var searchString = "_"
	for (var i=2; i <= maxVal; i++) {
		searchString = searchString + "_"
	}
	for (var i=maxVal; i >= 2; i--) {
		var re = new RegExp(searchString.substring(0, i), "g");
		fenString = fenString.replace(re, i);
	}

	return fenString;
}


function playSound(url) {
	var audio = new Audio();
	audio.src = url+".ogg";
	audio.play();
}




function highlight(fieldId, descr) {
	$("#" + fieldId).addClass("highlight_" + descr);
}

function _addEvents(object, board) {
	if (!board.isWatching) {
		object.mousedown(function() {_dnd_down($(this), board)});
		object.mouseup(function() {_dnd_up($(this))});
		object.click(function() {_dnd_click($(this), board)});
	}
}



function _debug(msg, level) {
	if (debugLevel >= level) {
		addServerMessage(msg);
	}
}


String.prototype.startsWith = function (str){
    return data.substring(0, input.length) === input;
};



$(document).ready(function() {
		// prevent auto-dragging in Firefox
		$(document).bind("dragstart", function(e) {
    		if (e.target.nodeName.toLowerCase() == "div") {
				return false;
			}
		});
});



