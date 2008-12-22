// $Header$

var doRequestMemory = new Object();
var doRequestMemorySave = new Object();

var templates = new Array();

var mediaPlayerStarted = false;

// Get Settings
var settings = null;
var parentControlList = null;

// UpdateStreamReader
var UpdateStreamReaderNextReadPos = 0;
var UpdateStreamReaderPollTimer = null;
var UpdateStreamReaderPollTimerCounter = 0;
var UpdateStreamReaderRetryCounter = 0;
var UpdateStreamReaderRetryLimit = 10
var UpdateStreamReaderRequest = null;

//var UpdateStreamReaderPollTimerCounterTwisted = 0;

function UpdateStreamReaderStart(){
	var ua = navigator.userAgent;
	
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		debug("UpdateStreamReader IE Fix");

		var namespace = { 	
					'url_updates': url_updates
		};
		$('UpdateStreamReaderIEFixPanel').innerHTML = RND(tplUpdateStreamReaderIE, namespace);
		
	}else {
		UpdateStreamReaderNextReadPos = 0;
		allMessages = "";
		UpdateStreamReaderRequest = new XMLHttpRequest();
		UpdateStreamReaderRequest.onerror = UpdateStreamReaderOnError;
		UpdateStreamReaderRequest.open("GET", url_updates, true);
 		UpdateStreamReaderRequest.send(null);
		UpdateStreamReaderPollTimer = setInterval(UpdateStreamReaderLatestResponse, 1000);
	}
}
  
function UpdateStreamReaderLatestResponse() {
	UpdateStreamReaderPollTimerCounter++;
	
	if(UpdateStreamReaderPollTimerCounter > 30) {
		clearInterval(UpdateStreamReaderPollTimer);
		UpdateStreamReaderRequest.abort();
		UpdateStreamReaderRequest = null;
		UpdateStreamReaderPollTimerCounter = 0;
		UpdateStreamReaderStart();
		
//		UpdateStreamReaderPollTimerCounterTwisted++;
		return;
	}
	var allMessages = UpdateStreamReaderRequest.responseText;
	do {
		var unprocessed = allMessages.substring(UpdateStreamReaderNextReadPos);
		var messageXMLEndIndex = unprocessed.indexOf("\n");
		
		if (messageXMLEndIndex!=-1) {
			//reset RetryCounter, if it was a reconnect, it succeeded!
			UpdateStreamReaderRetryCounter = 0;
			
			var endOfFirstMessageIndex = messageXMLEndIndex + "\n".length;
			var anUpdate = unprocessed.substring(0, endOfFirstMessageIndex);
	
			var re = new RegExp("<script>parent\.(.*)</script>");
			anUpdate = re.exec(anUpdate);

			if(anUpdate != null){
				if (anUpdate.length == 2){
					eval(anUpdate[1]);
				}
			}
			
			UpdateStreamReaderNextReadPos += endOfFirstMessageIndex;
		}
		if(UpdateStreamReaderNextReadPos > 65000){
			UpdateStreamReaderRequest.abort();
			UpdateStreamReaderRequest = null;
			UpdateStreamReaderPollTimerCounter = 0;
			UpdateStreamReaderStart();
			messageXMLEndIndex = -1;
		}
	} while (messageXMLEndIndex != -1);
}

function UpdateStreamReaderOnError(){
	window.clearInterval(UpdateStreamReaderPollTimer);
	UpdateStreamReaderRetryCounter += 1;
	
	debug("UpdateStreamReaderOnError: ErrorCount "+UpdateStreamReaderRetryCounter);
	
	if(UpdateStreamReaderRetryCounter >= UpdateStreamReaderRetryLimit){
		debug("UpdateStreamReaderOnError: RetryLimit reached!");
		
		UpdateStreamReaderRetryCounter = 0;
		
		Dialog.confirm(
			"Live Update Stream has an Error!<br><br>You will not receive any Updates from Enigma2.<br>Should I try to reconnect?",
			{	
				windowParameters: {width:300, className: windowStyle},
				okLabel: "reconnect",
				buttonClass: "myButtonClass",
				cancel: function(win) {debug("cancel confirm panel")},
				ok: function(win) {UpdateStreamReaderStart(); return true;}
			}
		);
	} else {
		setTimeout("UpdateStreamReaderStart()", 5000);
	}
}
//end UpdateStreamReader

//Popup And Messagebox Helpers
function setWindowContent(window, html){
	window.document.write(html);
	window.document.close();
}


function openPopup(title, html, width, height, x, y){
	debug("opening Window: "+title);
	
	var popup = window.open('about:blank',title,'scrollbars=yes, width='+width+',height='+height+',left='+x+',top='+y+',screenX='+x+',screenY='+y);
	try {
		setWindowContent(popup, html);
		return popup;
	} catch(e){
		alert("Please disable your Popup-Blocker for Enigma2 WebControl to work flawlessly!");
		return null;
	}
}
	
function messageBox(t, m){
	alert(m);
}


//Template Helpers
function fetchTpl(tplName, callback){
	url = "/webdata/tpl/"+tplName+".htm";
		new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o, e){ throw(e); },				
				onSuccess: function(request){
								saveTpl(request, tplName)
									if(callback != null){
										callback();
									}
							},
				onComplete: requestFinished 
			});
}

function saveTpl(request, tplName){
	templates[tplName] = request.responseText;
}


function processTpl(tplName, data, domElement, callback){
	url = "/webdata/tpl/"+tplName+".htm";
		new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o, e){ throw(e); },				
				onSuccess: function(request){
								renderTpl(request.responseText, data, domElement)
								if(callback != null) callback();
							},
				onComplete: requestFinished 
			});
}

