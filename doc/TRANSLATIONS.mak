LANGS = ar ca cs da de el en es et fa fi fr fy he hr hu is it lt lv nl no pl pt ru sv sk sl sr tr uk
PLUGIN ?= pluginfoldername
PLUGIN_DIR := $(CURDIR)/$(PLUGIN)
PLUGIN_TMPDIR := $(PLUGIN_DIR)TMP


usage:
	@echo "[*] Please run '$(MAKE) -f doc/TRANSLATIONS.mak help' to display further information!"


help:
	@echo '[*] Migrate an existing plugin translation into the new global translation file:'
	@echo '    $$ $(MAKE) -f doc/TRANSLATIONS.mak migrate PLUGIN=pluginfoldername'


migrate:
	@echo '[*] Migrating translations for plugin: $(PLUGIN)'
	@echo '[*] Creating temporary working folders'
	@cp -a $(PLUGIN_DIR) $(PLUGIN_TMPDIR)
	@cp -a $(CURDIR)/po $(CURDIR)/po2
	@for lang in $(LANGS); do \
		if [ -f ${PLUGIN_TMPDIR}/po/$$lang.po ]; then \
			echo [*] - Updating global $$lang.po..; \
			msgcat --use-first -s --to-code=UTF-8 -o $(CURDIR)/po/$$lang.po $(CURDIR)/po2/$$lang.po ${PLUGIN_TMPDIR}/po/$$lang.po; \
		fi \
	done
	@echo '[*] Deleting temporary working folder'
	@$(RM) -r $(PLUGIN_TMPDIR)
	@$(RM) -r $(CURDIR)/po2
	@echo '[*] Done.'
