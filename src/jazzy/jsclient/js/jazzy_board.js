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

var piece_sprite_url = "img/pieces/48px/sprite48.png";
var piece_order = "kqrbnpcih";
var piece_width = 48;
var server_url = self.location.protocol + "//" + self.location.host + "/";
alert(server_url);

function Board(id, width, height) {
	this.id = id;
	this.width = width;
	this.height = height;
	this.flipped = false;
	this.isWatching = false;

	//alert(this.width + " x " + this.height);

	this.build();
}

Board.prototype.build = function() {
	// create a new board
	var boardId = "board_" + this.id;
	$("#" + boardId).remove();
	boardDiv = $('<div>').attr('id', boardId).addClass('board');
	var counter = 0;
	var rows = this.height;
	var cols = this.width;
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
				field.attr('id', boardId + '_field'+counter);
			} else {
				field.attr('id', boardId + '_field'+(fields-counter-1));
			}
			// set events for drag and drop
			if (!this.isWatching) {
				field.mousedown(function() {_dnd_down($(this))});
				field.mouseup(function() {_dnd_up($(this))});
				field.click(function() {_dnd_click($(this))});
			}
			
			// append it to the board	
			boardDiv.append(field);
			$("#boards").append(boardDiv);

			counter++;
		}
	}

	// correct the board div's size
	var field_width = $("#" + boardId + "_field0").width();
	boardDiv.css("width", field_width*cols);
	var field_height = $("#" + boardId + "_field0").height();
	boardDiv.css("height", field_height*rows);
	
	//_debug("Created board of size " + board_cols + "x" + board_rows, 3);
}


Board.prototype.loadFEN = function(fenString) {
	var boardId = "board_" + this.id;
	
	// clear board
	$("#board").children('div[id^="field"]').children().remove();

	// create new pieces
	//_debug("Loading FEN position: " + fenString, 3);
	cleanFen = fenString.replace(/\//g, "");
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
	console.debug(pieceDiv);
	return pieceDiv
}


// Test
$(function() {
	myBoard = new Board("b1", 8, 8);
	myBoard2 = new Board("b2", 5, 5);
	myBoard.loadFEN('K_______/________/qrppk___/________/________/________/________/________');
});


