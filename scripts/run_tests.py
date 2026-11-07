"""Run tests against the exact release runtime and its official pytest fixtures.

See home-assistant/core packages/pytest-homeassistant at tag 2026.11.0.
No Home Assistant implementation or test fixture is patched by this runner.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import os
from pathlib import Path
import sys

EXPECTED_VERSION = "2026.11.0"


def main() -> int:
    """Validate dependencies before pytest loads any plugins."""
    for distribution in ("homeassistant", "pytest-homeassistant"):
        try:
            installed = version(distribution)
        except PackageNotFoundError:
            raise SystemExit(f"Install requirements-test.txt: {distribution} is missing") from None
        if installed != EXPECTED_VERSION:
            raise SystemExit(
                f"Expected {distribution}=={EXPECTED_VERSION}, found {installed}. "
                "Install requirements-test.txt in an isolated environment."
            )
    try:
        version("pytest-homeassistant-custom-component")
    except PackageNotFoundError:
        pass
    else:
        raise SystemExit(
            "Uninstall pytest-homeassistant-custom-component before running tests: "
            "it conflicts with the official pytest-homeassistant fixtures."
        )
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))

    # HA installs its supported httpx2 alias before any third-party pytest plugin
    # can import httpx. pyproject also follows the official -p no:respx setting.
    import homeassistant  # noqa: F401
    import pytest

    print(f"Home Assistant {EXPECTED_VERSION}; official pytest-homeassistant {EXPECTED_VERSION}")
    return pytest.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
