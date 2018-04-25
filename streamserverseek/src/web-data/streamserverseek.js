
function secondsTimeSpanToMS(s) {
    var m = Math.floor(s/60); //Get remaining minutes
    s -= m*60;
    return (m < 10 ? '0'+m : m)+":"+(s < 10 ? '0'+s : s); //zero padding on minutes and seconds
}

var setTimer = true;

function updateInfo(callback)
{
    setTimer = true;
    $.ajax({
        url: 'web/getinfo?unit=sec',
        cache: false,
        success:function(data) {
            result = {};
            $(data).find("e2streamserverseekinfo").first().children().each(function(key, value){
                var $value = $(value);
                result[$value.prop("tagName").substring(2)] = $value.html();
            });
            callback(result);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            callback(false);
        }
    });
}

var infoTimeout;

var infoCallbackFunc = function(info){
    if (info && info.state > 0)
    {
        $('.controls').show();
        $('.row.inactive').hide();
        $('.row.error').hide();
        $('.controls .servicename').html(info.servicename);
        if (info.seekable == "1") {
            $('.controls .length').html(secondsTimeSpanToMS(info.length));
            $("input.slider").slider({
                max: info.length,
            });
            $("input.slider").slider('setValue', info.playposition);
            $("input.slider").slider("enable");
        } else {
            $('.controls .length').html('--:--');   
            $("input.slider").slider({
                max: 0,
            });
            $("input.slider").slider("disable");
            $("input.slider").slider('setValue', 0);
        }
    }
    else if (info)
    {
        $('.controls').hide();
        $('.row.inactive').show();
        $('.row.error').hide();
    }
    else
    {
        $('.row.controls').hide();
        $('.row.inactive').hide();
        $('.row.error').show();
    }
    if (setTimer)
        infoTimeout = setTimeout(function(){ updateInfo(infoCallbackFunc); }, 1000);
};

updateInfo(infoCallbackFunc);

var mySlider = $("input.slider").slider({
    tooltip: 'always',
    formatter: function(value) {
        return secondsTimeSpanToMS(value);
    },
    step: 1
});

$("input.slider").slider("on", "slideStart", function() {
    setTimer = false;
    clearTimeout(infoTimeout);
});

$("input.slider").slider("on", "slideStop", function() {
    $.ajax({
        url: 'web/seekto?unit=sec&pos=' + $("input.slider").slider("getValue"),
        cache: false,
        async: false,
    });
    updateInfo(infoCallbackFunc);
});

