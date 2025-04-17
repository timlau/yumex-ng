from yumex.ui.transaction_result import YumexTransactionResult


def run_test(win):
    test_transaction_result_show_errors(win)


def test_transaction_result_show_errors(win):
    """Test the transaction result dialog."""
    result = YumexTransactionResult()
    msg = "Something is rotten in the state of Denmark\n" * 10
    msg += "10 < 11\n"  # This need to be escaped else it will be interpreted as a tag
    result.show_errors(msg)
    result.present(win)