function renderTpl(tpl, data, domElement) {
	var result = tpl.process(data);
	$(domElement).innerHTML = result;
}

var currentBouquet = bouquetsTv;
function getBouquetEpg(){
	loadServiceEPGNowNext(currentBouquet);
}

function d2h(nr, len){

		hex = parseInt(nr).toString(16).toUpperCase();
		if(len > 0){
			try{
				while(hex.length < len){
					hex = "0"+hex;
				}
			} 
			catch(e){}
		} 
		return hex;
}

function quotes2html(txt) {
	txt = txt.replace(/"/g, '&quot;');
	return txt.replace(/'/g, "\\\'");
}


//Debugging Window
var debugWin = '';

function loadAndOpenDebug(){
	fetchTpl('tplDebug', openDebug)
}

function openDebug(){
	debugWin = openPopup("Debug", templates['tplDebug'], 500, 300);
}

function debug(text){
	if(DBG){
		if(!debugWin.closed && debugWin.location){
			var inner = debugWin.document.getElementById('debugContent').innerHTML;
			debugWin.document.getElementById('debugContent').innerHTML = new Date().toLocaleString() + ": "+text+"<br>" + inner;
		} 
	}
}

function showhide(id){
 	o = $(id).style;
 	o.display = (o.display!="none")? "none":"";
}

function set(element, value){
	if(element == "CurrentService") {
		if(value.search(/^MP3 File:/) != -1) {
			value = value.replace(/.*\//, '');
		}
	}
	element = parent.$(element);
	if(value.length > 550) {
		value = value.substr(0,550) + "[...]";
	}
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		try{
			elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
			if(elementscript){
				elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
			}
		}
		catch(e){}
	}
}

function setComplete(element, value){
	//debug(element+"-"+value);
	element = parent.$(element);
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
		if(elementscript){
			elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
		}
	}
}
//AJAX Request Handling
// requestindikator
var requestcounter = 0;
function requestIndicatorUpdate(){
	/*debug(requestcounter+" open requests");
	if(requestcounter>=1){
		$('RequestIndicator').style.display = "inline";
	}else{
		$('RequestIndicator').style.display = "none";
	}*/
}

function requestStarted(){
	requestcounter +=1;
	requestIndicatorUpdate();
}

function requestFinished(){
	requestcounter -=1;
	requestIndicatorUpdate();
}

// end requestindikator
function doRequest(url, readyFunction, save){
	requestStarted();
	doRequestMemorySave[url] = save;
	debug("doRequest: Requesting: "+url);
/*	
	if(save == true && typeof(doRequestMemory[url]) != "undefined") {
		readyFunction(doRequestMemory[url]);
	} else {
*/
		debug("doRequest: loading");
		new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o,e){ throw(e); },				
				onSuccess: function (transport, json) {
							if(typeof(doRequestMemorySave[url]) != "undefined") {
								if(doRequestMemorySave[url]) {
									debug("doRequest: saving request"); 
									doRequestMemory[url] = transport;
								}
							}
							readyFunction(transport);
						},
				onComplete: requestFinished 
			});
//	}
}

function getXML(request){
	if (document.implementation && document.implementation.createDocument){
		var xmlDoc = request.responseXML
	}
	else if (window.ActiveXObject){
		var xmlInsert = document.createElement('xml');

		xmlInsert.setAttribute('innerHTML',request.responseText);
		xmlInsert.setAttribute('id','_MakeAUniqueID');
		document.body.appendChild(xmlInsert);
		xmlDoc = $('_MakeAUniqueID');
		document.body.removeChild($('_MakeAUniqueID'));
	} else {
		debug("Your Browser Sucks!");
	}
	return xmlDoc;
}

function parentPin(servicereference) {
    debug ("parentPin: parentControlList");
	servicereference = decodeURIComponent(servicereference);
	if(parentControlList == null || String(getSettingByName("config.ParentalControl.configured")) != "true") {
		return true;
	}
	//debug("parentPin " + parentControlList.length);
	if(getParentControlByRef(servicereference) == servicereference) {
		if(String(getSettingByName("config.ParentalControl.type.value")) == "whitelist") {
			debug("parentPin leaving here 1");
			return true;
		}
	} else {
		debug("parentPin leaving here 2");
		return true;
	}
	debug("going to ask for PIN");

	var userInput = prompt('ParentControll was switch on.<br> Please enter PIN','PIN');
	if (userInput != '' && userInput != null) {
		if(String(userInput) == String(getSettingByName("config.ParentalControl.servicepin.0")) ) {
			return true;
		} else {
			return parentPin(servicereference);
		}
	} else {
		return false;
	}
}

function zap(servicereference){
	new Ajax.Request( "/web/zap?sRef=" + servicereference, 
						{
							asynchronous: true,
							method: 'get'
						}
					);
	setTimeout("getSubServices()", 5000);
}

//++++       SignalPanel                           ++++
function openSignalDialog(){
	openPopup("Signal Info",tplSignalPanel, 215, 100,620,40);
}


//++++ EPG functions                               ++++
function loadEPGBySearchString(string){
		doRequest(url_epgsearch+escape(string),incomingEPGrequest, false);
}

function loadEPGByServiceReference(servicereference){
		doRequest(url_epgservice+servicereference,incomingEPGrequest, false);
}

