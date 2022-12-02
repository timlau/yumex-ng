user:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install
	ninja -C builddir run

inst-builddeps:
	sudo dnf install gtk4-devel libadwaita-devel meson blueprint-compiler transifex-client


transifex-update:
	tx pull 
	po/update_potfile.sh 
	tx push
	git add po/*
	git commit -m "i18n: updated translations from transifex"
