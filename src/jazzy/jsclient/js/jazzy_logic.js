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
var runningClocks, clickTimeoutId;

if (typeof BoardStorage === 'function') {
    var boardStorage = new BoardStorage();
}


/*
 * global variables
 * 
 * DO NOT CHANGE ANYTHING BELOW HERE UNLESS YOU KNOW WHAT YOU DO!
 */
var debugLevel = 1;
var gameId, mqId, availible_games, currSelectedGame, playerName;
var activeJSONCall = false;
var styleNameArray = styleNames.split(",");
var boardStyleNameArray = boardStyleNames.split(",");
var selfPlayerIDs = '';
var currPlayer = {};
var myTurn = {};
var sock, game;


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
        }, function() {
            $(this).html('Disconnect');
            // TODO something like sock.reconnect();
        });

        // setup style chooser
        var targets = $('[name="style-chooser-main"]');
        for (var styleIndex in styleNameArray) {
            targets.append($('<option>').text(styleNameArray[styleIndex]));
        }
        targets = $('[name="style-chooser-board"]');
        for (styleIndex in boardStyleNameArray) {
            targets.append($('<option>').text(boardStyleNameArray[styleIndex]));
        }
        $('select[name="style-chooser-main"]').change(function() {
            _changeStyle('main');
        });
        $('select[name="style-chooser-board"]').change(function() {
            _changeStyle('board');
        });
        
        // code for fullscreen mode
        window.addEventListener("mozfullscreenchange", function() { _onFullscreen(); });
        window.addEventListener("webkitfullscreenchange", function() { _onFullscreen(); });
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
            $(this).find('[class^="data_content"]').slideUp(500, function() {
                $(this).toggleClass('data_content_empty').toggleClass('data_content');
            });
        }).click().click();
    });
}


function _onFullscreen() {
	var element = getFullscreenElement();
	if (element !== undefined && element !== null) {
		// fullscreen has been started
		
		// calc maximum board size dynamically
		element = $(element);
		var height = $(window).height();
		console.debug("Height: " + height);
		$(element).children(':not(.canvas-container)').each(function() {
			height -= $(this).height();
			console.debug(height);
		});
		var width = $(window).width();
		console.debug("Width: " + $(window).width());
		// set appropriate css rules
		console.debug(element);
		element.find('.canvas-container').each(function() {
			console.debug("canvas: " + $(this));
			// save prior size
			$(this).data('old-width', $(this).css('width'));
			$(this).data('old-height', $(this).css('height'));
			// set new size
			$(this).css({'width': width, 'height': height});
			// repaint
			var boardId = element.attr('id').replace(/-.*/, '').replace('board_', '');
	        var thisBoard = boardStorage.getBoard(boardId);
	        thisBoard.repaintFull();
		});
	} else {
		// fullscreen exited
		$('.board').find('.canvas-container').each(function() {
			// save prior size
			if ($(this).data('old-width') !== undefined) {
				// set new size
				$(this).css({'width': $(this).data('old-width'), 'height': $(this).data('old-height')});
				// repaint
				var boardId = $(this).attr('id').replace(/-.*/, '').replace('board_', '');
		        var thisBoard = boardStorage.getBoard(boardId);
		        thisBoard.repaintFull();
			}
		});
	}
}


function getFullscreenElement() {
	return document.mozFullScreenElement; // || window.webkitFullScreenElement;
}