var epgListData = {};
function incomingEPGrequest(request){
	debug("incoming request" +request.readyState);		
	if (request.readyState == 4){
		var EPGItems = new EPGList(getXML(request)).getArray(true);
		debug("have "+EPGItems.length+" e2events");
		if(EPGItems.length > 0){			
			var namespace = new Array();
			for (var i=0; i < EPGItems.length; i++){
				try{
					var item = EPGItems[i];				
					namespace[i] = {	
						'date': item.getTimeDay(),
						'eventid': item.getEventId(),
						'servicereference': item.getServiceReference(),
						'servicename': quotes2html(item.getServiceName()),
						'title': quotes2html(item.getTitle()),
						'titleESC': escape(item.getTitle()),
						'starttime': item.getTimeStartString(), 
						'duration': Math.ceil(item.getDuration()/60000), 
						'description': quotes2html(item.getDescription()),
						'endtime': item.getTimeEndString(), 
						'extdescription': quotes2html(item.getDescriptionExtended()),
						'number': String(i),
//						'extdescriptionSmall': quotes2html(item.getDescriptionExtended()),
						'start': item.getTimeBegin(),
						'end': item.getTimeEnd()
					};
					
				} catch (blubb) { debug("Error rendering: "+blubb);	}
			}
			
			epgListData = {epg : namespace};
			fetchTpl('tplEpgList', showEpgList);
		} else {
			messageBox('No Items found!', 'Sorry but I could not find any EPG Content containing your search value');
		}
	}
}

var EPGListWindow = '';

function showEpgList(){
	html = templates['tplEpgList'].process(epgListData);
	
	if (!EPGListWindow.closed && EPGListWindow.location) {
		setWindowContent(EPGListWindow, html);
	} else {
		EPGListWindow = openPopup("Electronic Program Guide", html, 900, 500,50,60);
	}
}

