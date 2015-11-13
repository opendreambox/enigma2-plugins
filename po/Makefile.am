LANGS = ar ca cs da de el en es fa fi fr fy hr hu is it lt nl no pl pt ru sk sr sv tr
PLUGIN = @PACKAGE_NAME@

LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO)

.po.mo:
	$(MSGFMT) -o $@ $<

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
