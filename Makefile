user:
	meson setup builddir --prefix="$(shell pwd)/builddir" --buildtype=debug --wipe
	ninja -C builddir install
	ninja -C builddir run

inst-builddeps:
	sudo dnf install gtk4-devel libadwaita-devel meson blueprint-compiler