function extdescriptionSmall(txt,num) {
	if(txt.length > 410) {
		var shortTxt = txt.substr(0,410);
		txt = txt.replace(/\'\'/g, '&quot;');
		txt = txt.replace(/\\/g, '\\\\');
		txt = txt.replace(/\'/g, '\\\'');
		txt = txt.replace(/\"/g, '&quot;');
		var smallNamespace = { 'txt':txt,'number':num, 'shortTxt':shortTxt};
		return RND(tplEPGListItemExtend, smallNamespace);
	} else {
		return txt;
	}
}	

function loadServiceEPGNowNext(servicereference){
	var url = url_epgnow+servicereference;
	doRequest(url, incomingServiceEPGNowNext, false);
}

function incomingServiceEPGNowNext(request){
	if(request.readyState == 4){
		var epgevents = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
		for (var c=0; c < epgevents.length; c++){
			var epgEvt = new EPGEvent(epgevents.item(c));
			
			if (epgEvt.getEventId() != 'None'){
				buildServiceListEPGItem(epgEvt,"NOW");
			}
		}
	}
}

function buildServiceListEPGItem(epgevent, type){
	var e = $(type+epgevent.getServiceReference());
		try{
			var namespace = { 	
				'starttime': epgevent.getTimeStartString(), 
				'title': epgevent.getTitle(), 
				'length': Math.ceil(epgevent.duration/60) 
			};
			var data = {epg : namespace};
			//e.innerHTML = RND(tplServiceListEPGItem, namespace);
			
			if(templates['tplServiceListEPGItem'] != null){
				renderTpl(templates['tplServiceListEPGItem'], data, type + epgevent.getServiceReference());
			} else {
				debug("EPGItem: tplServiceListEPGItem N/A");
			}
		} catch (e) {
			debug("EPGItem: Error rendering: " + e);
		}	
}



//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ GUI functions                               ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

var currentBodyMainElement = null

function setBodyMainContent(domId){
	domElement =$(domId);
	if(currentBodyMainElement != null){
		currentBodyMainElement.style.display = "none";		
	}
	domElement.style.display = "";
	currentBodyMainElement = domElement;
}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ volume functions                            ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

function initVolumePanel(){
	getVolume(); 
}

function getVolume(){
	doRequest(url_getvolume, handleVolumeRequest, false);
}

function volumeSet(val){
	doRequest(url_setvolume+val, handleVolumeRequest, false);
}

function volumeUp(){
	doRequest(url_volumeup, handleVolumeRequest, false);
}

function volumeDown(){
	doRequest(url_volumedown, handleVolumeRequest, false);
}

function volumeMute(){
	doRequest(url_volumemute, handleVolumeRequest, false);
}

function handleVolumeRequest(request){
	if (request.readyState == 4) {
		var b = getXML(request).getElementsByTagName("e2volume");
		var newvalue = b.item(0).getElementsByTagName('e2current').item(0).firstChild.data;
		var mute = b.item(0).getElementsByTagName('e2ismuted').item(0).firstChild.data;
		debug("volume"+newvalue+";"+mute);
		
		for (var i = 1; i <= 10; i++)		{
			if ( (newvalue/10)>=i){
				$("volume"+i).src = "/webdata/img/led_on.png";
			}else{
				$("volume"+i).src = "/webdata/img/led_off.png";
			}
		}
		if (mute == "False"){
			$("speaker").src = "/webdata/img/speak_on.png";
		}else{
			$("speaker").src = "/webdata/img/speak_off.png";
		}
	}    	
}

var bouquetsMemory = new Object();

function initChannelList(){
	//debug("init ChannelList");	
	var url = url_getServices+encodeURIComponent(bouquetsTv);
	currentBouquet = bouquetsTv;
	doRequest(url, incomingBouquetListInitial, true);
}


var loadedChannellist = new Object();
function loadBouquet(servicereference, name){ 
	debug("loading bouquet with "+servicereference);

	currentBouquet = servicereference;
	
	
	setContentHd(name);
	setAjaxLoad('contentMain');
	
	debug("loadBouquet " + typeof(loadedChannellist[servicereference]));
	if(typeof(loadedChannellist[servicereference]) == "undefined") {
		doRequest(url_getServices+servicereference, incomingChannellist, true);
	} else {
		incomingChannellist();
	}
}

function incomingBouquetListInitial(request){
	if (request.readyState == 4) {
		var list0 = new ServiceList(getXML(request)).getArray();
		debug("have "+list0.length+" TV Bouquet ");	

		//loading first entry of TV Favorites as default for ServiceList
		loadBouquet(list0[0].getServiceReference(), list0[0].getServiceName());

		bouquetsMemory["bouquetsTv"] = list0;
	}
}

function incomingBouquetList(request){
	if (request.readyState == 4) {
		var list0 = new ServiceList(getXML(request)).getArray();
		debug("have "+list0.length+" TV Bouquet ");	
		renderBouquetTable(list0, 'contentMain');
	}
}

function renderBouquetTable(list, target){
	debug("renderBouquetTable with "+list.length+" Bouquets");	
	
	var namespace = new Array();
	if (list.length < 1) alert("NO BOUQUETS!");
	for (var i=0; i < list.length; i++){
		try{
			var bouquet = list[i];
			namespace[i] = {
				'servicereference': bouquet.getServiceReference(), 
				'bouquetname': bouquet.getServiceName()
			};
		} catch (blubb) { alert("Error rendering!"); }
	}
	var data = { 
		services : namespace 
	};
	
	processTpl('tplBouquetList', data, 'contentMain');
}	

function incomingChannellist(request){
	var services = null;
	if(request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		debug("got "+services.length+" Services");
	}
	if(services != null) {
		var namespace = new Array();
		for ( var i = 0; i < services.length ; i++){
			var service = services[i];
			namespace[i] = { 	
				'servicereference': service.getServiceReference(),
				'servicename': service.getServiceName()
			};
		}
		var data = { 
			services : namespace 
		};
		
		processTpl('tplServiceList', data, 'contentMain', getBouquetEpg);

	}
}

// Movies
function loadMovieList(tag){
	debug("loading movies by tag '"+tag+"'");
	if(typeof(tag) == 'undefined'){
		tag = '';
	}
	doRequest(url_movielist+tag, incomingMovieList, false);
}

function incomingMovieList(request){
	if(request.readyState == 4){
		var movies = new MovieList(getXML(request)).getArray();
		debug("have "+movies.length+" movies");
		namespace = new Array();	
		for ( var i = 0; i < movies.length; i++){
			var movie = movies[i];
			namespace[i] = { 	
				'servicereference': movie.getServiceReference(),
				'servicename': movie.getServiceName() ,
				'title': movie.getTitle(), 
				'description': movie.getDescription(), 
				'descriptionextended': movie.getDescriptionExtended(),
				'filelink': String(movie.getFilename()).substr(17,movie.getFilename().length),
				'filename': String(movie.getFilename()),
				'filesize': movie.getFilesizeMB(),
				'tags': movie.getTags().join(', ') ,
				'length': movie.getLength() ,
				'time': movie.getTimeDay()+"&nbsp;"+ movie.getTimeStartString()
			};
		}
		data = { movies : namespace }
		processTpl('tplMovieList', data, 'contentMain');
	}		
}

function delMovieFile(file,servicename,title,description) {
	debug("delMovieFile: file("+file+"),servicename("+servicename+"),title("+title+"),description("+description+")");
	var result = confirm(
		"Selected timer:\n"
		+"Servicename: "+servicename+"\n"
		+"Title: "+title+"\n"
		+"Description: "+description+"\n"
		+"Are you sure that you want to delete the Timer?"
	);

	if(result){
		debug("delMovieFile ok confirm panel"); 
		doRequest(url_moviefiledelete+"?filename="+file, incomingDelMovieFileResult, false); 
		return true;
	}
	else{
		debug("delMovieFile cancel confirm panel");
		return false;
	}
}

function incomingDelMovieFileResult(request) {
	debug("incomingDelMovieFileResult");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		if(delresult.getState()){
			loadMovieList('');
		}else{
			messageBox("Deletion Error","Reason: "+delresult.getStateText());
		}
	}		
}


// send Messages
function showMessageSendForm(){
		$('BodyContent').innerHTML = tplMessageSendForm;
}

var MessageAnswerPolling;
function sendMessage(messagetext,messagetype,messagetimeout){
	if(!messagetext){
		messagetext = $('MessageSendFormText').value;
	}	
	if(!messagetimeout){
		messagetimeout = $('MessageSendFormTimeout').value;
	}	
	if(!messagetype){
		var index = $('MessageSendFormType').selectedIndex;
		messagetype = $('MessageSendFormType').options[index].value;
	}	
	if(ownLazyNumber(messagetype) == 0){
		new Ajax.Request(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, { asynchronous: true, method: 'get' });
		MessageAnswerPolling = setInterval(getMessageAnswer, ownLazyNumber(messagetimeout)*1000);
	} else {
		doRequest(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult, false);
	}
}

function incomingMessageResult(request){

	if(request.readyState== 4){
		var b = getXML(request).getElementsByTagName("e2message");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
		if (result=="True"){
			messageBox('Message sent: ' + resulttext);//'message send successfully! it appears on TV-Screen');
		}else{
			messageBox('Message NOT sent: ' + resulttext);
		}
	}		
}

function getMessageAnswer() {
	doRequest(url_messageanswer, incomingMessageResult, false);
	clearInterval(MessageAnswerPolling);
}

// RemoteControl Code
function loadAndOpenWebRemote(){
	fetchTpl('tplWebRemote', openWebRemote);
}

var webRemoteWindow = '';
function openWebRemote(){
	
	if (!webRemoteWindow.closed && webRemoteWindow.location) {
		setWindowContent(webRemoteWindow, templates['tplWebRemote']);
	} else {
		webRemoteWindow = openPopup('WebRemote', templates['tplWebRemote'], 250, 640);
	}
	
}

function sendRemoteControlRequest(command){
	doRequest(url_remotecontrol+'?command='+command, incomingRemoteControlResult, false);
//	if($('getScreen').checked) {
//		openGrabPicture();
//	}
}

function openGrabPicture() {
	if($('BodyContent').innerHTML != tplRCGrab) {
		$('BodyContent').innerHTML = tplRCGrab;
	}
	debug("openGrabPicture");
	var buffer = new Image();
	var downloadStart;

	buffer.onload = function () { debug("image zugewiesen"); $('grabPageIMG').src = buffer.src; return true;};
	buffer.onerror = function (meldung) { debug("reload grab image failed"); return true;};

	downloadStart = new Date().getTime();
	buffer.src = '/grab?' + downloadStart;
	$('grabPageIMG').height(400);
	tplRCGrab = $('BodyContent').innerHTML;
}

function incomingRemoteControlResult(request){
	if(request.readyState == 4){
		var b = getXML(request).getElementsByTagName("e2remotecontrol");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
	} else {
		$('rcWindow').innerHTML = "<h1>some unknown error</h1>" + tplRemoteControlForm;
	}
}

function getDreamboxSettings(){
	doRequest(url_settings, incomingGetDreamboxSettings, false);
}

function incomingGetDreamboxSettings(request){
	if(request.readyState == 4){
		settings = new Settings(getXML(request)).getArray();
	}
	debug ("starte getParentControl " + getSettingByName("config.ParentalControl.configured"));
	if(String(getSettingByName("config.ParentalControl.configured")) == "true") {
		getParentControl();
	}
}

function getSettingByName(txt) {
	debug("getSettingByName ("+txt+")");
	for(i = 0; i < settings.length; i++) {
		debug("("+settings[i].getSettingName()+") (" +settings[i].getSettingValue()+")");
		if(String(settings[i].getSettingName()) == String(txt)) {
			return settings[i].getSettingValue().toLowerCase();
		} 
	}
	return "";
}

function getParentControl() {
	doRequest(url_parentcontrol, incomingParentControl, false);
}

function incomingParentControl(request) {
	if(request.readyState == 4){
		parentControlList = new ServiceList(getXML(request)).getArray();
		debug("parentControlList got "+parentControlList.length + " services");
	}
}

function getParentControlByRef(txt) {
	debug("getParentControlByRef ("+txt+")");
	for(i = 0; i < parentControlList.length; i++) {
		debug("("+parentControlList[i].getClearServiceReference()+")");
		if(String(parentControlList[i].getClearServiceReference()) == String(txt)) {
			return parentControlList[i].getClearServiceReference();
		} 
	}
	return "";
}

function ownLazyNumber(num) {
	if(isNaN(num)){
		return 0;
	} else {
		return Number(num);
	}
}

function getSubServices() {
	doRequest(url_subservices,incomingSubServiceRequest, false);
}

//var SubServicePoller = setInterval(getSubServices, 15000);
var subServicesInsertedList = new Object();

function incomingSubServiceRequest(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		debug("got "+services.length+" SubServices");
		
		if(services.length > 1) {
			
			first = services[0];
			var mainChannellist = loadedChannellist[String($('mainServiceRef').value)];

			last = false
			var namespace = new Array();
			
			//we already have the main service in our servicelist so we'll start with the second element
			for ( var i = 1; i < services.length ; i++){
				var reference = services[i];
				namespace[i] = { 	
					'servicereference': reference.getServiceReference(),
					'servicename': reference.getServiceName()
				};
			}
			data = { subs : namespace };
			
			//TODO 'tplSubServices'
			processTpl('tplSubServices', data, $('SUB'+first.getServiceReference));
			
			subServicesInsertedList[String(first.getServiceReference())] = services;
			loadedChannellist[$('mainServiceRef').value] = mainChannellist;
		}
	}
}

