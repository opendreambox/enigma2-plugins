var dreamboxWebSocket = (function() {
	"use strict";
	var _ws = null;
	var _requestMap = {};
	var _requestID = 0;
	var _streamSession = userprefs.data["stream_session"];
	var _sessionValid = userprefs.data["stream_session"] != undefined;
	var _baseUrl = window.location.hostname + ":" + window.location.port;

	var _authenticationRequest = function() {};
	var _readyCallback = function() {};
	var _closeCallback = function() {};

	function connectInternal(authCb, readyCb, closeCb) {
		_authenticationRequest = authCb;
		_readyCallback = readyCb;
		_closeCallback = closeCb;
		reconnectInternal();
	}

	function reconnectInternal() {
		var protocol = window.location.protocol.startsWith("https") ? "wss" : "ws";
		var port = window.location.port;
		if (Number.parseInt(port) == Number.NaN) //no port value set for locations using the default port
			port = protocol ==  "ws" ? 80 : 443;
		var uri = protocol + "://" + window.location.hostname + ":" + port + "/ws";
		_ws = new WebSocket(uri);
		_ws.onmessage = onMessageInternal.bind(this);
		_ws.onclose = onCloseInternal.bind(this);
		_ws.onerror = onErrorInternal.bind(this);
	}

	function onCloseInternal(event) {
		if (!event.wasClean)
			reconnectInternal();
		_closeCallback(event);
	}

	function onErrorInternal(event) {
		console.log(event);
	}

	function disconnectInternal() {
		if (_ws == null)
			return;
		_ws.close();
		_ws = null;
	}

	function onMessageInternal(msg) {
		var data = JSON.parse(msg.data)
		console.log(data);
		if (data.type == "auth_ok") {
			_streamSession = data.session;
			userprefs.data["stream_session"] = _streamSession;
			userprefs.save();
			_sessionValid = true;
			_readyCallback();
			return;
		} else if (data.type == "auth_required") {
			if (_sessionValid && _streamSession != null) {
				callFunctionInternal("auth", {"session" : _streamSession}, function(data){});
				_sessionValid = false;
				_streamSession = null;
			} else {
				_authenticationRequest();
			}
		} else if (data.type == "result") {
			var callback = _requestMap[data.id]
			if (callback == undefined)
				return;
			callback(data);
			delete _requestMap[data.id];
		}
	}

	function callFunctionInternal(type, data, callback) {
		_requestID++;
		data["type"] = type;
		data["id"] = _requestID;
		console.log(data);
		_requestMap[_requestID] = callback;
		_ws.send(JSON.stringify(data));
		return _requestID;
	}

	return {
		connect : connectInternal,
		disconnect : disconnectInternal,
		callFunction : callFunctionInternal,
		streamSession : _streamSession
	}
})();

