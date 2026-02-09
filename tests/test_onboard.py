"""Tests for onboarding wizard (EVOLUTION_ROADMAP §18)."""

import pytest

from cli.onboard import ONBOARD_MARKER, get_marker_path, is_onboarded


class TestOnboardDetection:
    """Marker path and onboarded detection."""

    def test_get_marker_path_returns_path_with_marker_name(self):
        """get_marker_path() returns a Path ending with .siya_onboarded."""
        p = get_marker_path()
        assert p.name == ONBOARD_MARKER

    def test_is_onboarded_false_when_marker_missing(self, tmp_path, monkeypatch):
        """is_onboarded() is False when marker file does not exist."""
        monkeypatch.setattr("cli.onboard._project_root", lambda: tmp_path)
        assert is_onboarded() is False

    def test_is_onboarded_true_when_marker_exists(self, tmp_path, monkeypatch):
        """is_onboarded() is True when marker file exists."""
        monkeypatch.setattr("cli.onboard._project_root", lambda: tmp_path)
        (tmp_path / ONBOARD_MARKER).write_text("onboarded\n")
        assert is_onboarded() is True