// Array.insert( index, value ) - Insert value at index, without overwriting existing keys
Array.prototype.insert = function( j, v ) {
	if( j>=0 ) {
		var a = this.slice(), b = a.splice( j );
		a[j] = v;
		return a.concat( b );
	}
}

// Array.splice() - Remove or replace several elements and return any deleted elements
if( typeof Array.prototype.splice==='undefined' ) {
	Array.prototype.splice = function( a, c ) {
		var i = 0, e = arguments, d = this.copy(), f = a, l = this.length;
	
		if( !c ) { 
			c = l - a; 
		}
		
		for( i; i < e.length - 2; i++ ) { 
			this[a + i] = e[i + 2]; 
		}
		
		for( a; a < l - c; a++ ) { 
			this[a + e.length - 2] = d[a - c]; 
		}
		this.length -= c - e.length + 2;
	
		return d.slice( f, f + c );
	};
}

function writeTimerListNow() {
	new Ajax.Request( url_timerlistwrite, { asynchronous: true, method: 'get' });
}

function recordingPushed() {
	doRequest(url_timerlist, incomingRecordingPushed, false);
}

function incomingRecordingPushed(request) {
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		
		var aftereventReadable = new Array ('Nothing', 'Standby', 'Deepstandby/Shutdown');
		var justplayReadable = new Array('record', 'zap');
		var OnOff = new Array('on', 'off');
		
		var namespace = new Array();
		
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];

			if(ownLazyNumber(timer.getDontSave()) == 1) {
				var beginDate = new Date(Number(timer.getTimeBegin())*1000);
				var endDate = new Date(Number(timer.getTimeEnd())*1000);
				namespace[i] = {
				'servicereference': timer.getServiceReference(),
				'servicename': timer.getServiceName() ,
				'title': timer.getName(), 
				'description': timer.getDescription(), 
				'descriptionextended': timer.getDescriptionExtended(), 
				'begin': timer.getTimeBegin(),
				'beginDate': beginDate.toLocaleString(),
				'end': timer.getTimeEnd(),
				'endDate': endDate.toLocaleString(),
				'state': timer.getState(),
				'duration': Math.ceil((timer.getDuration()/60)),
				'repeated': timer.getRepeated(),
				'repeatedReadable': repeatedReadable(timer.getRepeated()),
				'justplay': timer.getJustplay(),
				'justplayReadable': justplayReadable[Number(timer.getJustplay())],
				'afterevent': timer.getAfterevent(),
				'aftereventReadable': aftereventReadable[Number(timer.getAfterevent())],
				'disabled': timer.getDisabled(),
				'onOff': OnOff[Number(timer.getDisabled())],
				'color': colorTimerListEntry( timer.getState() )
				};
			}
		}
		data = { recordings : namespace };
		openPopup("Record Now", 'tplTimerListItem', data, 900, 500, "Record now window");
	}
}

