"""
Regression tests for skip-mode handling in SolverAnalysisHandler.
"""

import os
import sys
from types import SimpleNamespace


# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.handlers.analysis_handler import SolverAnalysisHandler


class _FakeCombo:
    def __init__(self, text="", visible=True):
        self._text = text
        self._visible = visible

    def currentText(self):
        return self._text

    def isVisible(self):
        return self._visible


def test_skip_modes_are_read_even_when_combo_is_not_visible():
    tab = SimpleNamespace(
        skip_modes_combo=_FakeCombo(text="6", visible=False),
        skip_last_modes_combo=_FakeCombo(text="2", visible=False),
    )
    handler = SolverAnalysisHandler(tab)

    assert handler._get_skip_n_modes() == 6
    assert handler._get_skip_last_n_modes() == 2


def test_skip_modes_default_to_zero_for_blank_or_invalid_values():
    tab = SimpleNamespace(
        skip_modes_combo=_FakeCombo(text="", visible=True),
        skip_last_modes_combo=_FakeCombo(text="not-a-number", visible=True),
    )
    handler = SolverAnalysisHandler(tab)

    assert handler._get_skip_n_modes() == 0
    assert handler._get_skip_last_n_modes() == 0
