import pytest

from altair.utils import AltairDeprecationWarning
from altair.utils.deprecation import deprecated


def test_deprecated_class():
    class Dummy:
        def __init__(self, *args) -> None:
            self.args = args

    OldChart = deprecated("", version="", alternative="LayerChart")(Dummy)
    with pytest.warns(AltairDeprecationWarning, match=r"alt\.Dummy.+alt\.LayerChart"):
        OldChart()


def test_deprecation_decorator():
    @deprecated("", version="999", alternative="12345")
    def func(x):
        return x + 1

    with pytest.warns(
        AltairDeprecationWarning, match=r"alt\.func.+altair=999.+12345 instead"
    ):
        y = func(1)
    assert y == 2