function recordingPushedDecision(recordNowNothing,recordNowUndefinitely,recordNowCurrent) {
	var recordNow = recordNowNothing;
	recordNow = (recordNow == "") ? recordNowUndefinitely: recordNow;
	recordNow = (recordNow == "") ? recordNowCurrent: recordNow;
	if(recordNow != "nothing" && recordNow != "") {
		doRequest(url_recordnow+"?recordnow="+recordNow, incomingTimerAddResult, false);
	}
}

function ifChecked(rObj) {
	if(rObj.checked) {
		return rObj.value;
	} else {
		return "";
	}
}

//About
/*
 * Show About Information in contentMain
 */
function showAbout() {
	doRequest(url_about, incomingAbout, false);
}

/*
 * Handles an incoming request for /web/about
 * Parses the Data, and calls everything needed to render the 
 * Template using the parsed data and set the result into contenMain
 * @param request - the XHR
 */
function incomingAbout(request) {
	if(request.readyState == 4){
		debug("incomingAbout returned");
		var aboutEntries = getXML(request).getElementsByTagName("e2abouts").item(0).getElementsByTagName("e2about");

		var xml = aboutEntries.item(0);
		
		var namespace = {};
		var ns = new Array();
		
		try{
			var fptext = "V"+xml.getElementsByTagName('e2fpversion').item(0).firstChild.data;
			
			
			var nims = xml.getElementsByTagName('e2tunerinfo').item(0).getElementsByTagName("e2nim");
			debug("nims: "+nims.length);
			for(var i = 0; i < nims.length; i++){
				
				name = nims.item(i).getElementsByTagName("name").item(0).firstChild.data;
				type = nims.item(i).getElementsByTagName("type").item(0).firstChild.data;
				debug(name);
				debug(type);
				ns[i] = { 'name' : name, 'type' : type};
				
			}
			
			
			var hdddata = xml.getElementsByTagName('e2hddinfo').item(0);
			
			var hddmodel 	= hdddata.getElementsByTagName("model").item(0).firstChild.data;
			var hddcapacity = hdddata.getElementsByTagName("capacity").item(0).firstChild.data;
			var hddfree		= hdddata.getElementsByTagName("free").item(0).firstChild.data;

			namespace = {
				'model' : xml.getElementsByTagName('e2model').item(0).firstChild.data	
				,'enigmaVersion': xml.getElementsByTagName('e2enigmaversion').item(0).firstChild.data
				,'fpVersion': fptext
				,'webifversion': xml.getElementsByTagName('e2webifversion').item(0).firstChild.data				
				,'lanDHCP': xml.getElementsByTagName('e2landhcp').item(0).firstChild.data
				,'lanIP': xml.getElementsByTagName('e2lanip').item(0).firstChild.data
				,'lanNetmask': xml.getElementsByTagName('e2lanmask').item(0).firstChild.data
				,'lanGateway': xml.getElementsByTagName('e2langw').item(0).firstChild.data

//					,'tunerInfo': tunerinfo
				,'hddmodel': hddmodel
				,'hddcapacity': hddcapacity
				,'hddfree': hddfree
				
				,'serviceName': xml.getElementsByTagName('e2servicename').item(0).firstChild.data
				,'serviceProvider': xml.getElementsByTagName('e2serviceprovider').item(0).firstChild.data
				,'serviceAspect': xml.getElementsByTagName('e2serviceaspect').item(0).firstChild.data
				,'serviceVideosize': xml.getElementsByTagName('e2servicevideosize').item(0).firstChild.data
				,'serviceNamespace': xml.getElementsByTagName('e2servicenamespace').item(0).firstChild.data
				
				,'vPidh': '0x'+d2h(xml.getElementsByTagName('e2vpid').item(0).firstChild.data, 4)
				 ,'vPid': ownLazyNumber(xml.getElementsByTagName('e2vpid').item(0).firstChild.data)
				,'aPidh': '0x'+d2h(xml.getElementsByTagName('e2apid').item(0).firstChild.data, 4)
				 ,'aPid': ownLazyNumber(xml.getElementsByTagName('e2apid').item(0).firstChild.data)
				,'pcrPidh': '0x'+d2h(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data, 4)
				 ,'pcrPid': ownLazyNumber(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data)
				,'pmtPidh': '0x'+d2h(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data, 4)
				 ,'pmtPid': ownLazyNumber(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data)
				,'txtPidh': '0x'+d2h(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data, 4)
				 ,'txtPid': ownLazyNumber(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data)
				,'tsidh': '0x'+d2h(xml.getElementsByTagName('e2tsid').item(0).firstChild.data, 4)
				 ,'tsid': ownLazyNumber(xml.getElementsByTagName('e2tsid').item(0).firstChild.data)
				,'onidh': '0x'+d2h(xml.getElementsByTagName('e2onid').item(0).firstChild.data, 4)
				 ,'onid': ownLazyNumber(xml.getElementsByTagName('e2onid').item(0).firstChild.data)
				,'sidh': '0x'+d2h(xml.getElementsByTagName('e2sid').item(0).firstChild.data, 4)
				 ,'sid': ownLazyNumber(xml.getElementsByTagName('e2sid').item(0).firstChild.data)
			};				  
		} catch (e) {
			debug("About parsing Error" + e);
		}

		data = { about : namespace,
				 tuner : ns};
		processTpl('tplAbout', data, 'contentMain');
	}
}