var dreamboxPlayer = (function() {
	"use strict";
	var _hls = null;
	var _currentBouquet = null;
	var _currentService = null;
	var _pendingService = null;
	var _streamHost = 'http://' + window.document.location.host + ':8080';
	// StreamServerSeek start
	if (window.location.href.match(/sss-vod$/)) {
		var _streamHost = 'http://' + window.document.location.host + '/streamserverseek/proxy';
	}
	// StreamServerSeek end

	var _videoElement = document.getElementById('video');

	var _dialogLogin = null;
	var _dialogBitrates = null;

	var _streamSettings = {};

	function startInternal() {
		/* reload bouquet when drawer is opened via button */
		var drawerBtn = document.querySelector('.mdl-layout__drawer-button');
		drawerBtn.addEventListener('click', function(event) {
			if (_currentBouquet != null)
				loadBouquetInternal(_currentBouquet);
		});
		setupDialogs();
		dreamboxWebSocket.onAuthenticationRequired = onAuthenticationRequired
		dreamboxWebSocket.connect(onAuthenticationRequired, onReady, onDisconnect);
	}

	function setupDialogs() {
		_dialogLogin = document.querySelector('#login_dialog');
		if (!_dialogLogin.showModal) {
			dialogPolyfill.registerDialog(_dialogLogin);
		}
		_dialogLogin.querySelector('.send').addEventListener('click', function(event) {
			dreamboxPlayer.login();
			return false;
		});
		var loginForm = _dialogLogin.querySelector('#login_form');

		_dialogBitrates = document.querySelector('#bitrate_dialog');
		var showDialogButton = document.querySelector('#button-bitrates');
		if (!_dialogBitrates.showModal) {
			dialogPolyfill.registerDialog(_dialogBitrates);
		}
		showDialogButton.addEventListener('click', showBitrateSettings);
		_dialogBitrates.querySelector('.close').addEventListener('click', function() {
			_dialogBitrates.close();
		});
		_dialogBitrates.querySelector('.ok').addEventListener('click', function() {
			var audioBitrateE = document.getElementById("audioBitrate");
			var videoBitrateE = document.getElementById("videoBitrate");
			applyBitrates(audioBitrateE.value,videoBitrateE.value);
			_dialogBitrates.close();
		});
	}

	function loadStreamSettings() {
		dreamboxWebSocket.callFunction("get_stream_settings", {}, onStreamSettingsReady.bind(this))
	}

	function onStreamSettingsReady(response) {
		if (!response.success) {
			notify("Error loading stream settings!");
			return;
		}
		_streamSettings = response.result;
		var videoBitrateE = document.getElementById("videoBitrate");
		videoBitrateE.value = _streamSettings.videoBitrate;
		videoBitrateE.parentElement.classList.add("is-dirty");

		var audioBitrateE = document.getElementById("audioBitrate");
		audioBitrateE.value = _streamSettings.audioBitrate;
		audioBitrateE.parentElement.classList.add("is-dirty");
	}

	function showBitrateSettings() {
		loadStreamSettings();
		_dialogBitrates.showModal();
	}

	function onAuthenticationRequired() {
		_dialogLogin.showModal();
	}

	function loginInternal() {
		var user = _dialogLogin.querySelector("#login_user").value;
		var pass = _dialogLogin.querySelector("#login_pass").value;
		var token = btoa(user + ":" + pass);
		dreamboxWebSocket.callFunction("auth", {"token" : token}, onLoginResult);
	}

	function onLoginResult(result) {
		var loginContainer = _dialogLogin.querySelector('#login_container');
		var classes = loginContainer.classList;
		if (result.success) {
			if (classes.contains('is-invalid'))
				classes.remove('is-invalid');
		} else {
			if (!classes.contains('is-invalid'))
				classes.add('is-invalid');
		}
	}

	function onReady() {
		notify("Welcome!");
		if (_dialogLogin.open)
			_dialogLogin.close();
		loadStreamSettings();
		loadServicesInternal(); // List of TV Bouquets
		// StreamServerSeek start
		if (window.location.href.match(/sss-vod$/)) {
			_streamHost = 'http://' + window.document.location.host + '/streamserverseek/vod';
			playInternal();
			$('.plyr__progress').css('visibility', 'visible');
			if (window.history.pushState)
				window.history.replaceState({}, document.title, '/stream/');
			$('.mdl-snackbar__text').html('StreamServerSeek - Loading...');
		}
		// StreamServerSeek end
	}

	function onDisconnect(event) {
		if (!event.wasClean) {
			notify("Reconnecting...", 1000);
		} else {
			notify("Connection Lost - " + event.reason + " (" + event.code + ")", 1000);
		}
		console.log(event);
	}

	function setupHls() {
		var config = {
			xhrSetup : function(xhr, url) {
				xhr.withCredentials = true; // do send cookies
				//xhr.setRequestHeader("X-Stream-Session", dreamboxWebSocket.streamSession);
			},
			autoStartLoad : true,
			startPosition : -1,
			capLevelToPlayerSize : false,
			debug : true /*,
			liveSyncDurationCount : 3,
			liveMaxLatencyDurationCount : 6,
			initialLiveManifestSize : 1,
			maxBufferLength : 30,
			maxMaxBufferLength : 600,
			maxBufferSize : 60 * 1000 * 1000,
			maxBufferHole : 0.5,
			lowBufferWatchdogPeriod : 0.5,
			highBufferWatchdogPeriod : 3,
			nudgeOffset : 0.1,
			nudgeMaxRetry : 3,
			maxFragLookUpTolerance : 0.2,
			*/
		};
		// StreamServerSeek start
		config.maxMaxBufferLength = 15;
		// StreamServerSeek end
		_hls = new Hls(config);

		var url = _streamHost + '/stream.m3u8';
		_hls.loadSource(url);
		_hls.attachMedia(_videoElement);
		// StreamServerSeek start
		$('.plyr__progress input').change(function(){
			_hls.currentLevel = -1; // clear buffer, so segments will be redownloaded - otherwise streamserverseek doesn't know where to seek to
			notify('StreamServerSeek - Seeking...');
		});
		// StreamServerSeek end
		_hls.on(Hls.Events.MANIFEST_PARSED, function() {
			_videoElement.play();
		});
	}

	function notify(message, timeout) {
		var snackbarContainer = document.querySelector('#snackbar');
		var data = {'message' : message};
		if (timeout != undefined)
			data['timeout'] = timeout;
		snackbarContainer.MaterialSnackbar.showSnackbar(data);
	}

	function changeServiceResponse(response) {
		if (this.readyState == 4 && this.status == 200) {
			var res = JSON.parse(this.responseText);
			console.log(res)
			if (!res.result) {
				_pendingService = _currentService;
			}
		}
	}

	function changeService(reference) {
		_currentService = reference;
		console.log(reference);
		var url = 'http://' + window.document.location.host + ':8080/api.json?ref=' + encodeURIComponent(reference);
		var request = new XMLHttpRequest();
		request.addEventListener("readystatechange", changeServiceResponse);
		request.overrideMimeType('application/json');
		request.open("GET", url);
		request.send();
	}

	function changeBitrateResponse(response) {
		if (this.readyState == 4 && this.status == 200) {
			var res = JSON.parse(this.responseText);
			console.log(res)
			if (res.result) {
				notify("New bitrates applied!");
			} else {
				notify("Could not apply new bitrates!");
			}
		}
	}

	function applyBitrates(audioBitrate, videoBitrate) {
		var ab = Number.parseInt(audioBitrate);
		var vb = Number.parseInt(videoBitrate);
		if (ab == Number.NaN || vb == Number.NaN) {
			notify("Invalid Bitrate value!");
			return;
		}
		_streamSettings.audioBitrate = ab;
		_streamSettings.videoBitrate = vb;
		var url = 'http://' + window.document.location.host + ':8080/api.json?audio_bitrate=' + encodeURIComponent(audioBitrate) + '&video_bitrate=' + encodeURIComponent(videoBitrate);
		var request = new XMLHttpRequest();
		request.addEventListener("readystatechange", changeBitrateResponse);
		request.overrideMimeType('application/json');
		request.open("GET", url);
		request.send();
	}

	function onMetadataReady() {
		if (_pendingService != null) {
			changeService(_pendingService);
			_pendingService = null;
		}
	}

	function playInternal(reference) {
		notify("Stream is loading...", 6000);
		// use native where possible
		if (_videoElement.canPlayType('application/vnd.apple.mpegurl')) {
			_videoElement.src = _streamHost + '/stream.m3u8';
			_videoElement.addEventListener('canplay', function() {
				_videoElement.play();
			});
		} else if (Hls.isSupported()) {
			if (_hls == null)
				setupHls();
			_videoElement.play();
			// fallback to hls.js
		} else {
			notify("Sorry, your browser seems to be too old for this type of stream!");
			return;
		}
		if (reference != undefined)
			changeService(reference);
	}

	function onServiceClick(event) {
		// StreamServerSeek start
		if (_streamHost.match(/vod$/)) {
			_streamHost = 'http://' + window.document.location.host + '/streamserverseek/proxy';
			if (_hls != null) {
				_hls.loadSource(_streamHost + '/stream.m3u8');
				_hls.attachMedia(_videoElement);
			}
			$('.plyr__progress').css('visibility', 'hidden');
		}
		// StreamServerSeek end
		var ref = event.target.getAttribute("data-reference");
		if (ref == null)
			ref = event.target.parentElement.getAttribute("data-reference");
		playInternal(ref);
		toggleDrawer();
	}

	function toggleDrawer() {
		var layout = document.querySelector('.mdl-layout');
		layout.MaterialLayout.toggleDrawer();
	}

	function onBouquetClick(event) {
		var ref = event.target.getAttribute("data-reference");
		if (ref == null)
			ref = event.target.parentElement.getAttribute("data-reference");
		loadBouquetInternal(ref);
		toggleDrawer();
	}

	function fillServiceList(data) {
		var parent = document.getElementById('services');
		parent.innerHTML = null;
		var result = data.result;
		var bouquetElement = document.getElementById('menu-bouquet')
		bouquetElement.innerHTML = result.name;

		result.data.forEach(function(evt) {
			var a = document.createElement('a');
			a.href = "#" + evt.reference;
			a.setAttribute('data-reference', evt.reference);
			a.className = 'mdl-navigation__link';
			a.style = "text-align: left;";
			var span = document.createElement('div');
			var textNode = document.createTextNode(evt.name);
			span.appendChild(textNode);
			span.className = "mdl-typography--title";
			componentHandler.upgradeElement(span);
			a.appendChild(span);

			if (evt.title != null) {
				span = document.createElement('div');
				textNode = document.createTextNode(evt.title);
				span.appendChild(textNode);
				componentHandler.upgradeElement(span);
				a.appendChild(span);
			}
			componentHandler.upgradeElement(a);
			parent.appendChild(a)
			a.onclick = onServiceClick;
		});
	}

	function fillBouquetList(data) {
		var parent = document.getElementById('bouquets');
		parent.innerHTML = null;
		var result = data.result;
		var ref = null;
		result.data.forEach(function(service) {
			if (ref == null)
				ref = service.reference;
			var a = document.createElement('a');
			a.href = '#';
			a.className = 'mdl-button mdl-js-button mdl-js-ripple-effect';
			a.style = 'color: white';
			a.setAttribute('data-reference', service.reference);
			a.onclick = onBouquetClick;
			var textNode = document.createTextNode(service.name);
			a.appendChild(textNode);
			componentHandler.upgradeElement(a);
			parent.appendChild(a)
		});
		loadBouquetInternal(ref); // Favorites TV
	}

	function loadServicesInternal(reference) {
		if (reference == undefined || reference == null) // TV Bouquets as default
			reference = "1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195) FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet";
		dreamboxWebSocket.callFunction("get_services", {"reference" : reference}, fillBouquetList);
	}

	function loadBouquetInternal(reference) {
		if (reference == undefined || reference == null)
			reference = "1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.favourites.tv\" ORDER BY bouquet";
		_currentBouquet = reference;
		dreamboxWebSocket.callFunction("get_epg_nownext", {
			"reference" : reference,
			which : 0 // now
		}, fillServiceList);
	}

	return {
		start : startInternal,
		login : loginInternal,
		loadBouquet : loadBouquetInternal,
		loadServices : loadServicesInternal
	}
})();
window.addEventListener('load', function() {
	dreamboxPlayer.start();
	const plyr = new Plyr('#video', {
		controls : [ 'play-large', 'play', 'mute', 'volume', 'settings', 'airplay', 'fullscreen', 'progress' ],
		settings : [ 'quality', 'speed' ],
		autoplay : true,
		disableContextMenu : false,
		displayDuration : false,
		fullscreen : {
			enabled : true,
			fallback : true,
			iosNative : false
		},
		iconUrl : window.location.protocol + '//' + window.location.hostname + '/stream/plyr.svg'
	});
});
