from yumex.utils.enums import ScriptType


def test_script_type():
    """Test the ScriptType enum"""
    assert str(ScriptType.PRE_INSTALL) == "PreInstall"
    assert str(ScriptType.POST_INSTALL) == "PostInstall"
    assert str(ScriptType.UNKNOWN) == "Unknown"
    assert ScriptType.PRE_INSTALL == 1
    assert ScriptType(1) == ScriptType.PRE_INSTALL
    assert str(ScriptType(1)) == "PreInstall"
