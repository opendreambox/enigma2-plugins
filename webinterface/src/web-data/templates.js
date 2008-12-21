Version = '$Header$';
// EPG Templates
var tplUpdateStreamReaderIE = '<iframe id="UpdateStreamReaderIEFixIFrame" src="%(url_updates)" height="0" width="0" scrolling="none" frameborder="0">no iframe support!</iframe>';


var tplEPGListItemExtend  = '%(shortTxt) ...<a nohref onclick="setComplete(\'extdescription%(number)\',\'%(txt)\');">more</a>';

var tplRecordingFooter   = '<hr><br><table style="text-align: left; width: 100%; height: 178px;" border="0" cellpadding="2" cellspacing="2"><tbody>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowNothing" name="recordNow" value="nothing" checked>';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'Do nothing';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowUndefinitely" name="recordNow" value="undefinitely">';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'record current playing undefinitely';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
    tplRecordingFooter  += '<input type="radio" id="recordNowCurrent" name="recordNow" value="recordCurrentEvent">';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += 'record current event';
    tplRecordingFooter  += '</td></tr>';
	tplRecordingFooter  += '<tr><td style="vertical-align: top;">';
	tplRecordingFooter  += '&nbsp;';
    tplRecordingFooter  += '</td><td style="vertical-align: top;">';
    tplRecordingFooter  += '<img src="/webdata/gfx/ok.jpg" title="OK" border="0" onclick="recordingPushedDecision(ifChecked($(\'recordNowNothing\')), ifChecked($(\'recordNowUndefinitely\')), ifChecked($(\'recordNowCurrent\')) );window.close()">';
    tplRecordingFooter  += '</td></tr>';
    tplRecordingFooter  += '</tbody></table>';

//Volume Template
var tplVolumePanel  = "<img onclick='volumeUp()' src='/webdata/gfx/arrow_up.png'>";
	tplVolumePanel += "<img onclick='volumeDown()' src='/webdata/gfx/arrow_down.png'>";
	tplVolumePanel += "<img id='volume1' onclick='volumeSet(10)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume2' onclick='volumeSet(20)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume3' onclick='volumeSet(30)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume4' onclick='volumeSet(40)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume5' onclick='volumeSet(50)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume6' onclick='volumeSet(60)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume7' onclick='volumeSet(70)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume8' onclick='volumeSet(80)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume9' onclick='volumeSet(90)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='volume10' onclick='volumeSet(100)' src='/webdata/gfx/led_off.png'>";
	tplVolumePanel += "<img id='speaker' onclick='volumeMute()' src='/webdata/gfx/speak_on.png'>";

//Signal Template
var tplSignalPanel  = '<table width="100%" id="SignalPanelTable">';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">dB</td><td style="background-color: #DDDDDD;"><div id="SNRdB">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">SNR</td><td style="background-color: #DDDDDD;"><div id="SNR">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">AGC</td><td style="background-color: #DDDDDD;"><div id="AGC">N/A</div></td></tr>';
	tplSignalPanel += '<tr><td style="background-color: #DDDDDD;">BER</td><td style="background-color: #DDDDDD;"><div id="BER">N/A</div></td></tr>';
	tplSignalPanel += '</table>';

