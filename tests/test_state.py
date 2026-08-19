import json
from pathlib import Path
from factorysoftware.state import (
    compute_hash,
    Manifest,
    ManifestFile,
    read_manifest,
    write_manifest,
    append_log,
    read_log,
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


def test_read_log_empty_when_missing(tmp_path: Path):
    assert read_log(tmp_path) == []


def test_append_log_then_read_roundtrip(tmp_path: Path):
    append_log(tmp_path, "pipeline_step", {"phase": "requirements", "step_id": "prd"})
    append_log(tmp_path, "phase_gate", {"phase": "requirements", "result": "approved"})
    events = read_log(tmp_path)
    assert len(events) == 2
    assert events[0]["event_type"] == "pipeline_step"
    assert events[0]["data"]["step_id"] == "prd"
    assert "ts" in events[0]
    assert events[1]["event_type"] == "phase_gate"


def test_append_log_is_append_only(tmp_path: Path):
    append_log(tmp_path, "a", {})
    append_log(tmp_path, "b", {})
    lines = (tmp_path / ".factory" / "log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    json.loads(lines[0])
    json.loads(lines[1])
