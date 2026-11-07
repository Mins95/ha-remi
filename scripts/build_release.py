"""Build and verify the integration ZIP consumed by Marketplace and HACS."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

DOMAIN = "urbanhello_remi_unofficial"
COMPONENT = PurePosixPath("custom_components") / DOMAIN
ASSET_NAME = f"{DOMAIN}.zip"
VERSION_PATTERN = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-beta\.[1-9][0-9]*)?"
)
REQUIRED_FILES = {
    "LICENSE",
    "__init__.py",
    "manifest.json",
    "services.yaml",
    "strings.json",
    "translations/en.json",
    "translations/fr.json",
    "www/remi-card.js",
    "www/remi-loader.js",
}
EXCLUDED_DIRECTORIES = {"__pycache__", ".pytest_cache", "tests", "docs"}


def _read_sources(repository: Path) -> dict[str, bytes]:
    """Read regular tracked component files, never local or ignored scratch files."""
    tracked = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", COMPONENT.as_posix()],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    component_root = repository.joinpath(*COMPONENT.parts).resolve()
    sources: dict[str, bytes] = {}
    for entry in tracked.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.decode("utf-8").split("\t", 1)
        mode, _object_id, stage = metadata.split()
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts or "\\" in raw_path:
            raise ValueError("Tracked component path is unsafe")
        relative = path.relative_to(COMPONENT)
        if (
            any(part.startswith(".") or part in EXCLUDED_DIRECTORIES for part in relative.parts)
            or relative.suffix in {".pyc", ".pyo", ".log"}
        ):
            continue
        if mode not in {"100644", "100755"} or stage != "0":
            raise ValueError("Release files must be regular files without Git conflicts")
        source = repository.joinpath(*path.parts)
        if source.is_symlink() or not source.resolve().is_relative_to(component_root):
            raise ValueError("Release files must stay inside the integration directory")
        name = relative.as_posix()
        if name in sources:
            raise ValueError("Release contains a duplicate path")
        sources[name] = source.read_bytes()
    missing = REQUIRED_FILES - sources.keys()
    if missing:
        raise ValueError(f"Required release files are missing: {', '.join(sorted(missing))}")
    return sources


def _validate_sources(sources: dict[str, bytes], version: str | None) -> str:
    """Check the identity, version and JSON shipped in the archive."""
    parsed = {
        name: json.loads(content)
        for name, content in sources.items()
        if name.endswith(".json")
    }
    manifest = parsed["manifest.json"]
    if not isinstance(manifest, dict) or manifest.get("domain") != DOMAIN:
        raise ValueError("Release manifest has the wrong integration domain")
    actual = manifest.get("version")
    if not isinstance(actual, str) or not VERSION_PATTERN.fullmatch(actual):
        raise ValueError("Release manifest has an invalid version")
    if version is not None and actual != version:
        raise ValueError("Requested release version does not match manifest.json")
    return actual


def validate_archive(archive: Path, sources: dict[str, bytes]) -> None:
    """Verify root layout, file membership, CRCs and every packaged byte."""
    with ZipFile(archive) as package:
        names = package.namelist()
        if len(names) != len(set(names)) or set(names) != set(sources):
            raise ValueError("Release ZIP contents differ from the selected source files")
        if package.testzip() is not None:
            raise ValueError("Release ZIP failed its integrity check")
        for name, content in sources.items():
            if package.read(name) != content:
                raise ValueError(f"Release ZIP differs from source: {name}")


def build_release(repository: Path, output: Path, version: str | None = None) -> Path:
    """Build a deterministic archive and replace the output only after validation."""
    repository = repository.resolve()
    output = output.resolve()
    if output.name != ASSET_NAME:
        raise ValueError(f"Release archive must be named {ASSET_NAME}")
    if output.is_relative_to(repository.joinpath(*COMPONENT.parts)):
        raise ValueError("Release archive must be outside the integration directory")
    hacs = json.loads((repository / "hacs.json").read_text(encoding="utf-8"))
    if hacs.get("zip_release") is not True or hacs.get("filename") != ASSET_NAME:
        raise ValueError("hacs.json must select this ZIP release asset")
    sources = _read_sources(repository)
    _validate_sources(sources, version)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=output.parent, suffix=".zip")
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as package:
            for name, content in sorted(sources.items()):
                entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = ZIP_DEFLATED
                package.writestr(entry, content, compresslevel=9)
        validate_archive(temporary, sources)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> int:
    """Build the checked-out version; release CI additionally requires an exact version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Require this exact manifest version")
    parser.add_argument("--output", type=Path, default=Path("dist") / ASSET_NAME)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    archive = build_release(repository, args.output, args.version)
    print(f"Verified release archive: {archive.name} ({archive.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
