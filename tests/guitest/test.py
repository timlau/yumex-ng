def run_test(win):
    # test_transaction_result_show_errors(win)
    test_search_settings(win)
    return


def test_transaction_result_show_errors(win):
    from yumex.ui.transaction_result import YumexTransactionResult

    """Test the transaction result dialog."""
    result = YumexTransactionResult()
    msg = "Something is rotten in the state of Denmark\n" * 10
    msg += "10 < 11\n"  # This need to be escaped else it will be interpreted as a tag
    result.show_errors(msg)
    result.present(win)


def test_search_settings(win):
    from yumex.ui.search_settings import YumexSearchSettings

    """Test the search settings dialog."""
    settings = YumexSearchSettings()
    rc = settings.show(win)
    print(rc)
    print(settings.options)
