def run_test(win):
    # test_transaction_result_show_errors(win)
    test_transaction_result_show_errors_long(win)
    # test_search_settings(win)
    # test_system_upgrade_dialog(win)
    return


def test_system_upgrade_dialog(win):
    from yumex.ui.dialogs import YesNoDialog

    """Test the system upgrade dialog."""
    dialog = YesNoDialog(win)
    dialog.show()
    print(f"reboot : {dialog.answer}")
    assert dialog.answer is True or dialog.answer is False


def test_transaction_result_show_errors(win):
    from yumex.ui.transaction_result import YumexTransactionResult

    """Test the transaction result dialog."""
    result = YumexTransactionResult()
    msg = "Something is rotten in the state of Denmark\n" * 10
    # msg += "10 < 11\n"  # This need to be escaped else it will be interpreted as a tag
    result.show_errors(msg)
    result.present(win)


def test_transaction_result_show_errors_long(win):
    from yumex.ui.transaction_result import YumexTransactionResult

    """Test the transaction result dialog."""
    result = YumexTransactionResult()
    msg = """
Problem 1: installed package libtinysparql-3.9.1-2.fc42.x86_64 requires libicui18n.so.76()(64bit), but none of the providers can be installed
  - installed package libtinysparql-3.9.1-2.fc42.x86_64 requires libicuuc.so.76()(64bit), but none of the providers can be installed
  - libicu-76.1-4.fc42.x86_64 does not belong to a distupgrade repository
  - problem with installed package
 Problem 2: package gnome-session-wayland-session-47.0.1-1.fc41.x86_64 from fedora requires gnome-shell, but none of the providers can be installed
  - problem with installed package
  - installed package gnome-shell-common-48.1-1.fc42.noarch conflicts with gnome-shell < 48~rc-3 provided by gnome-shell-47.5-1.fc41.x86_64 from updates
  - installed package gnome-shell-common-48.1-1.fc42.noarch conflicts with gnome-shell < 48~rc-3 provided by gnome-shell-47.0-1.fc41.x86_64 from fedora
  - gnome-shell-48.1-1.fc42.x86_64 does not belong to a distupgrade repository
  - gnome-session-wayland-session-47.0.1-2.fc42.x86_64 does not belong to a distupgrade repository
  - problem with installed package
 Problem 3: package boost-locale-1.83.0-8.fc41.x86_64 from fedora requires libicudata.so.74()(64bit), but none of the providers can be installed
  - package boost-locale-1.83.0-8.fc41.x86_64 from fedora requires libicui18n.so.74()(64bit), but none of the providers can be installed
  - package boost-locale-1.83.0-8.fc41.x86_64 from fedora requires libicuuc.so.74()(64bit), but none of the providers can be installed
  - cannot install both libicu-74.2-2.fc41.x86_64 from fedora and libicu-76.1-4.fc42.x86_64 from @System
  - problem with installed package
  - installed package localsearch-3.9.0-1.fc42.x86_64 requires libicui18n.so.76()(64bit), but none of the providers can be installed
  - boost-locale-1.83.0-12.fc42.x86_64 does not belong to a distupgrade repository
  - problem with installed package
 Problem 4: package gtk3-3.24.43-2.fc41.x86_64 from fedora requires libtracker-sparql-3.0.so.0()(64bit), but none of the providers can be installed
  - installed package libtinysparql-3.9.1-2.fc42.x86_64 obsoletes libtracker-sparql < 3.8 provided by libtracker-sparql-3.7.3-3.fc41.x86_64 from fedora
  - problem with installed package
  - installed package tinysparql-3.9.1-2.fc42.x86_64 requires libtinysparql-3.0.so.0()(64bit), but none of the providers can be installed
  - installed package tinysparql-3.9.1-2.fc42.x86_64 requires libtinysparql(x86-64) = 3.9.1-2.fc42, but none of the providers can be installed
  - gtk3-3.24.49-2.fc42.x86_64 does not belong to a distupgrade repository
  - problem with installed package
 Problem 5: problem with installed package
  - package libavfilter-free-7.1.1-1.fc41.x86_64 from updates requires librubberband.so.2()(64bit), but none of the providers can be installed
  - package libavfilter-free-7.0.2-7.fc41.x86_64 from fedora requires librubberband.so.2()(64bit), but none of the providers can be installed
  - installed package rubberband-libs-4.0.0-3.fc42.x86_64 conflicts with rubberband < 4.0.0-3.fc42 provided by rubberband-3.3.0-7.fc41.x86_64 from fedora
  - libavfilter-free-7.1.1-3.fc42.x86_64 does not belong to a distupgrade repository
  - problem with installed package"""  # noqa: E501
    result.show_errors(msg)
    result.present(win)


def test_search_settings(win):
    from yumex.ui.search_settings import YumexSearchSettings

    """Test the search settings dialog."""
    settings = YumexSearchSettings()
    rc = settings.show(win)
    print(rc)
    print(settings.options)
