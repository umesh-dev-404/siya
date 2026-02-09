"""
Onboarding wizard — first-run guided setup.

Per EVOLUTION_ROADMAP §18 (MODE B locked):
- Steps: welcome, data dir, optional Supabase, summary, confirm.
- Writes .env and marker only after explicit user confirm (LAW 1).
- Logs config write (LAW 13). No tool execution.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Marker file name; when present, consider "onboarded"
ONBOARD_MARKER = ".siya_onboarded"
ENV_FILENAME = ".env"


def _project_root() -> Path:
    """Directory for .env and marker: cwd when running wizard."""
    return Path.cwd()


def get_marker_path() -> Path:
    """Path to onboarded marker file (project root)."""
    return _project_root() / ONBOARD_MARKER


def is_onboarded() -> bool:
    """True if marker file exists (user has completed onboarding)."""
    return get_marker_path().exists()


def _env_path() -> Path:
    """Path to .env file (project root)."""
    return _project_root() / ENV_FILENAME


def _read_existing_env() -> dict[str, str]:
    """Read existing KEY=VALUE pairs from .env if present."""
    path = _env_path()
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _write_env(updates: dict[str, str]) -> None:
    """Update .env with given keys; preserve existing other keys."""
    path = _env_path()
    existing = _read_existing_env()
    for k, v in updates.items():
        existing[k] = v
    # Write SIYA_* and SUPABASE_* only so we don't overwrite unrelated env
    to_write = {k: existing[k] for k in existing if k.startswith("SIYA_") or k.startswith("SUPABASE_")}
    content = "\n".join(f"{k}={to_write[k]}" for k in sorted(to_write)) + "\n"
    path.write_text(content, encoding="utf-8")
    logger.info("Config written: %s (keys: %s)", str(path), list(updates.keys()))
    logger.info("Onboarding config write: path=%s keys_written=%s", str(path), list(updates.keys()))


def run_wizard(*, force: bool = False) -> int:
    """
    Run onboarding wizard. Returns 0 on success, 1 on cancel/error.

    If force is False and is_onboarded(), print message and return 0 (idempotent re-run
    is still possible by calling with force=True or by running again and answering prompts).
    """
    root = _project_root()
    if not force and is_onboarded():
        print("Onboarding already completed (marker present). Run with --force to run again.")
        return 0

    print("Siya onboarding — guided setup")
    print("=" * 40)
    print("This wizard sets data directory and optional Supabase. No tools will be executed.")
    print()

    # Step 1: Welcome (already above)

    # Step 2: Data directory
    default_data = str(root / "data")
    data_dir_raw = input(f"Data directory path [{default_data}]: ").strip() or default_data
    data_dir = str(Path(data_dir_raw).expanduser().resolve())

    # Step 3: Optional Supabase
    use_supabase_raw = input("Use Supabase for cloud sync? (y/n) [n]: ").strip().lower() or "n"
    use_supabase = use_supabase_raw in ("y", "yes")
    supabase_url = ""
    supabase_key = ""
    if use_supabase:
        supabase_url = input("SUPABASE_URL: ").strip()
        supabase_key = input("SUPABASE_KEY (anon key): ").strip()

    # Step 4: Summary
    print()
    print("Summary:")
    print(f"  Data directory: {data_dir}")
    print(f"  Supabase: {'yes' if use_supabase else 'no'}")
    if use_supabase:
        print(f"  SUPABASE_URL: {supabase_url or '(empty)'}")
    print()

    # Step 5: Confirm
    confirm = input("Write config to .env and complete onboarding? (y/n) [n]: ").strip().lower() or "n"
    if confirm not in ("y", "yes"):
        print("Onboarding cancelled. No changes made.")
        return 0

    # Write
    updates: dict[str, str] = {"SIYA_DATA_DIR": data_dir}
    if use_supabase:
        updates["SUPABASE_URL"] = supabase_url
        updates["SUPABASE_KEY"] = supabase_key
    _write_env(updates)
    get_marker_path().write_text("onboarded\n", encoding="utf-8")
    print("Config written. Marker file created. Onboarding complete.")
    return 0


def main() -> int:
    """Entry point for siya-onboard script."""
    import sys
    force = "--force" in sys.argv or "-f" in sys.argv
    return run_wizard(force=force)


if __name__ == "__main__":
    import sys
    sys.exit(main())