function _changeStyle(type, value) {
    var target;
    if (type == 'main') {
        target = $('[name^="style-chooser-main"]');
    } else {
        target = $('[name^="style-chooser-board"]');
    }
    // unload old and reload new css file
    if (value !== undefined) {
        newStyleFile = target.val(value);
    }
    value = target.val();
    var newStyleFile = 'css/' + target.val() + '-' + type + '.css';

    // already loaded?
    if ($('link[href="css/' + newStyleFile + '"]').size() > 0) return;

    // actually change the css file parsed
    for (var styleIndex in styleNameArray) {
        // remove
        $('link[href="css/' + styleNameArray[styleIndex] + '-' + type + '.css"]').remove();
    }
    // set new style
    $('head').append($('<link>').attr({
        'type': 'text/css',
        'rel': 'stylesheet',
        'href': newStyleFile
    }));

    // repaint boards if style changed
    var boards = $('.board');
    boards.each(function() {
        var boardId = $(this).attr('id').replace(/^board_/, '');
        var thisBoard = boardStorage.getBoard(boardId);

        thisBoard.pullStyles(); // also triggers .repaintFull()        
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
            mqId = data.mqId;
            if (mqId !== undefined) {
                location.href = server_url + 'play.html?' + mqId;
            } else {
                $('#messages').append($('<span>').addClass('message').html(data.msg));
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
    if (availible_games === undefined) {
        return;
    }
    target = $('#gameSelection_step1');
    target.empty();
    // find categories
    categories = {};
    for (var gameId in availible_games) {
        game = availible_games[gameId];
        categories[game.cat] = 1; // using it as a set basically
    }

    // add them
    for (var cat in categories) {
        entry = $('<div>').addClass('entry').html(cat);
        entry.click(function() {
            showGames($(this).html());
        }); // TODO setup function
        target.append(entry);
    }
}

// show games of selected category


function showGames(cat) {
    target = $('#gameSelection_step2');
    target.empty();

    // loop games
    for (var gameId in availible_games) {
        game = availible_games[gameId];
        if (game.cat == cat) {
            entry = $('<div>').addClass('entry').html(game.title);
            entry.click(function() {
                showDetails($(this).html());
            }); // TODO setup function
            target.append(entry);
        }
    }
}

// show game details


function showDetails(game) {
    target = $('#gameSelection_step3');
    target.empty();

    // loop games
    for (var gameId in availible_games) {
        loopGame = availible_games[gameId];
        if (game === loopGame.title) {
            target.html(loopGame.title + '<br/>' + loopGame.desc + '<br/>' + loopGame.details + '<br/><a href="' + loopGame.link + '">More...</a>');
            break;
        }
    }

    currSelectedGame = game;
}



function _shortCastling(boardId) {
    var move = new Move(boardId, "SHORTCASTLING", "");
    var board = boardStorage.getBoard(boardId);
    board.handleMoveInput(move);
}

function _longCastling(boardId) {
    var move = new Move(boardId, "LONGCASTLING", "");
    var board = boardStorage.getBoard(boardId);
    board.handleMoveInput(move);
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
    if (arguments.length === 0) {
        doShort = true;
    }

    var result = '<span class="time">';
    var now = new Date();
    if (now.getHours() < 10) {
        result = result + '0';
    }
    result = result + now.getHours() + ':';
    if (now.getMinutes() < 10) {
        result = result + '0';
    }
    result = result + now.getMinutes();
    if (!doShort) {
        result = result + ':';
        if (now.getSeconds() < 10) {
            result = result + '0';
        }
        result = result + now.getSeconds();
    }
    return result + "</span>";
}




function createGame() {
    if (currSelectedGame === undefined) {
        return;
    }
    serverCall('new/' + currSelectedGame, function(data) {
        follow(data);
    }, true, true);
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

function _claimClock(boardId) {
    // claim clock
    game.send("claim/" + mqId + "/clock");
}

function _claimRepetition(boardId) {
    // claim threefold repetition
    game.send("claim/" + mqId + "/repetition");
}

function _claimXMoveRule(boardId) {
    // claim threefold repetition
    game.send("claim/" + mqId + "/xmoverule");
}


function updateOverview() {
    $(document).ready(function() {
        window.setInterval("showSlots()", 5000);
        showSlots();
    });
}

function showSlots() {
    gameId = window.location.href.match(/[\dA-Fa-f]+$/);
    serverCall('getslots/' + gameId, function(data) {
        var target = $('#slots').empty();
        for (var i = 0; i < data.length; i++) {
            var slotDiv = $('<div>').addClass('slot-box');
            if (data[i].open === true) {
                slotContent = '<div class="slot-desc">{0}</div><div class="slot-pname">{1}</div>'.format(data[i].desc, data[i].pname);
                slotDiv.addClass('slot-open');
                // add joining event
                slotDiv.data('joinId', data[i].joinId);
                slotDiv.click(function(joinId) {
                    serverCall('join/' + gameId + '/' + $(this).data('joinId') + '/' + getPlayerName(), function(data) {
                        follow(data);
                    }, true, true);
                });
            } else {
                slotContent = '<div class="slot-desc">{0}</div><div class="slot-pname"></div>'.format(data[i].desc);
                slotDiv.addClass('slot-taken');
            }
            // put to DOM
            target.append(slotDiv.html(slotContent));
        }
    }, true, true);
}


function follow(data) {
    if (data.msg !== undefined) {
        $.prompt(data.msg);
    } else {
        // follow the link sent by the server
        window.location = data.link;
    }
}


function _parseCurrPlayer(currPlayerValue, boardId) {
    if (currPlayerValue === undefined) {
        return;
    }

    currPlayer[boardId] = currPlayerValue;
    myTurn[boardId] = selfPlayerIDs.indexOf(currPlayerValue) != -1;

    // set styles
    // clear board
    $('[id^="' + boardId + '_p"]').removeClass('player-curr');
    // set new
    $('[id$="_p' + currPlayerValue + '"]').addClass('player-curr');

    // nowhere current player?
    var globalTurn = false;
    for (var thisBoardTurn in myTurn) {
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
    if (fString === undefined) {
        return undefined;
    }
    return fString.replace(/^board_/, "").replace(/_field/, "_");
}

function lengthenFieldString(fString) {
    if (fString === undefined) {
        return undefined;
    }
    return fString.replace(/_/, "_field").replace(/^/, "board_");
}

// handle click to "resign" button in UI
// send corresponding message to the server


function _resign(boardId) {
    var confirmed = $.prompt("Do you really want to resign?", {
        buttons: {
            Yes: true,
            No: false
        },
        focus: 1
    });
    if (confirmed) {
        game.send("end/" + mqId + "/resign/" + boardId);
    }
}

// handle click to "offer draw" button in UI
// send corresponding message to the server


function _offerDraw(boardId) {
    if (myTurn[boardId]) {
        _notify("You can only offer draw on your opponent's turn.");
        return;
    }
    var confirmed = confirm("Do you really want to offer a draw?", {
        buttons: {
            Yes: true,
            No: false
        },
        focus: 1
    });
    if (confirmed) {
        game.send("end/" + mqId + "/draw-offer/" + boardId);
    }
}

function _notify(message) {
    console.info(message);
    $.bar({
        'message': message,
        'position': 'bottom'
    });
}

function _fillPocket(position, content, board) {
    // TODO reenable
    // var pocketId = position=='top'?'1':'0';
    // var position = (position=='top' && !board.flipped) || (position=='bottom'
	// && board.flipped)?'top':'bottom';
    // var pocket = $('#' + position + '-pocket-board_' + board.id).empty();
    // for (var i=0; i<content.length; i++) {
    // var pieceDiv = board.getPieceDiv(content.charAt(i));
    // var fieldDiv = $('<div>').addClass('field').attr('id', 'board_' +
	// board.id + '_fieldp' + pocketId + i).append(pieceDiv);
    // add click events
    // _addEvents(fieldDiv, board);
    // pocket.append(fieldDiv);
    // }
}

function _parseBoardPlayers(players, targetBoard) {
    // format players: name:id,name:id/name:id,name:id
    var playerArray = players.toString().split(/[,\/]/);
    var myBoard = false;
    for (var i in playerArray) {
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
    position = (position == 'top' && !board.flipped) || (position == 'bottom' && board.flipped) ? 'top' : 'bottom';
    var playerHostDiv = $('#board_' + board.id + '-' + position + '-players').empty();
    var playerSplit = content.split(',');
    for (var i = 0; i < playerSplit.length; i++) {
        var playerData = playerSplit[i].split(':');
        var playerDiv = $('<div>').addClass('btn player').attr('id', board.id + '_p' + playerData[1]).html(playerData[0]).attr('title', playerData[1]); // [0]
																																						// = ID
        // add click events
        playerHostDiv.append(playerDiv);
        // highlight if it's yourself
        if (selfPlayerIDs.search(playerData[1]) !== -1) {
            playerDiv.addClass('player-me');
        }
    }
}


function parseMQ(data) {
    if (data === undefined || data === null || data === '') {
        return;
    }
    console.debug("Received message queue:\n" + JSON.stringify(data, null, '\t'));

    var mtype = data.mtype;
    switch (mtype) {
    case "move":
        silent = data.silent === true ? true : false; // TODO this needs a
														// fix. What does the
														// server send? Boolean
														// or string?
        boardId = data.from.replace(/_.*/, '');
        board = boardStorage.getBoard(boardId);
        board.move(lengthenFieldString(data.from) ,lengthenFieldString(data.to), data.toPiece, silent);
        _parseCurrPlayer(data.currP, boardId);
        // TODO add ['check'] in server and client -> play sound (don't set when
		// game is finished)
        break;
    case "movehist":
        addServerMessage(data.user + " played <b>" + data.str + "</b>");
        break;
    case "promote":
        boardId = data.from.replace(/_.*/, '');
        // get options, offer, get decision and resend move
        var selectionDiv = $('<div>').html('Select which piece to promote to:<br/><br/>');
        var counter = 0;
        for (var elem in data.options) {
            piece = data.options[elem];
            board = boardStorage.getBoard(boardId);
            pieceDiv = board.getPieceDiv(piece).addClass('promotion_piece');
            // add events
            pieceDiv.bind("click", {
                Param1: data.from,
                Param2: data.to,
                Param3: piece
            }, function(event) {
                var move = new Move(boardId, event.data.Param1, event.data.Param2, event.data.Param3);
                board.handleMoveInpu(move);
                // remove dialog
                $.modal.close();
            });
            counter++;
            // add to parent div
            selectionDiv.append(pieceDiv);
        }
        // call modally
        selectionDiv.css('minimum-height', board.pieceImg.width * counter).modal();
        break;
    case "chat":
        addChatMessage(data.user, decodeURIComponent(data.msg));
        playSound('media/chat-message');
        break;
    case "gameover":
        goMsg = "Game finished.\nResult: " + data.result + "\n" + data.msg;
        addServerMessage(goMsg);
        setTimeout(function() {
            $.prompt(goMsg);
        }, 1000);
        // TODO play sound
        break;
    case "gamesit":
        var j = -1;
        var clocksChanged = false;
        // save own IDs
        if (data.playerSelf !== undefined) {
            selfPlayerIDs = data.playerSelf;
        }
        while (true) {
            j++;
            // build the board
            try {
                var test = data[j].board_id;
            } catch (e) {
                break;
            }
            var boardId = data[j].board_id;
            var targetBoard = boardStorage.getBoard(boardId);
            if (data[j].board_size !== undefined) {
                boardSize = data[j].board_size.split('x');
                board = boardStorage.newBoard(boardId, boardSize[0], boardSize[1], data[j].flipped);
                // load the position
                board.loadFen(data[j].fen);
                // fix highlight
                board.highlightClear();
                if (data[j].lmove_from !== undefined && data[j].lmove_to !== undefined) {
                    board.highlight(lengthenFieldString(data[j].lmove_from), highlightType.LAST_MOVE);
                    board.highlight(lengthenFieldString(data[j].lmove_to), highlightType.LAST_MOVE);
                }
                targetBoard = board;
                targetBoard.pullStyles(); // also triggers .repaintFull()
            }
            if (data[j].players !== undefined) {
                var players = data[j].players.split('/');
                _parseBoardPlayers(players, targetBoard);
                _fillPlayers('top', players[1], targetBoard);
                _fillPlayers('bottom', players[0], targetBoard);
            }
            if (data[j].pockets !== undefined) {
                pockets = data[j].pockets.split('/');
                _fillPocket('top', pockets[1], targetBoard);
                _fillPocket('bottom', pockets[0], targetBoard);
            }
            if (data[j].capturePockets !== undefined) {
                // TODO implement filling (#27 on GitHub)
            }
            if (data[j].currP !== undefined) {
                // check if it's my turn
                _parseCurrPlayer(data[j].currP, boardId);
            }
            if (data[j].clocks !== undefined) {
                clocks = data[j].clocks.split(/[\/:]+/);
                // TODO time formatting
                $('#board_' + boardId + '-top-clock').data('time', clocks[targetBoard.flipped ? 0 : 2]).data('active', clocks[targetBoard.flipped ? 1 : 3] === "True");
                $('#board_' + boardId + '-bottom-clock').data('time', clocks[targetBoard.flipped ? 2 : 0]).data('active', clocks[targetBoard.flipped ? 3 : 1] === "True");
                clocksChanged = true;
            }
        }
        if (data.gameId !== undefined) {
            // add the appropriate link to the game's overview page
            $('#menu_game').children('a').attr('href', 'game.html?' + data.gameId);
        }
        if (clocksChanged) {
            _runClocks();
        }
        break;
    case "srvmsg":
        addServerMessage(data.msg);
        break;
    case "setname":
        $('[id$="_p' + data.id + '"]').html(data.name);
        break;
    case "draw-offer":
        var confirmed = confirm("Your opponent is offering a draw. Do you accept?", {
            buttons: {
                Yes: true,
                No: false
            },
            focus: 1
        });
        if (confirmed) {
            game.send("end/" + mqId + "/draw-offer");
        }
        break;
    case "alert":
        _notify(data.msg);
        break;
    }
}


function _runClocks() {
    var now = new Date();
    var nowTime = now.getTime();

    window.clearTimeout(clickTimeoutId);

    var allClocks = $('[id*="-clock"]');
    _updateClocks(allClocks, false);

    runningClocks = $(allClocks).filter(function() {
        return $(this).data('active');
    }).each(function() {
        $(this).data('started', nowTime);
    });
    _updateClocks(runningClocks, true);
}

function _updateClocks(targets, events) {
    var nextUpdate = 5000;
    var now = new Date();
    var nowTime = now.getTime();
    $(targets).each(function() {
        nextUpdate = Math.min(nextUpdate, _paintClock($(this), nowTime));
    });

    // set event for next update
    if (events && targets.length > 0) {
        clickTimeoutId = window.setTimeout(function() {
            _updateClocks(targets, true);
        }, nextUpdate);
    }
}

function _paintClock(elem, nowTime) {
    var unparsed = parseFloat($(elem).data('time'));
    if (isNaN(unparsed)) {
        return Number.MAX_VALUE;
    }

    // unlimited time?
    if (unparsed === 86400) {
        $(elem).html('').attr('title', 'No active time limit.');
    }

    var timePassed;
    if ($(elem).data('active') === false) {
        timePassed = 0;
    } else {
        timePassed = nowTime - $(elem).data('started');
    }
    unparsed -= timePassed / 1000;

    var negative = false;
    if (unparsed < 0) {
        negative = true;
        unparsed = -unparsed;
    }

    var hours = Math.floor(unparsed / 3600);
    var minutes = Math.floor((unparsed - 3600 * hours) / 60);
    var seconds = Math.floor(unparsed - 3600 * hours - 60 * minutes);
    var centiseconds = Math.floor((unparsed - 3600 * hours - 60 * minutes - seconds) * 100);

    var output = '';
    var timeout = 1000; // milliseconds
    // which stage?
    if (unparsed >= 60 * 10) { // ten or more minutes left -> minute-based
								// display
        output = hours + ':' + minutes;
        timeout = 5 * 1000;
    } else if (unparsed >= 30) { // 30 or more seconds left -> second-based
									// display
        output = hours > 0 ? (hours + ':') : '' + twoDigit(minutes) + ':' + twoDigit(seconds);
        timeout = 250;
    } else { // less than 30 seconds left -> as exact as possible
        output = minutes + ':' + twoDigit(seconds) + ',' + twoDigitBack(centiseconds);
        timeout = 50;
    }

    // set output
    var longOutput = 'Clock: {0} hours, {1} minutes, and {2}.{3} seconds left.'.format(hours, minutes, seconds, centiseconds);
    if (negative) {
        output = '-' + output;
        longOutput = 'Clock: expired since {0} hours, {1} minutes, and {2}.{3} seconds.'.format(hours, minutes, seconds, centiseconds);
    }
    $(elem).html(output).attr('title', longOutput);

    if (unparsed === 0) {
        // TODO possibly send message for server to check
        return Number.MAX_VALUE;
    }

    return timeout;
}

function twoDigit(number) {
    return (number < 10 ? '0' : '') + number;
}

function twoDigitBack(number) {
    return number + (number < 10 ? '0' : '');
}



function getPlayerName() {
    if (playerName !== undefined) {
        return playerName;
    }
    // search for saved old name
    try {
        var support = 'localStorage' in window && window.localStorage !== null;
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
        buttons: {
            Ok: true
        }
    });
}

function _lS_nameCallback(v, m, f) {
    an = m.children('#alertName');

    if (f.alertName === "") {
        an.css("border", "solid #ff0000 1px");
        return false;
    }
    playerName = f.alertName; // save globally
    window.localStorage.setItem('jazzy-player-name', playerName);
    return true;
}


function _makeFullscreen(id) {
	var elem = $('#' + id).get(0);
	if (elem.requestFullScreen) {  
		elem.requestFullScreen();  
	} else if (elem.mozRequestFullScreen) {  
		elem.mozRequestFullScreen();  
	} else if (elem.webkitRequestFullScreen) {  
		elem.webkitRequestFullScreen();  
	}
}


/* minimal templating functions */

function _getTemplate(selector) {
    var templateSource = $('#board-templates');
    return templateSource.find(selector).clone(false);
}

function _replaceInTemplate(element, from, to) {
    var regexp = new RegExp(from, 'g');
    element.html(element.html().replace(regexp, to));
    element.attr('id', element.attr('id').replace(regexp, to));
    return element;
}


// Move class
function Move(boardId, from, to, promotion, special) {
    this.boardId = boardId;
    this.from = from;
    this.to = to;
    this.promotion = promotion;
    this.special = special;
}

Move.prototype.send = function() {
	// post move to server and wait for message queue containing it (means move
	// was okay)!
	var from = this.boardId + '_' + this.from;
	var to = this.boardId + '_' + this.to;
    var url = 'post/' + mqId + '/move/' + from + '/' + to;
    url += '/' + (this.promotion === undefined?'':this.promotion);
    url += '/' + (this.special === true?'true':'false');
    game.send(url);
}



// convience methods

function isArray(obj) {
    return (typeof(obj.length) == "undefined") ? false : true;
}

// Inspired by http://bit.ly/juSAWl
// Augment String.prototype to allow for easier formatting. This implementation
// doesn't completely destroy any existing String.prototype.format functions,
// and will stringify objects/arrays.
String.prototype.format = function(i, safe, arg) {

    function format() {
        var str = this,
            len = arguments.length + 1;

        // For each {0} {1} {n...} replace with the argument in that position.
		// If
        // the argument is an object or an array it will be stringified to JSON.
        for (i = 0; i < len; arg = arguments[i++]) {
            safe = typeof arg === 'object' ? JSON.stringify(arg) : arg;
            str = str.replace(RegExp('\\{' + (i - 1) + '\\}', 'g'), safe);
        }
        return str;
    }

    // Save a reference of what may already exist under the property native.
    // Allows for doing something like: if("".format.native) { /* use native */
	// }
    format.native = String.prototype.format;

    // Replace the prototype property
    return format;
}();


if (typeof console.log == "object" && Function.prototype.bind && console) {
    ["log", "debug", "info", "warn", "error", "assert", "dir", "clear", "profile", "profileEnd"].forEach(function(method) {
        console[method] = this.call(console[method], console);
    }, Function.prototype.bind);
}