var tplAddTimerForm  = '<table border=0 cellpadding=0 cellspacing=10>';
	tplAddTimerForm += '<tr><td colspan="3">Action:</td>';
	tplAddTimerForm += '<td colspan="3">';
	tplAddTimerForm += '<select name="justplay" id="justplay" size="1">';
	tplAddTimerForm += '%(justplay)';
	tplAddTimerForm += '</select></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">&nbsp;</td>';
	tplAddTimerForm += '<td colspan="3">Note: For recurring events start/end day/month are not required.</td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">Start:</td>';
	tplAddTimerForm += '<td colspan="3"><select name="syear" size="1" id="syear" onchange="javascript:addTimerFormChangeTime(\'syear\');">%(syear)</select>.';
	tplAddTimerForm += '<select name="smonth" id="smonth" size="1" onchange="javascript:addTimerFormChangeTime(\'smonth\');">%(smonth)</select>.';
	tplAddTimerForm += '<select name="sday" id="sday" size="1" onchange="javascript:addTimerFormChangeTime(\'sday\');">%(sday)</select>';
	tplAddTimerForm += '&nbsp;-&nbsp;<select name="shour" id="shour" size="1" onchange="javascript:addTimerFormChangeTime(\'shour\');">%(shour)</select>';
	tplAddTimerForm += ':<select name="smin" id="smin" size="1" onchange="javascript:addTimerFormChangeTime(\'smin\');">%(smin)</select></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">End:</td>';
	tplAddTimerForm += '<td colspan="3"><select name="eyear" id="eyear" size="1" onchange="javascript:addTimerFormChangeTime(\'eyear\');">%(eyear)</select>.';
	tplAddTimerForm += '<select name="emonth" id="emonth" size="1" onchange="javascript:addTimerFormChangeTime(\'emonth\');">%(emonth)</select>.';
	tplAddTimerForm += '<select name="eday" id="eday" size="1" onchange="javascript:addTimerFormChangeTime(\'eday\');">%(eday)</select>';
	tplAddTimerForm += '&nbsp;-&nbsp;<select name="ehour" id="ehour" size="1" onchange="javascript:addTimerFormChangeTime(\'ehour\');">%(ehour)</select>';
	tplAddTimerForm += ':<select name="emin" id="emin" size="1" onchange="javascript:addTimerFormChangeTime(\'emin\');">%(emin)</select></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">&nbsp;</td><td colspan="3">Note: For one-time events the "days" field doesn\'t have to be specified.</td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">Days:</td><td colspan="3">%(repeated)';
	tplAddTimerForm += '<tr><td colspan="3">Channel:</td><td>';
	tplAddTimerForm += '<p><input type="radio" id="tvradio" name="tvradio" value="tv" checked onchange="javascript:addTimerFormChangeType();"">TV</p>';
	tplAddTimerForm += '<p><input type="radio" name="tvradio" value="radio" onchange="javascript:addTimerFormChangeType();">Radio</p><td>';
	tplAddTimerForm += '<p>Channel:</p>';
	tplAddTimerForm += '<select name="channel" id="channel" size="1" onchange="timerFormExtendChannellist($(\'channel\').options[$(\'channel\').selectedIndex].value)">%(channel)</select></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">Name:</td>';
	tplAddTimerForm += '<td colspan="3"><input name="name" id="name" type="text" size="100" maxlength="100" style="color: #000000;" value="%(name)"></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">Description:</td>';
	tplAddTimerForm += '<td colspan="3"><input name="descr" id="descr" type="text" size="100" maxlength="100" style="color: #000000;" value="%(description)"></td></tr>';
	tplAddTimerForm += '<tr><td colspan="3">After event do:</td>';
	tplAddTimerForm += '<td colspan="3"><select id="after_event" name="after_event" size="1">%(afterEvent)</select></td></tr>';
	tplAddTimerForm += '<tr>&nbsp;&nbsp;</tr>';
	tplAddTimerForm += '<tr><td colspan="3">&nbsp;</td><td colspan="3">';
	tplAddTimerForm += '<input name="deleteOldOnSave" id="deleteOldOnSave" type="hidden" value="%(deleteOldOnSave)">';
	tplAddTimerForm += '<input name="channelOld" id="channelOld" type="hidden" value="%(channelOld)">';
	tplAddTimerForm += '<input name="beginOld" id="beginOld" type="hidden" value="%(beginOld)">';
	tplAddTimerForm += '<input name="endOld" id="endOld" type="hidden" value="%(endOld)">';
	tplAddTimerForm += '<input name="eventID" id="eventID" type="hidden" value="%(eventID)">';
	tplAddTimerForm += 	'<button onclick="sendAddTimer();">Add/Save</button></td></tr></table>';

var tplAddTimerFormOptions = '<option value="%(value)" %(selected)>%(txt)</option>';

var tplAddTimerFormCheckbox = '<input type="checkbox" id="%(id)" name="%(name)" value="%(value)" %(checked)>&nbsp;%(txt)&nbsp;&nbsp;';


var tplExtraHiddenFunctions  = '<ul style="list-style-type:disc">';
	tplExtraHiddenFunctions += '<li><div onclick="restartTwisted()">Restart Twisted</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="clearInterval(UpdateStreamReaderPollTimer);">Stop Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="restartUpdateStream();">Restart Time/Signal/Current-Channel -Updates</div></li>';
	tplExtraHiddenFunctions += '<li><div onclick="startDebugWindow();">Start Debug-Window</div></li>';
	tplExtraHiddenFunctions += '</ul>'

var tplRCGrab  = '<IMG id="grabPageIMG" src=""/ height="400" alt="loading image">';

var tplMediaPlayerHeader  = '<div class="BodyContentChannellist">\n<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
	tplMediaPlayerHeader += '<thead class="fixedHeader">\n';
	tplMediaPlayerHeader += '<tr>\n';
	tplMediaPlayerHeader += '<th><div class="sListHeader">MediaPlayer %(root)';
	tplMediaPlayerHeader += '<map name="mpcontrols">';
	tplMediaPlayerHeader += '<area shape="circle" coords="17, 17, 14" nohref onclick="sendMediaPlayer(0)" alt="jump back">';
	tplMediaPlayerHeader += '<area shape="circle" coords="54, 17, 14" nohref onclick="sendMediaPlayer(1)" alt="play">';
	tplMediaPlayerHeader += '<area shape="circle" coords="88, 17, 14" nohref onclick="sendMediaPlayer(2)" alt="pause">';
	tplMediaPlayerHeader += '<area shape="circle" coords="125, 17, 14" nohref onclick="sendMediaPlayer(3)" alt="jump forward">';
	tplMediaPlayerHeader += '<area shape="circle" coords="161, 17, 14" nohref onclick="sendMediaPlayer(4)" alt="stop">';
	tplMediaPlayerHeader += '</map><img src="/webdata/gfx/dvr-buttons-small-fs8.png" align="top" title="Control MediaPlayer" border="0" usemap="#mpcontrols">\n'
