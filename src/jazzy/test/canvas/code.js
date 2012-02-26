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


// settings
var borderXSize = 50;
var borderYSize = 50;
var fontWidth = 100;

var globalScalingFactor = 4;
var dragZoomFactor = 1.3;

var spriteOrder = "kqrbnpcih";
var spriteBaseSize = 48;


var highlightType = {
    LAST_MOVE : 1,
    SELECTION : 2
}



$(document).ready(function() {
    b1 = new Board(1, 8, 8, false);
    b1.loadFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR");
});



/* BoardStorage class */
function BoardStorage() {
	this.boards = new Object();
}

BoardStorage.prototype.newBoard = function(id, numXFields, numYFields, flipped) {
	var myboard = new Board(id, numXFields, numYFields, flipped);
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
function Board(id, numXFields, numYFields, flipped) {
    var elem = document.createElement('canvas');    
    if (!elem.getContext && elem.getContext('2d')) {
        alert('No canvas support :-(');
    }

    this.id = id;
	this.numXFields = numXFields;
	this.numYFields = numYFields;
	this.flipped = flipped;
	this.isWatching = false;
	this.locked = false;
	this.animated = false;
    this.fenString = "";
    this.numFields = numXFields * numYFields;

    this.pieceImg = $('#pieceImage').get(0);
    
    // prepare highlighting information
    this.highlightArray = new Array(this.numFields);
    for (var i=0; i < this.highlightArray.length; i++) {
        this.highlightArray[i] = 0;
    }

    // jQuery caching
    this.divId = "#board_" + this.id;
    this.div = $("#board_" + this.id);
    // create all the canvases if necessary
    this.jqcanvas = this.div.find('canvas');
    if (this.jqcanvas.length == 0) {
        $("<canvas>").attr('id', 'board_' + this.id + '-canvas-board').css('position', 'absolute').css('z-index', 0).appendTo(this.div);        
        $("<canvas>").attr('id', 'board_' + this.id + '-canvas-highlight').css('position', 'absolute').css('z-index', 1).appendTo(this.div);        
        $("<canvas>").attr('id', 'board_' + this.id + '-canvas-pieces').css('position', 'absolute').css('z-index', 2).appendTo(this.div);        
        $("<canvas>").attr('id', 'board_' + this.id + '-canvas-dragging').css('position', 'absolute').css('z-index', 3).appendTo(this.div);        

        this.jqcanvas = this.div.find('canvas');
    }
    this.canvasBoard = this.jqcanvas[0];
    this.canvasHighlight = this.jqcanvas[1];
    this.canvasPieces = this.jqcanvas[2];
    this.canvasDragging = this.jqcanvas[3];
    this.div.css('cursor', 'pointer');

	this.build();
    var board = this;
    var pieceImg = $('#pieceImage')[0];
    pieceImg.onload = function(){
        board.repaintFull();
    };
}


Board.prototype.lock = function() {
	this.locked = true;
}
Board.prototype.unlock = function() {
	this.locked = false;
}
Board.prototype.isLocked = function() {
	return this.locked;
}


Board.prototype.build = function() {
	// create a new board
	var boardId = this.divId;
	var board = this;
	
	// set events for drag and drop
	this.addMouseEvents();
	this.addKeyboardEvents();
		
	// pockets
	topPocket = $('<div>').attr('id', 'top-pocket-' + boardId).addClass('pocket').addClass('top-pocket');
	bottomPocket = $('<div>').attr('id', 'bottom-pocket-' + boardId).addClass('pocket').addClass('bottom-pocket');
	// players
	topPlayers = $('<div>').attr('id', 'top-players-' + boardId).addClass('players top-players');
	bottomPlayers = $('<div>').attr('id', 'bottom-players-' + boardId).addClass('players bottom-players');

	// buttons for castling
	//outerDiv = $('<div>').attr('id', boardId + '-frame').append(topPocket).append(topPlayers).append(boardDiv).append(bottomPlayers).append(bottomPocket).append($('<div>').attr('id', boardId + '-controls').append(this.getBoardControls()));
			
	//$("#boards").append(outerDiv);
}

Board.prototype.sizeChanged = function() {
    var canvas = this.canvasBoard;
    var width = this.div.width();
    var height = this.div.height();
    if (Math.abs(canvas.width - width * globalScalingFactor) > 10 || Math.abs(canvas.height - height * globalScalingFactor) > 10) { // cache usable?
        var canvases = $('[id^="board_' + this.id + '-canvas-"]');
        console.debug(canvases);
        canvases.css('width', width).css('height', height);    
        canvases.each(function() {
            this.width = width * globalScalingFactor;   
            this.height = height * globalScalingFactor;
        });

        // calculate space availible for board (respect borders)            
        this.boardWidth = canvas.width - 2*borderXSize;
        this.boardHeight = canvas.height - 2*borderYSize;
        this.fieldWidth = this.boardWidth/this.numXFields;
        this.fieldHeight = this.boardHeight/this.numYFields;
         // force square fields
        this.fieldSize = Math.floor(Math.min(this.fieldWidth, this.fieldHeight));
        this.fieldWidth = this.fieldSize;
        this.fieldHeight = this.fieldSize;
        // center board
        this.xOffset = borderXSize + (this.boardWidth - this.fieldWidth*this.numXFields)/2;
        this.yOffset = borderYSize + (this.boardHeight - this.fieldHeight*this.numYFields)/2;
        this.boardWidth = this.fieldWidth*this.numXFields;
        this.boardHeight = this.fieldHeight*this.numYFields;
        return true;
    }
    return false;
}


Board.prototype.repaintFull = function() {
    this.repaintBoard();
    this.repaintHighlight();
    this.repaintPieces();
    this.repaintDragging();
}

Board.prototype.repaintBoard = function() {
    if (this.sizeChanged()) {
        this.repaintFull();
        return;
    }

    var canvas = this.canvasBoard;
    var c = canvas.getContext('2d');
    // calculate sizes dynamically (if size did change, otherwise use cached values)
    

    // clear
    c.clearRect(0,0,canvas.width,canvas.height);

    // draw board border (with a little shadow)
    c.rect(this.xOffset, this.yOffset, this.boardWidth, this.boardHeight);
    c.shadowOffsetX = 0;
    c.shadowOffsetY = 0;
    c.shadowBlur = canvas.width/40;
    c.shadowColor = "gray";
    c.strokeStyle = "black";
    c.fillStyle = "black";
    c.fill();
    c.shadowBlur = 0;
        
    // draw board (with respect to highlighted fields!)
    var nextDark = false;
    var fieldId = 0;
    var step = 1;
    if (this.flipped) {
        nextDark = (this.numFields % 2 == 0) ? nextDark : !nextDark;
        fieldId = this.numFields - 1;
        step = -step;
    }
    
    for (var row=0; row<this.numYFields ; row++) {
        for (var col=0; col<this.numXFields ; col++) {
            if (nextDark) {
                c.fillStyle = "#1A12A6";
            } else {
                c.fillStyle = "#C0BEED";
            }
            // draw single field's background (TODO: use images!)    
            c.fillRect(this.xOffset + col*this.fieldWidth, this.yOffset + row*this.fieldHeight, this.fieldWidth, this.fieldHeight);

            // prepare for next field
            nextDark = !nextDark;
            fieldId += step;
        }
        nextDark = (this.numXFields % 2 == 0) ? !nextDark : nextDark;
    }

    // draw side texts
    // TODO later
}


Board.prototype.repaintHighlight = function() {
    var canvas = this.canvasHighlight;
    var c = canvas.getContext('2d');

    // clear
    c.clearRect(0,0,canvas.width,canvas.height);

    // draw board (with respect to highlighted fields!)
    var nextDark = false;
    var fieldId = 0;
    var step = 1;
    if (this.flipped) {
        nextDark = (this.numFields % 2 == 0) ? nextDark : !nextDark;
        fieldId = this.numFields - 1;
        step = -step;
    }
    
    for (var row=0; row<this.numYFields ; row++) {
        for (var col=0; col<this.numXFields ; col++) {
            // TODO use parts of sprite image?
            if (this.highlightArray[fieldId] > 0) {
                if (this.highlightArray[fieldId] >= highlightType.SELECTION) {
                    if (nextDark) {
                        c.fillStyle = "#4A8F63";
                    } else {
                        c.fillStyle = "#2AF775";
                    }
                } else if (this.highlightArray[fieldId] >= highlightType.LAST_MOVE) {
                    if (nextDark) {
                        c.fillStyle = "#DBBE00";
                    } else {
                        c.fillStyle = "#E2FA6B";
                    }
                }
                c.fillRect(this.xOffset + col*this.fieldWidth, this.yOffset + row*this.fieldHeight, this.fieldWidth, this.fieldHeight);
            }
               
            // prepare for next field
            nextDark = !nextDark;
            fieldId += step;
        }
        nextDark = (this.numXFields % 2 == 0) ? !nextDark : nextDark;
    }    
}


Board.prototype.repaintPieces = function() {
    var canvas = this.canvasPieces;
    var c = canvas.getContext('2d');

    // clear
    c.clearRect(0,0,canvas.width,canvas.height);

    // draw board (with respect to highlighted fields!)
    var nextDark = false;
    var fieldId = 0;
    var step = 1;
    if (this.flipped) {
        nextDark = (this.numFields % 2 == 0) ? nextDark : !nextDark;
        fieldId = this.numFields - 1;
        step = -step;
    }
    
    for (var row=0; row<this.numYFields ; row++) {
        for (var col=0; col<this.numXFields ; col++) {
            // draw piece if applicable
            if (this.fenChars[fieldId] !== '_' && (this.moveFrom === undefined || this.moveFrom !== fieldId)) {
                var pieceType = this.fenChars[fieldId];
                var pieceIndex = getPieceIndex(pieceType);
                //c.fillText(this.fenChars[fieldId], xOffset + col*fieldWidth, yOffset + row*fieldHeight);
                c.drawImage(this.pieceImg, 0, pieceIndex*spriteBaseSize, spriteBaseSize, spriteBaseSize,
                            this.xOffset + col*this.fieldWidth, this.yOffset + row*this.fieldHeight, this.fieldWidth, this.fieldHeight);
            }
               
            // prepare for next field
            nextDark = !nextDark;
            fieldId += step;
        }
        nextDark = (this.numXFields % 2 == 0) ? !nextDark : nextDark;
    }    
}



Board.prototype.repaintDragging = function() {
    var canvas = this.canvasDragging;
    var c = canvas.getContext('2d');
    
    // clear
    c.clearRect(0,0,canvas.width,canvas.height);

    // draw dragged piece (zoom it a little!)
    if (this.moveFrom !== undefined) {
        var pieceType = this.fenChars[this.moveFrom];
        if (pieceType !== '_') {
            var pieceIndex = getPieceIndex(pieceType);
            var zoomedWidth = this.fieldWidth*dragZoomFactor;
            var zoomedHeight = this.fieldHeight*dragZoomFactor;
            c.drawImage(this.pieceImg, 0, pieceIndex*spriteBaseSize, spriteBaseSize, spriteBaseSize,
                this.mouseX*globalScalingFactor-zoomedWidth/2, this.mouseY*globalScalingFactor-zoomedHeight/2, zoomedWidth, zoomedHeight);
        }
    }
}





function getPieceIndex(pieceType) {
    var pieceIndex = spriteOrder.indexOf(pieceType.toLowerCase())*2;
    if (pieceIndex >= 0) {
        if (pieceType == pieceType.toLowerCase()) {
            // black piece
            pieceIndex = pieceIndex + 1;
        }
    }
    return pieceIndex;
}

Board.prototype.addMouseEvents = function() {
    var board = this;
    this.jqcanvas.mousedown(function(e) {
        // find field
        var field = board.getField(e, this);
        // source or target field clicked?
        if (board.moveFrom === undefined) {
            board.moveFrom = field;
            board.highlight(field, highlightType.SELECTION);

            board.mouseX = e.pageX - board.canvasBoard.offsetLeft;
	        board.mouseY = e.pageY - board.canvasBoard.offsetTop;
            
            // hide cursor if we drag something visible
            var pieceType = board.fenChars[board.moveFrom];
            if (pieceType !== '_') {
                board.div.css('cursor', 'none');
            }
        } else {
            board.moveTo = field;
            board.highlight(field, highlightType.SELECTION);

            // TODO use old move posting logic here            
            console.debug("moving " + board.moveFrom + " to " + board.moveTo);
            board.resetMoveInput();
        }
        
        // repaint (for highlight field and piece zoom)
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });
    this.jqcanvas.mouseup(function(e) {
        var field = board.getField(e, this);
        if (board.moveFrom === undefined) {
            return;
        }
        
        var dragged = (field !== board.moveFrom); 
        if (dragged) {
            board.moveTo = field;
            board.highlight(field, highlightType.SELECTION);
            
            // TODO use old move posting logic here            
            console.debug("moving " + board.moveFrom + " to " + board.moveTo);
            board.resetMoveInput();
        }
        
        // repaint (for resetting highlight field and piece zoom, possibly a move)
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });

    this.jqcanvas.mousemove(function(e) {
        // do a repaint, if a) mouse is down b)
        if (board.moveFrom !== undefined) {
            board.mouseX = e.pageX - board.canvasBoard.offsetLeft;
	        board.mouseY = e.pageY - board.canvasBoard.offsetTop;

            board.repaintDragging();
        } 
    });


    this.jqcanvas.mouseout(function(e) {
        board.resetMoveInput();
        // repaint
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });

    // TODO: does not seem to ever fire :(
    this.div.resize(function(e) {
        console.debug('resized');
        // repaint
        board.repaintBoard();
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });
}

Board.prototype.resetMoveInput = function() {
    this.moveFrom = undefined;
    this.moveTo = undefined;
    this.highlightClear(highlightType.SELECTION);

    this.div.css('cursor', 'pointer');
}


Board.prototype.addKeyboardEvents = function() {
}


Board.prototype.getField = function(e, elem) {
    var x = e.pageX - elem.offsetLeft;
	var y = e.pageY - elem.offsetTop;
    
    var col = Math.floor((x*globalScalingFactor-this.xOffset) / this.fieldWidth);
    var row = Math.floor((y*globalScalingFactor-this.yOffset) / this.fieldHeight);
    //console.debug("Zeile " + row + "\nSpalte:" + col);
    var pos = row*this.numXFields + col;
    // flipped?
    if (this.flipped) {
        pos = this.numFields - 1 - pos;
    }
    return pos;
}


Board.prototype.getBoardControls = function(boardId) {
	return '<button type="button" class="btn" onclick="_shortCastling(\'' + boardId + '\');">O-O</button> <button type="button" class="btn" onclick="_longCastling(\'' + boardId + '\');">O-O-O</button><br /><br />' + '<button type="button" class="btn" id="btn_offer_draw" onclick="_offerDraw(\'' + boardId + '\');">Offer draw</button> ' + '<button type="button" class="btn" id="btn_repetition" onclick="_repetition(\'' + boardId + '\');">Claim Repetition</button> ' + '<button type="button" class="btn" id="btn_x_move_rule" onclick="_xMoveRule(\'' + boardId + '\');">Claim x Move rule</button> ' + '<button type="button" class="btn" id="btn_resign" onclick="_resign(\'' + boardId + '\');">Resign</button>';
}


Board.prototype.loadFen = function(fenString) {
    this.fenString = fenString;
    var cleanFen = _lengthenFen(this.fenString, this.numXFields).replace(/\//g, "");
    this.fenChars = cleanFen.split("");
    
	this.repaintPieces();
}


Board.prototype.move = function(from, to, toPiece, silent) {

}

Board.prototype.highlight = function(fieldId, type) {
    this.highlightArray[fieldId] |= type; // bit-wise OR!
}

Board.prototype.highlightMove = function(from, to) {
	this.highlight(from, highlightType.LAST_MOVE);
	this.highlight(to, highlightType.LAST_MOVE);
}

Board.prototype.highlightClear = function(type) {
    for (var i=0; i<this.highlightArray.length; i++) {
	    this.highlightArray[i] &= ~type; // bit-wise NAND!
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






function _debug(msg, level) {
	if (debugLevel >= level) {
		addServerMessage(msg);
	}
}


String.prototype.startsWith = function (str){
    return data.substring(0, input.length) === input;
};