// Spezial functions, mostly for testing purpose
function openHiddenFunctions(){
	openPopup("Extra Hidden Functions",tplExtraHiddenFunctions,300,100,920,0);
}
function restartUpdateStream() {
	clearInterval(UpdateStreamReaderPollTimer);
	UpdateStreamReaderRequest.abort();
	UpdateStreamReaderRequest = null;
	UpdateStreamReaderPollTimerCounter = 0;
	UpdateStreamReaderStart();
}

function startDebugWindow() {
	DBG = true;
	debugWin = openPopup("DEBUG", "", 300, 300,920,140, "debugWindow");
}

function restartTwisted() {
	new Ajax.Request( "/web/restarttwisted", { asynchronous: true, method: "get" })
}


//MediaPlayer
function loadMediaPlayer(directory){
	debug("loading loadMediaPlayer");
	doRequest(url_mediaplayerlist+directory, incomingMediaPlayer, false);
}

function incomingMediaPlayer(request){
	if(request.readyState == 4){
		var files = new FileList(getXML(request)).getArray();
		debug(getXML(request));
		debug("have "+files.length+" entry in mediaplayer filelist");
		listerHtml 	= tplMediaPlayerHeader;

		root = files[0].getRoot();
		if (root != "playlist") {
			listerHtml 	= RND(tplMediaPlayerHeader, {'root': root});
			if(root != '/') {
				re = new RegExp(/(.*)\/(.*)\/$/);
				re.exec(root);
				newroot = RegExp.$1+'/';
				if(newroot == '//') {
					newroot = '/';
				}
				listerHtml += RND(tplMediaPlayerItemBody, 
					{'root': root
					, 'servicereference': newroot
					,'exec': 'loadMediaPlayer'
					,'exec_description': 'change to directory ../'
					,'color': '000000'
					,'root': newroot
					,'name': '..'});
			}
		}
		for ( var i = 0; i <files.length; i++){
			var file = files[i];
			if(file.getNameOnly() == 'None') {
				continue;
			}
			var exec = 'loadMediaPlayer';
			var exec_description = 'change to directory' + file.getServiceReference();
			var color = '000000';
			if (file.getIsDirectory() == "False") {
				exec = 'playFile';
				exec_description = 'play file';
				color = '00BCBC';
			}
			var namespace = {
				'servicereference': file.getServiceReference()
				,'exec': exec
				,'exec_description': exec_description
				,'color': color
				,'root': file.getRoot()
				,'name': file.getNameOnly()
			};
			listerHtml += tplMediaPlayerItemHead;
			listerHtml += RND(tplMediaPlayerItemBody, namespace);
			if (file.getIsDirectory() == "False") {
				listerHtml += RND(tplMediaPlayerItemIMG, namespace);
			}
			listerHtml += tplMediaPlayerItemFooter;
		}
		if (root == "playlist") {
			listerHtml += tplMediaPlayerFooterPlaylist;
		}
		listerHtml += tplMediaPlayerFooter;
		$('BodyContent').innerHTML = listerHtml;
		var sendMediaPlayerTMP = sendMediaPlayer;
		sendMediaPlayer = false;
		setBodyMainContent('BodyContent');
		sendMediaPlayer = sendMediaPlayerTMP;
	}		
}

function playFile(file,root) {
	debug("loading playFile");
	mediaPlayerStarted = true;
	new Ajax.Request( url_mediaplayerplay+file+"&root="+root, { asynchronous: true, method: 'get' });
}

function sendMediaPlayer(command) {
	debug("loading sendMediaPlayer");
	new Ajax.Request( url_mediaplayercmd+command, { asynchronous: true, method: 'get' });
}

function openMediaPlayerPlaylist() {
	debug("loading openMediaPlayerPlaylist");
	doRequest(url_mediaplayerlist+"playlist", incomingMediaPlayer, false);
}

function writePlaylist() {
	debug("loading writePlaylist");
	filename = prompt("Please enter a name for the playlist", "");
	if(filename != "") {
		new Ajax.Request( url_mediaplayerwrite+filename, { asynchronous: true, method: 'get' });
	}
}

//Powerstate
/*
 * Sets the Powerstate
 * @param newState - the new Powerstate
 * Possible Values (also see WebComponents/Sources/PowerState.py)
 * #-1: get current state
 * # 0: toggle standby
 * # 1: poweroff/deepstandby
 * # 2: rebootdreambox
 * # 3: rebootenigma
 */
function sendPowerState(newState){
	new Ajax.Request( url_powerstate+'?newstate='+newState, { asynchronous: true, method: 'get' });
}

