LANGS = ar ca cs da de el en es et fa fi fr fy he hr hu is it lt lv nl no pl pt ru sv sk sl sr tr uk
PLUGIN = @PACKAGE_NAME@
PYSRC = \
	$(top_srcdir)/aihdcontroler/src/*.py $(top_srcdir)/aihdcontroler/src/comp/*.py \
	$(top_srcdir)/antiscrollbar/src/*.py \
	$(top_srcdir)/ardmediathek/src/*.py \
	$(top_srcdir)/automaticvolumeadjustment/src/*.py \
	$(top_srcdir)/babelzapper/src/*.py \
	$(top_srcdir)/bitrateviewer/src/*.py \
	$(top_srcdir)/bonjour/src/*.py \
	$(top_srcdir)/cdinfo/src/*.py \
	$(top_srcdir)/dreamirc/src/*.py \
	$(top_srcdir)/dyndns/src/*.py \
	$(top_srcdir)/easyinfo/src/*.py \
	$(top_srcdir)/ecasa/src/*.py \
	$(top_srcdir)/emission/src/*.py \
	$(top_srcdir)/filebrowser/src/*.py \
	$(top_srcdir)/fstabeditor/src/*.py \
	$(top_srcdir)/genuinedreambox/src/*.py \
	$(top_srcdir)/googlemaps/src/*.py \
	$(top_srcdir)/growlee/src/*.py \
	$(top_srcdir)/httpproxy/src/*.py \
	$(top_srcdir)/letterbox/src/*.py \
	$(top_srcdir)/logomanager/src/*.py \
	$(top_srcdir)/menusort/src/*.py \
	$(top_srcdir)/merlinepg/src/*.py \
	$(top_srcdir)/merlinmusicplayer/src/*.py \
	$(top_srcdir)/movieepg/src/*.py \
	$(top_srcdir)/moviesearch/src/*.py \
	$(top_srcdir)/mphelp/src/*.py \
	$(top_srcdir)/multirc/src/*.py \
	$(top_srcdir)/netcaster/src/bin/*.py \
	$(top_srcdir)/orfat/src/*.py \
	$(top_srcdir)/orfteletext/src/*.py \
	$(top_srcdir)/pipservicerelation/src/*.py \
	$(top_srcdir)/pipzap/src/*.py \
	$(top_srcdir)/reconstructapsc/src_py/*.py \
	$(top_srcdir)/remotetimer/src/*.py \
	$(top_srcdir)/satloader/src/*.py \
	$(top_srcdir)/startuptostandby/src/*.py \
	$(top_srcdir)/subsdownloader2/src/*.py \
	$(top_srcdir)/svdrp/src/*.py \
	$(top_srcdir)/trafficinfo/src/*.py \
	$(top_srcdir)/tvcharts/src/*.py \
	$(top_srcdir)/valixdcontrol/src/*.py \
	$(top_srcdir)/webcamviewer/src/*.py \
	$(top_srcdir)/webinterface/src/*.py $(top_srcdir)/webinterface/src/*/*.py $(top_srcdir)/webinterface/src/*/*/*.py
XMLSRC = \
	$(top_srcdir)/aihdcontroler/meta/*.xml \
	$(top_srcdir)/antiscrollbar/meta/*.xml \
	$(top_srcdir)/ardmediathek/meta/*.xml \
	$(top_srcdir)/automaticvolumeadjustment/meta/*.xml \
	$(top_srcdir)/babelzapper/meta/*.xml \
	$(top_srcdir)/bitrateviewer/meta/*.xml \
	$(top_srcdir)/bonjour/meta/*.xml \
	$(top_srcdir)/cdinfo/meta/*.xml \
	$(top_srcdir)/dreamirc/meta/*.xml \
	$(top_srcdir)/dyndns/meta/*.xml \
	$(top_srcdir)/easyinfo/meta/*.xml \
	$(top_srcdir)/ecasa/meta/*.xml \
	$(top_srcdir)/emission/meta/*.xml \
	$(top_srcdir)/filebrowser/meta/*.xml \
	$(top_srcdir)/fstabeditor/meta/*.xml \
	$(top_srcdir)/genuinedreambox/meta/*.xml \
	$(top_srcdir)/googlemaps/meta/*.xml \
	$(top_srcdir)/growlee/meta/*.xml \
	$(top_srcdir)/httpproxy/meta/*.xml \
	$(top_srcdir)/letterbox/meta/*.xml \
	$(top_srcdir)/logomanager/meta/*.xml \
	$(top_srcdir)/menusort/meta/*.xml \
	$(top_srcdir)/merlinepg/meta/*.xml \
	$(top_srcdir)/merlinmusicplayer/meta/*.xml \
	$(top_srcdir)/movieepg/meta/*.xml \
	$(top_srcdir)/moviesearch/meta/*.xml \
	$(top_srcdir)/mphelp/meta/*.xml \
	$(top_srcdir)/multirc/meta/*.xml \
	$(top_srcdir)/netcaster/meta/*.xml \
	$(top_srcdir)/orfat/meta/*.xml \
	$(top_srcdir)/orfteletext/meta/*.xml \
	$(top_srcdir)/pipservicerelation/meta/*.xml \
	$(top_srcdir)/pipzap/meta/*.xml \
	$(top_srcdir)/reconstructapsc/meta/*.xml \
	$(top_srcdir)/remotetimer/meta/*.xml \
	$(top_srcdir)/satloader/meta/*.xml \
	$(top_srcdir)/startuptostandby/meta/*.xml \
	$(top_srcdir)/subsdownloader2/meta/*.xml \
	$(top_srcdir)/svdrp/meta/*.xml \
	$(top_srcdir)/trafficinfo/meta/*.xml \
	$(top_srcdir)/tvcharts/meta/*.xml \
	$(top_srcdir)/valixdcontrol/meta/*.xml \
	$(top_srcdir)/webcamviewer/meta/*.xml \
	$(top_srcdir)/webinterface/meta/*.xml
include $(top_srcdir)/Rules-po.mak

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done
