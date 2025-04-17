import gettext
import locale
import logging
import os
import signal
import sys

sys.dont_write_bytecode = True

import gi

gi.require_version("Flatpak", "1.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio  # type: ignore

logger = logging.getLogger(__name__)


def main() -> int:
    """The application's entry point."""

    from app import GuiTestApplication

    app = GuiTestApplication()
    return app.run()


if __name__ == "__main__":
    pkgdatadir = "/home/tim/udv/github/yumex-ng/builddir/data"
    localedir = "/home/tim/udv/github/yumex-ng/builddir/share/locale"

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gettext.install("yumex", localedir)

    locale.bindtextdomain("yumex", localedir)
    locale.textdomain("yumex")

    # In the local use case, use yumex module from the sourcetree
    sys.path.insert(1, "/home/tim/udv/github/yumex-ng")

    # In the local use case the installed schemas go in <builddir>/data
    os.environ["XDG_DATA_DIRS"] = "/home/tim/udv/github/yumex-ng/builddir/share:" + os.environ.get("XDG_DATA_DIRS", "")

    pkgdatadir = "/home/tim/udv/github/yumex-ng/builddir/data"
    resource = Gio.Resource.load(os.path.join(pkgdatadir, "yumex.gresource"))
    Gio.Resource._register(resource)
    main()