//FileBrowser
function loadFileBrowser(directory,types){
	debug("loading loadFileBrowser");
	doRequest(url_filelist+directory+"&types="+types, incomingFileBrowser, false);	
}
function incomingFileBrowser(request){
	if(request.readyState == 4){
		var files = new FileList(getXML(request)).getArray();
		debug(getXML(request));
		debug("have "+files.length+" entry in filelist");
		listerHtml 	= tplFileBrowserHeader;
		root = files[0].getRoot();
		listerHtml 	= RND(tplFileBrowserHeader, {'root': root});
		if(root != '/') {
			re = new RegExp(/(.*)\/(.*)\/$/);
			re.exec(root);
			newroot = RegExp.$1+'/';
			if(newroot == '//') {
				newroot = '/';
			}
			listerHtml += RND(tplFileBrowserItemBody, 
				{'root': root
				, 'servicereference': newroot
				,'exec': 'loadFileBrowser'
				,'exec_description': 'change to directory ../'
				,'color': '000000'
				,'root': newroot
				,'name': '..'});
		}
		for ( var i = 0; i <files.length; i++){
			var file = files[i];
			if(file.getNameOnly() == 'None') {
				continue;
			}
			var exec = 'loadFileBrowser';
			var exec_description = 'change to directory' + file.getServiceReference();
			var color = '000000';
			if (file.getIsDirectory() == "False") {
				exec = '';
				exec_description = 'do Nothing';
				color = '00BCBC';
			}
			var namespace = {
				'servicereference': file.getServiceReference()
				,'exec': exec
				,'exec_description': exec_description
				,'color': color
				,'root': file.getRoot()
				,'name': file.getNameOnly()
			};
			listerHtml += tplFileBrowserItemHead;
			listerHtml += RND(tplFileBrowserItemBody, namespace);
			if (file.getIsDirectory() == "False") {
				listerHtml += RND(tplFileBrowserItemIMG, namespace);
			}
			listerHtml += tplFileBrowserItemFooter;
		}
		listerHtml += RND(tplFileBrowserFooter, {'root': root});
		$('BodyContent').innerHTML = listerHtml;
		setBodyMainContent('BodyContent');
	}		
}
function delFile(file,root) {
	debug("loading loadMediaPlayer");
	doRequest(url_delfile+root+file, incomingDelFileResult, false);
}
function incomingDelFileResult(request) {
	debug("incomingDelFileResult");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		if(delresult.getState()){
			loadFileBrowser($('path').value);
		}else{
			messageBox("Deletion Error","Reason: "+delresult.getStateText());
		}
	}		
}


//Navigation and Content Helper Functions
/*
 * Loads all Bouquets for the given enigma2 servicereference and sets the according contentHeader
 * @param sRef - the Servicereference for the bouquet to load
 */
function getBouquets(sRef){
	setAjaxLoad('contentMain');

	var contentHeader = "";
	switch(sRef){
		case bouquetsTv:
			contentHeader = "Bouquets (TV)";
			break;
		case providerTv:
			contentHeader = "Provider (TV)";
			break;
		case bouquetsRadio:
			contentHeader = "Bouquets (Radio)";
			break;
		case providerRadio:
			contentHeader = "Provider (Radio)";
			break;
	}
	setContentHd(contentHeader);
	
	var url = url_getServices+encodeURIComponent(sRef);
	doRequest(url, incomingBouquetList, true);
}

/*
 * Loads another navigation template and sets the navigation header
 * @param template - The name of the template
 * @param title - The title to set for the navigation
 */
function reloadNav(template, title){
		setAjaxLoad('navContent');
		processTpl(template, null, 'navContent');
		setNavHd(title);
}

/*
 * Loads dynamic content to $(contentMain) by calling a execution function
 * @param fnc - The function used to load the content
 * @param title - The Title to set on the contentpanel
 */
function loadContentDynamic(fnc, title){
	setAjaxLoad('contentMain');
	setContentHd(title);
	fnc();
}

/*
 * Loads a static template to $(contentMain)
 * @param template - Name of the Template
 * @param title - The Title to set on the Content-Panel
 */
function loadContentStatic(template, title){
	setAjaxLoad('contentMain');
	setContentHd(title);
	processTpl(template, null, 'contentMain');
}

/*
 * Sets the Loading Notification to the given HTML Element
 * @param targetElement - The element the Ajax-Loader should be set in
 */
function setAjaxLoad(targetElement){
	$(targetElement).innerHTML = getAjaxLoad();
}

/*
 * Opens the given Extra
 * @param extra - Extra Page as String
 * Possible Values: power, about, message
 */
function openExtra(extra){
	switch(extra){
		case "power":
			loadContentStatic('tplPower', 'PowerControl');
			break;
	
		case "about":
			loadContentDynamic(showAbout, 'About');
			break;
		
		case "message":
			loadContentStatic('tplSendMessage', 'Send a Message');
			break;		
	}
}

/*
 * Switches Navigation Modes
 * @param mode - The Navigation Mode you want to switch to
 * Possible Values: TV, Radio, Movies, Timer, Extras
 */
function switchNav(mode){
	switch(mode){
		case "TV":
			reloadNav('tplNavTv', 'TeleVision');
			break;
		
		case "Radio":
			reloadNav('tplNavRadio', 'Radio');
			break;
		
		case "Movies":
			loadContentDynamic(loadMovieList, 'Movies');
			break;
			
		case "Timer":
			//The Navigation
			reloadNav('tplNavTimer', 'Timer');
			
			//The Timerlist
			loadContentDynamic(loadTimerList, 'Timer');
			break;
		
		case "Extras":
			reloadNav('tplNavExtras', 'Extras');
			break;
	}
}


/*
 * Does the everything required on initial pageload
 */
function init(){
	if(DBG){
		loadAndOpenDebug();
	}
	
	setAjaxLoad('navContent');
	setAjaxLoad('contentMain');
	
	fetchTpl('tplServiceListEPGItem');
	reloadNav('tplNavTv', 'TeleVision');
	
	initChannelList();
	initVolumePanel();
}
