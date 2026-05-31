# i18n build targets. Source of truth for the translation workflow.
#
# Usage:
#   make i18n-extract          regenerate messages.pot from source
#   make i18n-init LANG=sn     create a new empty catalog for a language
#   make i18n-update           merge updated messages.pot into existing catalogs
#   make i18n-compile          compile .po -> .mo (including #, fuzzy entries)

POT := translations/messages.pot
TRANSLATIONS_DIR := translations
BABEL_CFG := babel.cfg

.PHONY: i18n-extract i18n-init i18n-update i18n-compile

i18n-extract:
	pybabel extract -F $(BABEL_CFG) -o $(POT) .

i18n-init:
	@test -n "$(LANG)" || (echo "Usage: make i18n-init LANG=<code>"; exit 1)
	pybabel init -i $(POT) -d $(TRANSLATIONS_DIR) -l $(LANG)

i18n-update:
	pybabel update -i $(POT) -d $(TRANSLATIONS_DIR)

i18n-compile:
	pybabel compile -d $(TRANSLATIONS_DIR) --use-fuzzy
