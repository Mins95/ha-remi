"""Check the installable ZIP layout and prevent accidental source leakage."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import pytest

from scripts.build_release import (
    ASSET_NAME,
    COMPONENT,
    DOMAIN,
    REQUIRED_FILES,
    build_release,
    validate_archive,
)


@pytest.fixture
def package_repository(tmp_path: Path) -> Path:
    """Make a small Git index with the same install layout as the integration."""
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    component = tmp_path.joinpath(*COMPONENT.parts)
    for name in REQUIRED_FILES | {"brand/icon.png"}:
        path = component / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}" if path.suffix == ".json" else b"fixture\n")
    (component / "manifest.json").write_text(
        json.dumps({"domain": DOMAIN, "version": "0.5.0"}), encoding="utf-8"
    )
    (tmp_path / "hacs.json").write_text(
        json.dumps({"zip_release": True, "filename": ASSET_NAME}), encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    return tmp_path


def test_package_is_installable_and_reproducible(package_repository: Path) -> None:
    """Manifest/assets are at the ZIP root, with only tracked integration bytes."""
    component = package_repository.joinpath(*COMPONENT.parts)
    (component / "scratch.py").write_text("not tracked", encoding="utf-8")
    (component / "__pycache__").mkdir()
    (component / "__pycache__/cached.pyc").write_bytes(b"not shipped")
    (package_repository / "private-notes.txt").write_text("outside component")
    output = package_repository / "dist" / ASSET_NAME
    build_release(package_repository, output, "0.5.0")
    first = output.read_bytes()
    build_release(package_repository, output, "0.5.0")
    assert output.read_bytes() == first
    with ZipFile(output) as archive:
        assert set(archive.namelist()) == REQUIRED_FILES | {"brand/icon.png"}
        assert json.loads(archive.read("manifest.json"))["domain"] == DOMAIN
        assert archive.read("www/remi-card.js") == b"fixture\n"
        assert all(not name.startswith("custom_components/") for name in archive.namelist())


def test_tracked_caches_tests_and_docs_are_excluded(package_repository: Path) -> None:
    """Even accidentally tracked build artefacts cannot enter the release ZIP."""
    component = package_repository.joinpath(*COMPONENT.parts)
    for name in ("__pycache__/cached.pyc", "tests/test.py", "docs/notes.md", ".env"):
        path = component / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"exclude")
    subprocess.run(["git", "add", "."], cwd=package_repository, check=True)
    output = build_release(package_repository, package_repository / "dist" / ASSET_NAME)
    with ZipFile(output) as archive:
        assert set(archive.namelist()) == REQUIRED_FILES | {"brand/icon.png"}


@pytest.mark.parametrize("missing", ["www/remi-loader.js", "LICENSE"])
def test_missing_required_file_fails_before_overwriting_package(
    package_repository: Path, missing: str
) -> None:
    """Frontend and license files must ship; a bad build preserves any prior ZIP."""
    output = package_repository / ASSET_NAME
    output.write_bytes(b"previous release")
    subprocess.run(
        ["git", "rm", "--cached", "--quiet", str(COMPONENT / missing)],
        cwd=package_repository,
        check=True,
    )
    with pytest.raises(ValueError, match="Required release files are missing"):
        build_release(package_repository, output)
    assert output.read_bytes() == b"previous release"


@pytest.mark.parametrize("domain,version,requested", [
    ("another_domain", "0.5.0", "0.5.0"),
    (DOMAIN, "invalid", None),
    (DOMAIN, "0.5.0-beta.2", "0.5.0"),
])
def test_wrong_identity_or_version_is_rejected(
    package_repository: Path, domain: str, version: str, requested: str | None
) -> None:
    manifest = package_repository.joinpath(*COMPONENT.parts) / "manifest.json"
    manifest.write_text(json.dumps({"domain": domain, "version": version}), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        build_release(package_repository, package_repository / ASSET_NAME, requested)
    assert not (package_repository / ASSET_NAME).exists()


def test_hacs_asset_configuration_must_match(package_repository: Path) -> None:
    (package_repository / "hacs.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hacs.json"):
        build_release(package_repository, package_repository / ASSET_NAME)


def test_symlink_git_entry_is_rejected(package_repository: Path) -> None:
    """Reject Git symlink modes even when the platform checks them out as text."""
    target = (COMPONENT / "__init__.py").as_posix()
    object_id = subprocess.run(
        ["git", "hash-object", target], cwd=package_repository,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "update-index", "--cacheinfo", f"120000,{object_id},{target}"],
        cwd=package_repository, check=True,
    )
    with pytest.raises(ValueError, match="regular files"):
        build_release(package_repository, package_repository / ASSET_NAME)


def test_archive_validation_rejects_extra_files_and_changed_bytes(tmp_path: Path) -> None:
    archive = tmp_path / ASSET_NAME
    with ZipFile(archive, "w") as package:
        package.writestr("manifest.json", b"changed")
    with pytest.raises(ValueError, match="differs from source"):
        validate_archive(archive, {"manifest.json": b"expected"})
    with pytest.raises(ValueError, match="contents differ"):
        validate_archive(archive, {})
