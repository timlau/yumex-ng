user:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install
	ninja -C builddir run

inst-deps:
	sudo dnf install gtk4-devel libadwaita-devel meson blueprint-compiler python3-dnf 

potfiles:
	@echo "updating po/POTFILES with *.py & *.blp files"
	@find yumex -iname *.py > po/POTFILES
	@find data -iname *.blp >> po/POTFILES

transifex-update:
	po/update_potfile.sh 
	tx push
	git add po/*
	git commit -m "i18n: updated yumex.pot"

transifex-get:
	tx pull
	git add po/*
	git commit -m "i18n: updated translations from transifex"

