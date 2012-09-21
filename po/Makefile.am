LANGS = ar ca cs da de el en es et fa fi fr fy he hr hu is it lt lv nl no pl pt ru sv sk sl sr tr uk
LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

EXTRA_DIST = $(LANGPO)

if UPDATE_PO
XGETTEXT = xgettext
MSGUNIQ = msguniq
MSGMERGE = msgmerge
MSGINIT = msginit
MSGFMT = msgfmt
# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
@PACKAGE_NAME@-py.pot: $(top_srcdir)/webinterface/src/*.py \
	$(top_srcdir)/webinterface/src/WebComponents/*.py \
	$(top_srcdir)/webinterface/src/WebChilds/*/*.py \
	$(top_srcdir)/webinterface/src/WebComponents/*/*.py
	$(XGETTEXT) --language=Python --from-code=UTF-8 --add-comments="TRANSLATORS:" -d @PACKAGE_NAME@ -s -o $@ $^

@PACKAGE_NAME@-xml.pot: $(top_srcdir)/xml2po.py $(top_srcdir)/webinterface/meta/*.xml
	$(PYTHON) $^ > $@

@PACKAGE_NAME@.pot: @PACKAGE_NAME@-py.pot @PACKAGE_NAME@-xml.pot
	cat $^ | $(MSGUNIQ) -s -n --add-location --to-code=UTF-8 -o $@ -

%.po: @PACKAGE_NAME@.pot
	if [ -f $@ ]; then \
		$(MSGMERGE) --backup=none --add-location -s -N -U $@ $< && touch $@; \
	else \
		$(MSGINIT) --locale=UTF-8 $@ -o $@ -i $< --no-translator; \
	fi
endif

.po.mo:
	$(MSGFMT) -o $@ $<

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO) @PACKAGE_NAME@-py.pot @PACKAGE_NAME@-xml.pot @PACKAGE_NAME@.pot

dist-hook: $(LANGPO)

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)${datadir}/enigma2/po/$$lang/LC_MESSAGES/@PACKAGE_NAME@.mo; \
	done
