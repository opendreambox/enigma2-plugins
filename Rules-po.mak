CATEGORY ?= "Extensions"

plugindir = $(libdir)/enigma2/python/Plugins/$(CATEGORY)/$(PLUGIN)

LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO)

if UPDATE_PO
# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
$(PLUGIN)-py.pot:
	if test -d $(srcdir)/../src; then \
		$(XGETTEXT) -L python --from-code=UTF-8 --add-comments="TRANSLATORS:" -d $(PLUGIN) -s -o $(PLUGIN)-py.pot $(srcdir)/../src/*.py; \
	fi;
	if test -d $(srcdir)/../src_py; then \
		$(XGETTEXT) -L python --from-code=UTF-8 --add-comments="TRANSLATORS:" -d $(PLUGIN) -s -o $(PLUGIN)-py.pot $(srcdir)/../src_py/*.py; \
	fi;

$(PLUGIN)-xml.pot:
	if test -f $(srcdir)/../src/*.xml; then \
		$(PYTHON) $(top_srcdir)/xml2po.py $(srcdir)/../src/*.xml; \
	fi;
	if test ! -f $(srcdir)/../po/$(PLUGIN)-xml.pot; then \
		touch $(srcdir)/../po/$(PLUGIN)-xml.pot; \
	fi;

$(PLUGIN).pot: $(PLUGIN)-py.pot $(PLUGIN)-xml.pot
	if test -f $(srcdir)/../po/$(PLUGIN)-py.pot; then \
		sed -e s/charset=CHARSET/charset=UTF-8/ $(srcdir)/../po/$(PLUGIN)-py.pot -i; \
	fi;
	if test -f $(srcdir)/../po/$(PLUGIN)-xml.pot; then \
		sed -e s/charset=CHARSET/charset=UTF-8/ $(srcdir)/../po/$(PLUGIN)-xml.pot -i; \
	fi;
	cat $^ | $(MSGUNIQ) --no-location -o $@ -

%.po: $(PLUGIN).pot
	if [ -f $@ ]; then \
		$(MSGMERGE) --backup=none --no-location -s -N -U $@ $< && touch $@; \
	else \
		$(MSGINIT) -l $@ -o $@ -i $< --no-translator; \
	fi

CLEANFILES += $(PLUGIN)-py.pot $(PLUGIN)-xml.pot $(PLUGIN).pot
endif

.po.mo:
	$(MSGFMT) -o $@ $<

dist-hook: $(LANGPO)

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
	done
