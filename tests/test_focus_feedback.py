"""Tests for focus-feedback.py"""
import sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent.parent))
focus = import_module('focus-feedback')


def test_import():
    """Script imports without error."""
    assert focus is not None
