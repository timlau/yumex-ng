user:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install
	ninja -C builddir run

inst-builddeps:
	sudo dnf install gtk4-devel libadwaita-devel meson blueprint-compiler transifex-client


transifex-setup:
	tx init
	tx set --auto-remote https://www.transifex.com/projects/p/yumex/
	tx set --auto-local  -r yumex.yumex-ng 'po/<lang>.po' --source-lang en --source-file po/yumex.pot --execute


transifex-update:
	tx pull -a -f
	po/update_potfile.sh 
	tx push -s
	git commit -a -m "Updated translations from transifex"