//	tplMediaPlayerHeader += '<img src="/webdata/gfx/edit.gif" onclick="openMediaPlayerPlaylist()">';
// still need some work for editing.
	tplMediaPlayerHeader += '</div>\n';
	tplMediaPlayerHeader += '<div class="sListSearch">';
	tplMediaPlayerHeader += '<img src="/webdata/gfx/nok.png" align="top" title="close MediaPlayer" border="0" onclick="sendMediaPlayer(5)"></div></th>';
	tplMediaPlayerHeader += '</tr>\n';
	tplMediaPlayerHeader += '</thead>\n';
	tplMediaPlayerHeader += '<tbody class="scrollContent">\n';

var tplMediaPlayerItemHead = '<tr>\n';
var tplMediaPlayerItemBody = '<td><div style="color: #%(color);" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" class="sListSName" title="%(servicereference)">%(name)</div>';
var	tplMediaPlayerItemIMG  = '<div class="sListExt">\n';
	tplMediaPlayerItemIMG += '<img src="/webdata/gfx/play.png" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" title="%(exec_description)" border="0">\n';
	tplMediaPlayerItemIMG += '<a target="_blank" href="/file/?file=%(name)&root=%(root)"><img src="/webdata/gfx/save.png" title="download File" border="0"></a>\n';
	tplMediaPlayerItemIMG += '</div>\n';
var tplMediaPlayerItemFooter = '</tr>\n';

var tplMediaPlayerFooterPlaylist  = '<tr><td colspan="7"><button onclick="writePlaylist()">Write Playlist</button></td></tr>\n';
var tplMediaPlayerFooter = "</tbody></table>\n";


var tplFileBrowserHeader  = '<div class="BodyContentChannellist">\n<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
    tplFileBrowserHeader += '<thead class="fixedHeader">\n';
    tplFileBrowserHeader += '<tr>\n';
    tplFileBrowserHeader += '<th><div class="sListHeader">FileBrowser %(root)</div></th>\n';
    tplFileBrowserHeader += '<th><div class="sListSearch">';
	tplFileBrowserHeader += '<form onSubmit="loadFileBrowser(\'%(root)\', document.getElementById(\'searchText\').value); return false;">';
	tplFileBrowserHeader += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="Search Pattern"/>';
	tplFileBrowserHeader += '<input style="vertical-align:middle" type="image" src="/webdata/gfx/search.png" alt="search...">';
	tplFileBrowserHeader += '</form></div></th>';
    tplFileBrowserHeader += '</tr>\n';
    tplFileBrowserHeader += '</thead>\n';
    tplFileBrowserHeader += '<tbody class="scrollContent">\n';
    tplFileBrowserHeader += '<tr width="80%"><td>File/Directory</td>\n';
    tplFileBrowserHeader += '<td>Action</td>\n</tr>\n';

var tplFileBrowserItemHead = '<tr width="80%">\n';
var tplFileBrowserItemBody = '<td><div style="color: #%(color);" onclick="%(exec)(\'%(servicereference)\',\'%(root)\');" class="sListSName" title="%(servicereference)">%(name)</div></td>';
var tplFileBrowserItemIMG  = '<td><div class="sListExt">\n';
    tplFileBrowserItemIMG += '<img src="/webdata/gfx/trash.gif" onclick="delFile(\'%(name)\',\'%(root)\');" title="delete File" border="0">\n';
    tplFileBrowserItemIMG += '<a target="_blank" href="/file/?file=%(name)&root=%(root)"><img src="/webdata/gfx/save.png" title="download File" border="0"></a>\n';
    tplFileBrowserItemIMG += '</div></td>\n';
var tplFileBrowserItemFooter = '</tr>\n';

var tplFileBrowserFooter  = '</tbody></table>\n';
	tplFileBrowserFooter += '<form action="/upload" method="POST" target="_blank" enctype="multipart/form-data">';
	tplFileBrowserFooter += '<input type="hidden" id="path" value="%(root)" name="path">';
	tplFileBrowserFooter += '<input name="file" type="file">';
	tplFileBrowserFooter += '<input type="image" style="vertical-align:middle" src="/webdata/gfx/save.png" alt="upload">';
