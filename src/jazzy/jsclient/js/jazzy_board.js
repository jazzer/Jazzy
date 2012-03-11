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

var globalScalingFactor = 2;
var dragZoomFactor = 1.5;
var pieceImageReady = false;

var spriteOrder = "kqrbnpcih";


var highlightType = {
    LAST_MOVE: 1,
    SELECTION: 2,
    PREMOVE: 4
};



/* BoardStorage class */

function BoardStorage() {
    this.boards = [];
}

BoardStorage.prototype.newBoard = function(id, numXFields, numYFields, flipped) {
    var myboard = new Board(id, numXFields, numYFields, flipped);
    this.boards[id] = myboard;
    return myboard;
};

BoardStorage.prototype.getBoard = function(id) {
    if (this.boards[id] !== undefined) {
        return this.boards[id];
    }
    return undefined;
};





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

    // prepare highlighting information
    this.highlightArray = new Array(this.numFields);
    for (var i = 0; i < this.highlightArray.length; i++) {
        this.highlightArray[i] = 0;
    }

    this.build();

    this.pullStyles();
}


Board.prototype.lock = function() {
    this.locked = true;
};
Board.prototype.unlock = function() {
    this.locked = false;
};
Board.prototype.isLocked = function() {
    return this.locked;
};


Board.prototype.pullStyles = function() {
    pieceImageReady = false;
    this.pieceImg = new Image();

    /* wait for the piece image to load, then draw board
        using the CSS property background-image enables changing
        the piece set used with pure CSS.
    */
    var pieceImageInterval = window.setInterval(function() {
        var url = ($('#pieceImage-board_' + board.id).length > 0 ? $('#pieceImage-board_' + board.id) : $('#pieceImage')).css('background-image');
        if (url === '') {
            return;
        }
        window.clearInterval(pieceImageInterval);
        url = url.replace(/^url\(["']?(.*?)["']?\)$/, "$1");
        board.pieceImg.src = '';
        board.pieceImg.src = url;

        /* pull the relevant DOM elements for styling */
        board.backgroundStyle = ($('#backgroundColors-board_' + board.id).length > 0 ? $('#backgroundColors-board_' + board.id) : $('#backgroundColors'));
        board.highlightStyles = [];
        board.highlightStyles[highlightType.LAST_MOVE] = ($('#highlightColors-1-board_' + board.id).length > 0 ? $('#highlightColors-1-board_' + board.id) : $('#highlightColors-1'));
        board.highlightStyles[highlightType.SELECTION] = ($('#highlightColors-2-board_' + board.id).length > 0 ? $('#highlightColors-2-board_' + board.id) : $('#highlightColors-2'));
        board.highlightStyles[highlightType.PREMOVE] = ($('#highlightColors-3-board_' + board.id).length > 0 ? $('#highlightColors-3-board_' + board.id) : $('#highlightColors-3'));

        board.pieceImg.onload = function() {
            pieceImageReady = true;
        };
    }, 200);
};


Board.prototype.build = function() {
    // create a new board
    var board = this;
    var boardName = 'board_' + this.id;
    console.debug("building board " + boardName);

    // remove old board with same ID
    $("#" + boardName).remove();
    // generate the div and canvas elements
    var boardFrameDiv = $('<div>').attr({
        'id': boardName,
        'class': 'board'
    });

    var divCanvas = $('<div>').attr({
        'id': boardName + '-container-canvas',
        'class': 'canvas-container'
    });
    this.divCanvas = divCanvas;

    // create all the canvases
    this.canvasBoard = $("<canvas>").attr('id', boardName + '-canvas-board').css('z-index', 0).appendTo(this.divCanvas).get(0);
    console.debug(this.canvasBoard);
    this.canvasHighlight = $("<canvas>").attr('id', boardName + '-canvas-highlight').css('z-index', 1).appendTo(this.divCanvas).get(0);
    this.canvasPieces = $("<canvas>").attr('id', boardName + '-canvas-pieces').css('z-index', 2).appendTo(this.divCanvas).get(0);
    this.canvasDragging = $("<canvas>").attr('id', boardName + '-canvas-dragging').css('z-index', 3).appendTo(this.divCanvas).get(0);

    this.canvasFront = this.canvasDragging; // which one is top-most?
    this.divCanvas.css('cursor', 'pointer');

    // set events for drag and drop
    this.addMouseEvents();
    this.addKeyboardEvents();

    boardFrameDiv.append(divCanvas);

    // top data
    var templateDiv = _getTemplate('#top-data-boardId');
    templateDiv = _replaceInTemplate(templateDiv, "boardId", this.id);
    boardFrameDiv.prepend(templateDiv);
    // bottom
    templateDiv = _getTemplate('#bottom-data-boardId');
    templateDiv = _replaceInTemplate(templateDiv, "boardId", this.id);
    boardFrameDiv.append(templateDiv);

    // board controls
    templateDiv = _getTemplate('#board-controls-boardId');
    templateDiv = _replaceInTemplate(templateDiv, "boardId", this.id);
    boardFrameDiv.append(templateDiv);

    $("#boards").append(boardFrameDiv);
};



Board.prototype.sizeChanged = function() {
    var canvas = this.canvasBoard;
    var width = this.divCanvas.width();
    var height = this.divCanvas.height();
    if (Math.abs(canvas.width - width * globalScalingFactor) > 10 || Math.abs(canvas.height - height * globalScalingFactor) > 10) { // cache usable?
        var canvases = $('[id^="board_' + this.id + '-canvas-"]');
        canvases.css('width', width).css('height', height);
        canvases.each(function() {
            this.width = width * globalScalingFactor;
            this.height = height * globalScalingFactor;
        });

        // calculate space available for board (respect borders)            
        this.boardWidth = canvas.width - 2 * borderXSize;
        this.boardHeight = canvas.height - 2 * borderYSize;
        this.fieldWidth = this.boardWidth / this.numXFields;
        this.fieldHeight = this.boardHeight / this.numYFields;
        // force square fields
        this.fieldSize = Math.floor(Math.min(this.fieldWidth, this.fieldHeight));
        this.fieldWidth = this.fieldSize;
        this.fieldHeight = this.fieldSize;
        // center board
        this.xOffset = borderXSize + (this.boardWidth - this.fieldWidth * this.numXFields) / 2;
        this.yOffset = borderYSize + (this.boardHeight - this.fieldHeight * this.numYFields) / 2;
        this.boardWidth = this.fieldWidth * this.numXFields;
        this.boardHeight = this.fieldHeight * this.numYFields;
        return true;
    }
    return false;
};


Board.prototype.repaintFull = function() {
	console.debug("Called repaintFull for");
	console.debug(this);
    var board = this;
    // faking a sleep function
    if (!pieceImageReady) {
        window.setTimeout(function() {
            board.repaintFull();
        }, 200);
        return;
    }

    this.repaintBoard();
    this.repaintHighlight();
    this.repaintPieces();
    this.repaintDragging();
};

Board.prototype.repaintBoard = function() {
    if (this.sizeChanged()) {
        this.repaintFull();
        return;
    }

    var canvas = this.canvasBoard;
    console.info("painting board");
    console.debug(this.canvasBoard);
    var c = canvas.getContext('2d');
    // calculate sizes dynamically (if size did change, otherwise use cached values)

    // clear
    c.clearRect(0, 0, canvas.width, canvas.height);

    // draw board border (with a little shadow)
    c.rect(this.xOffset, this.yOffset, this.boardWidth, this.boardHeight);
    c.shadowOffsetX = 0;
    c.shadowOffsetY = 0;
    c.shadowBlur = canvas.width / 40;
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
        nextDark = (this.numFields % 2 === 0) ? nextDark : !nextDark;
        fieldId = this.numFields - 1;
        step = -step;
    }

    for (var row = 0; row < this.numYFields; row++) {
        for (var col = 0; col < this.numXFields; col++) {
            if (nextDark) {
                c.fillStyle = this.backgroundStyle.css('background-color');
            } else {
                c.fillStyle = this.backgroundStyle.css('color');
            }
            // draw single field's background (TODO: use images!)    
            c.fillRect(this.xOffset + col * this.fieldWidth, this.yOffset + row * this.fieldHeight, this.fieldWidth, this.fieldHeight);

            // prepare for next field
            nextDark = !nextDark;
            fieldId += step;
        }
        nextDark = (this.numXFields % 2 === 0) ? !nextDark : nextDark;
    }

    // draw side texts
    // TODO later
};


Board.prototype.repaintHighlight = function() {

    var canvas = this.canvasHighlight;
    var c = canvas.getContext('2d');

    // clear
    c.clearRect(0, 0, canvas.width, canvas.height);

    // iterate over board
    var nextDark = false;
    var fieldId = 0;
    var step = 1;
    if (this.flipped) {
        nextDark = (this.numFields % 2 === 0) ? nextDark : !nextDark;
        fieldId = this.numFields - 1;
        step = -step;
    }

    for (var row = 0; row < this.numYFields; row++) {
        for (var col = 0; col < this.numXFields; col++) {
            // TODO use parts of sprite image?
            if (this.highlightArray[fieldId] > 0) {
            	if (this.highlightArray[fieldId] >= highlightType.PREMOVE) {
                    if (nextDark) {
                        c.fillStyle = this.highlightStyles[highlightType.PREMOVE].css('background-color');
                    } else {
                        c.fillStyle = this.highlightStyles[highlightType.PREMOVE].css('color');
                    }
                } else if (this.highlightArray[fieldId] >= highlightType.SELECTION) {
                    if (nextDark) {
                        c.fillStyle = this.highlightStyles[highlightType.SELECTION].css('background-color');
                    } else {
                        c.fillStyle = this.highlightStyles[highlightType.SELECTION].css('color');
                    }
                } else if (this.highlightArray[fieldId] >= highlightType.LAST_MOVE) {
                    if (nextDark) {
                        c.fillStyle = this.highlightStyles[highlightType.LAST_MOVE].css('background-color');
                    } else {
                        c.fillStyle = this.highlightStyles[highlightType.LAST_MOVE].css('color');
                    }
                }
                c.fillRect(this.xOffset + col * this.fieldWidth, this.yOffset + row * this.fieldHeight, this.fieldWidth, this.fieldHeight);
            }

            // prepare for next field
            nextDark = !nextDark;
            fieldId += step;
        }
        nextDark = (this.numXFields % 2 === 0) ? !nextDark : nextDark;
    }
};


Board.prototype.repaintPieces = function() {
    if (!pieceImageReady) {
        return;
    }
    if (this.fenString === "") {
        return;
    }

    var canvas = this.canvasPieces;
    var c = canvas.getContext('2d');

    // clear
    c.clearRect(0, 0, canvas.width, canvas.height);

    // iterate over board
    var fieldId = 0;
    var step = 1;
    if (this.flipped) {
        fieldId = this.numFields - 1;
        step = -step;
    }

    var spriteWidth = this.pieceImg.width;
    for (var row = 0; row < this.numYFields; row++) {
        for (var col = 0; col < this.numXFields; col++) {
            // draw piece if applicable
            var pieceType = this.fields[fieldId];
            if (pieceType !== '_' && (this.moveFrom === undefined || this.moveFrom !== fieldId)) {
                var pieceIndex = getPieceIndex(pieceType);
                if (pieceIndex === -1) {
                    continue;
                }
                c.drawImage(this.pieceImg, 0, pieceIndex * spriteWidth, spriteWidth, spriteWidth, this.xOffset + col * this.fieldWidth, this.yOffset + row * this.fieldHeight, this.fieldWidth, this.fieldHeight);
            }

            // prepare for next field
            fieldId += step;
        }
    }
};



Board.prototype.repaintDragging = function() {
    if (!pieceImageReady) {
        return;
    }
    if (this.fenString === "") {
        return;
    }

    var canvas = this.canvasDragging;
    var c = canvas.getContext('2d');

    // clear
    c.clearRect(0, 0, canvas.width, canvas.height);

    // draw dragged piece (zoom it a little!)
    if (this.moveFrom !== undefined) {
        var pieceType = this.fields[this.moveFrom];
        if (pieceType !== undefined && pieceType !== '_') {
            var pieceIndex = getPieceIndex(pieceType);
            var zoomedWidth = this.fieldWidth * dragZoomFactor;
            var zoomedHeight = this.fieldHeight * dragZoomFactor;
            var spriteWidth = this.pieceImg.width;
            c.drawImage(this.pieceImg, 0, pieceIndex * spriteWidth, spriteWidth, spriteWidth, this.mousePos[0] * globalScalingFactor - zoomedWidth / 2, this.mousePos[1] * globalScalingFactor - zoomedHeight / 2, zoomedWidth, zoomedHeight);
        }
    }
};



function getPieceIndex(pieceType) {
    var pieceIndex = spriteOrder.indexOf(pieceType.toLowerCase()) * 2;
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

    this.divCanvas.mousedown(function(e) {
        // remove old premove
		board.resetPremoveInput();
    	// if alt key is hold, try to roll back everything
    	if (e.shiftKey) {
    		board.resetMoveInput();
    		board.repaintHighlight();
    		board.repaintPieces();
    		board.repaintDragging();
    	}
    	
        // find field
        var field = board.getField(e, this);
        if (field == -1) {
            return;
        }
		
        // source or target field clicked?
        if (board.moveFrom === undefined) {
            board.moveFrom = field;
            board.highlight(field, highlightType.SELECTION);

            board.mousePos = board.getRelativePos(e);

            // hide cursor if we drag something visible
            var pieceType = board.fields[board.moveFrom];
            if (pieceType !== '_') {
                board.divCanvas.css('cursor', 'none');
            }

            // repaint (for highlight field and piece zoom)
            board.repaintHighlight();
            board.repaintPieces();
            board.repaintDragging();
        } else {
            board.moveTo = field;
            board.highlight(field, highlightType.SELECTION);

            var postFrom = board.moveFrom;
            var postTo = board.moveTo;
            board.resetMoveInput();

            // repaint (for highlight field and piece zoom)
            board.repaintHighlight();
            board.repaintPieces();
            board.repaintDragging();

            // TODO use old move posting logic here
            var move = new Move(board.id, postFrom, postTo, undefined, e.ctrlKey);
            board.handleMoveInput(move);
        }
    });
    this.divCanvas.mouseup(function(e) {
    	// if alt key is hold, try to roll back everything
    	if (e.shiftKey) {
    		board.resetPremoveInput();
    		board.resetMoveInput();
    		board.repaintHighlight();
    		board.repaintPieces();
    		board.repaintDragging();
    	}

    	var field = board.getField(e, this);
        if (field == -1) {
            return;
        }

        if (board.moveFrom === undefined) {
            return;
        }

        var dragged = (field !== board.moveFrom);
        if (dragged) {
            board.moveTo = field;
            board.highlight(field, highlightType.SELECTION);

            var postFrom = board.moveFrom;
            var postTo = board.moveTo;
            board.resetMoveInput();

            // repaint (for resetting highlight field and piece zoom, possibly a move)
            board.repaintHighlight();
            board.repaintPieces();
            board.repaintDragging();

            // TODO use old move posting logic here            
            var move = new Move(board.id, postFrom, postTo, undefined, e.ctrlKey);
            board.handleMoveInput(move);
        }
    });

    this.divCanvas.mousemove(function(e) {
        // do a repaint, if a) mouse is down b)
        if (board.moveFrom !== undefined) {
            board.mousePos = board.getRelativePos(e);

            board.repaintDragging();
        }
    });


    this.divCanvas.mouseout(function(e) {
        board.resetMoveInput();
        // repaint
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });

    // TODO: does not seem to ever fire :(
    this.divCanvas.resize(function(e) {
        // repaint
        board.repaintBoard();
        board.repaintHighlight();
        board.repaintPieces();
        board.repaintDragging();
    });
};


Board.prototype.handleMoveInput = function(move) {
	var board = this;
	console.info(move);
	// is it a premove (it is iff it is not my turn)?
	if ($('#board_' + board.id).find('.player-me.player-curr').length > 0) {
		// real move
		move.send();
	} else {
		// premove
		board.premove = move;
		// highlight
        board.highlight(move.from, highlightType.PREMOVE);
        board.highlight(move.to, highlightType.PREMOVE);
		// repaint
        board.repaintHighlight();
	}
}

Board.prototype.resetPremoveInput = function() {
    this.premove = undefined;
    this.highlightClear(highlightType.PREMOVE);
}

Board.prototype.resetMoveInput = function() {
    this.moveFrom = undefined;
    this.moveTo = undefined;
    this.highlightClear(highlightType.SELECTION);

    this.divCanvas.css('cursor', 'pointer');
};


Board.prototype.addKeyboardEvents = function() {
    // TODO implement
};

Board.prototype.getRelativePos = function(e) {
    var elem = jQuery(this.canvasFront);
    var x = e.pageX - elem.offset().left;
    var y = e.pageY - elem.offset().top;

    var posArray = [x, y];
    return posArray;
};

Board.prototype.getField = function(e) {
    var elemPos = this.getRelativePos(e);
    var x = elemPos[0];
    var y = elemPos[1];

    var col = Math.floor((x * globalScalingFactor - this.xOffset) / this.fieldWidth);
    var row = Math.floor((y * globalScalingFactor - this.yOffset) / this.fieldHeight);

    if (col < 0 || col >= this.numXFields || row < 0 || row >= this.numYFields) {
        return -1;
    }

    var pos = row * this.numXFields + col;
    // flipped?
    if (this.flipped) {
        pos = this.numFields - 1 - pos;
    }
    return pos;
};



Board.prototype.loadFen = function(fenString) {
    this.fenString = fenString;
    var cleanFen = _lengthenFen(this.fenString, this.numXFields).replace(/\//g, "");
    this.fields = cleanFen.split("");

    this.repaintPieces();
};


Board.prototype.move = function(from, to, toPiece, silent) {
    // TODO animation?
    from = from.replace(/.*field/, '');
    to = to.replace(/.*field/, '');

    var isCapture = (this.fields[to] !== '_');

    this.fields[to] = this.fields[from];
    if (toPiece !== undefined) {
        this.fields[to] = toPiece;
    }
    this.fields[from] = '_';

    // play sound
    if (isCapture) {
        playSound('media/capture');
    } else {
        playSound('media/move');
    }

    // highlight move
    this.highlightClear(highlightType.LAST_MOVE);
    this.highlight(from, highlightType.LAST_MOVE);
    this.highlight(to, highlightType.LAST_MOVE);

    // is there a premove to be sent?
    if (this.premove !== undefined) {
    	this.premove.send();
    	this.resetPremoveInput();
    }
    
    // repaint
    this.repaintHighlight();
    this.repaintPieces();
};

Board.prototype.getPieceDiv = function(pieceType) {
    var pos = getPieceIndex(pieceType);
    if (pos == -1) {
        return '';
    }

    var pieceDiv = $("<div>");
    var url = ($('#pieceImage-board_' + board.id).length > 0 ? $('#pieceImage-board_' + board.id) : $('#pieceImage')).css('background-image');
    pieceDiv.css({
        'background-image': url,
        'background-color': "transparent",
        'background-repeat': "no-repeat",
        'height': this.pieceImg.width,
        'width': this.pieceImg.width,
        'background-position': "-0px -" + (pos * this.pieceImg.width) + "px"
    });
    return pieceDiv;
};

Board.prototype.highlight = function(fieldId, type) {
    this.highlightArray[fieldId] |= type; // bit-wise OR!
};

Board.prototype.highlightMove = function(from, to) {
    this.highlight(from, highlightType.LAST_MOVE);
    this.highlight(to, highlightType.LAST_MOVE);
};

Board.prototype.highlightClear = function(type) {
    if (type === undefined) {
        type = ~0;
    } // TODO check for correctness!
    for (var i = 0; i < this.highlightArray.length; i++) {
        this.highlightArray[i] &= ~type; // bit-wise NAND!
    }
};



function _lengthenFen(fenString, maxVal) {
    var replacement = "__";
    for (var i = 1; i <= maxVal; i++) {
        replacement = replacement + "_";
    }
    for (i = maxVal; i >= 1; i--) {
        var re = new RegExp(i, "g");
        fenString = fenString.replace(re, replacement.substring(0, i));
    }
    return fenString;
}

function _shortenFen(fenString, maxVal) {
    var searchString = "_";
    for (var i = 1; i <= maxVal; i++) {
        searchString = searchString + "_";
    }
    for (i = maxVal; i >= 1; i--) {
        var re = new RegExp(searchString.substring(0, i), "g");
        fenString = fenString.replace(re, i);
    }

    return fenString;
}


function playSound(url) {
    var audio = new Audio();
    audio.src = url + ".ogg";
    audio.play();
}






function _debug(msg, level) {
    if (debugLevel >= level) {
        addServerMessage(msg);
    }
}


String.prototype.startsWith = function(str) {
    return data.substring(0, input.length) === input;
};
