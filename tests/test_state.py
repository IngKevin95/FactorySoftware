from pathlib import Path
from factorysoftware.state import (
    compute_hash,
    Manifest,
    ManifestFile,
    read_manifest,
    write_manifest,
)


def test_package_imports():
    import factorysoftware


def test_compute_hash_is_deterministic():
    assert compute_hash("abc") == compute_hash("abc")
    assert compute_hash("abc") != compute_hash("abd")


def test_read_manifest_returns_none_when_missing(tmp_path: Path):
    assert read_manifest(tmp_path) is None


def test_write_then_read_manifest_roundtrip(tmp_path: Path):
    manifest = Manifest(
        version="0.1.0",
        installed_at="2026-08-19T00:00:00Z",
        providers=["claude_code"],
        files=[ManifestFile(path=".claude/skills/x/SKILL.md", hash="abc", skill_id="requirements-prd")],
    )
    write_manifest(tmp_path, manifest)
    loaded = read_manifest(tmp_path)
    assert loaded == manifest


def test_write_manifest_creates_factory_dir(tmp_path: Path):
    manifest = Manifest(version="0.1.0", installed_at="t", providers=[], files=[])
    write_manifest(tmp_path, manifest)
    assert (tmp_path / ".factory" / "manifest.json").exists()
