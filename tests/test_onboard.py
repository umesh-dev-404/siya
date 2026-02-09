"""Tests for onboarding wizard (EVOLUTION_ROADMAP §18)."""

import pytest

from cli.onboard import ONBOARD_MARKER, apply_onboarding, get_marker_path, is_onboarded


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


class TestApplyOnboarding:
    """apply_onboarding() writes .env and marker."""

    def test_apply_creates_marker_and_env(self, tmp_path, monkeypatch):
        """apply_onboarding() creates marker and .env with SIYA_DATA_DIR."""
        monkeypatch.setattr("cli.onboard._project_root", lambda: tmp_path)
        apply_onboarding(str(tmp_path / "data"), use_supabase=False)
        assert (tmp_path / ONBOARD_MARKER).exists()
        env = tmp_path / ".env"
        assert env.exists()
        content = env.read_text(encoding="utf-8")
        assert "SIYA_DATA_DIR" in content

    def test_apply_raises_on_empty_data_dir(self, tmp_path, monkeypatch):
        """apply_onboarding() raises ValueError when data_dir is empty or blank."""
        monkeypatch.setattr("cli.onboard._project_root", lambda: tmp_path)
        with pytest.raises(ValueError, match="required"):
            apply_onboarding("")
        with pytest.raises(ValueError, match="required"):
            apply_onboarding("   ")
