# Factory Core + Provider Agnosticism Layer — Design

Status: approved
Subsystem: 1 of N (core) — see `docs/superpowers/specs/README.md` for full decomposition index once created.

## Purpose

Provide a vendor-agnostic installable package that scaffolds a multi-phase SDLC
skill system (requirements -> architecture/design -> construction -> QA) into
any software project, adapted to whichever AI coding assistant(s) are present
in that project (Claude Code, GitHub Copilot, OpenAI Codex CLI, OpenCode,
Antigravity), with full lifecycle management (install/update/uninstall) and
local traceability/metrics.

This spec covers only the **core**: the installer, provider adapters, and
state/traceability mechanism. The actual phase content (requirements skill,
architecture skill, etc.) and project-type packs (backend/mobile/security/...)
are separate subsystems with their own specs, built on top of this core.

## Non-goals (v1)

- Calling any LLM API directly. The package never talks to a model; it only
  writes instruction files that an already-running AI assistant reads.
- Remote/cloud telemetry. All logs and metrics stay local to the project
  (`.factory/`), nothing is transmitted anywhere.
- Full phase content (requirements/architecture/construction/QA skills) —
  those are separate specs. This core only defines *how* such content gets
  rendered and installed per provider.
- Project-type-specific packs (backend, mobile, security, automations,
  agents, ...) — deferred, core only defines the extension point.

## Architecture

Python package `factorysoftware`, distributed via pip/uv. Three layers:

1. **Content** — provider-agnostic markdown source files (one file per skill,
   YAML frontmatter for name/description + body). Single source of truth.
2. **Adapters** — one Python module per provider. Each adapter knows how to
   detect the provider in a project and how to render/place content in that
   provider's expected format and location.
3. **CLI + state** — lifecycle commands and a local append-only log/manifest
   used for traceability and metrics.

```
src/factorysoftware/
  cli.py                  # init, update, uninstall, status, log
  adapters/
    base.py                # ProviderAdapter protocol
    claude_code.py
    copilot.py
    codex.py
    opencode.py
    antigravity.py
    registry.py             # detect() -> list[ProviderAdapter] present in project
  content/                 # *.md source, single source of truth
    advisor.md
    requirements.md
    architecture.md
    construction.md
    qa.md
  render.py                 # (content, adapter) -> rendered file(s)
  state.py                  # manifest.json, log.jsonl, metrics.json
tests/
  test_adapters.py
  test_render.py
  test_state.py
  test_cli.py
```

## ProviderAdapter interface

```python
class ProviderAdapter(Protocol):
    name: str

    def detect(self, project_root: Path) -> bool: ...
    def target_paths(self, skill_ids: list[str]) -> dict[str, Path]: ...
    def render(self, skill_id: str, content_md: str) -> str: ...
```

- `detect`: looks for provider fingerprints (`.claude/`, `.github/copilot*`,
  `AGENTS.md` conventions, provider-specific config files).
- `target_paths`: maps each skill id to the file path that provider expects
  (may collapse multiple skill ids into one file for single-file providers).
- `render`: converts the shared markdown content into that provider's
  expected format (frontmatter shape, wrapping, concatenation).

### Per-provider notes (v1, basic)

- **Claude Code**: multi-file, `.claude/skills/<id>/SKILL.md`, YAML
  frontmatter `name`/`description`.
- **GitHub Copilot**: single file `.github/copilot-instructions.md`,
  concatenates all phase content with headers.
- **OpenAI Codex CLI**: single file `AGENTS.md` at repo root, plain markdown,
  no frontmatter.
- **OpenCode**: treated like Codex (`AGENTS.md` convention) for v1 basic
  adapter — verify against current docs before implementing, format may
  differ.
- **Antigravity**: format not confidently known from current knowledge.
  Adapter ships as best-effort; implementation task must include a web-search
  verification step before writing it. If no reliable format is found,
  fall back to a generic `AGENTS.md`-style file and flag it in the manifest
  as `"confidence": "unverified"`.

## Lifecycle commands

- `factory init [--providers claude,copilot,...]`
  Detects providers present (registry.detect). If none detected, prompts
  interactively which to install for. Renders content via each matched
  adapter, writes files, records each written path + content hash in
  `.factory/manifest.json`.

- `factory update`
  Re-renders content from the currently installed package version. For each
  previously-written file: if its on-disk hash still matches the manifest
  hash (untouched by user), overwrite with the new render and update the
  manifest hash + version. If the hash differs (user edited it manually),
  skip and print a warning listing the file — never silently overwrite user
  edits.

- `factory uninstall`
  Reads `.factory/manifest.json`, deletes exactly the files it lists (skips
  any whose hash no longer matches, warns instead of deleting), then removes
  the manifest. Never touches files it didn't write.

- `factory status`
  Reads `.factory/log.jsonl` and `.factory/manifest.json`, prints: installed
  version, detected providers, current phase (from latest phase-transition
  event), QA coverage metrics, skill invocation counts.

- `factory log <event_type> [--data '<json>']`
  Appends one line to `.factory/log.jsonl`: `{"ts", "event_type", "data"}`.
  This is the hook phase-content skills call (via Bash/shell, since any
  agent capable of running the factory skills can run a shell command) after
  phase transitions, artifact creation, and — critically — advisor
  disagreements, so audits can reconstruct what happened and why.

## State files (`.factory/`, git-tracked by default)

- `manifest.json` — `{version, installed_at, providers: [...], files: [{path, hash, skill_id}]}`
- `log.jsonl` — append-only event stream, one JSON object per line
- `metrics.json` — computed cache (rebuilt from log.jsonl by `factory status`),
  not hand-edited

## Advisor/auditor blocking behavior (cross-cutting, defined here since it
affects the log schema)

The advisor persona (content spec, separate file) requires the agent to
present pros/cons and an honest recommendation on every significant decision,
even when it disagrees with the user. For a defined set of critical-risk
categories (security, data loss, silently skipped tests, irreversible
infra/deploy actions) the skill instructs the agent to require an explicit
extra confirmation step before proceeding, and to log the disagreement via
`factory log advisor_block '{"category": ..., "reason": ..., "user_override": bool}'`.
Non-critical disagreements are logged via `factory log advisor_note` but do
not block.

## Error handling

- `update`/`uninstall` never delete or overwrite a file whose hash doesn't
  match the manifest — always warn and skip instead.
- `init` run twice on an already-installed project: detected as "already
  installed" (manifest exists) — behaves like `update`, not a duplicate
  install.
- Missing `.factory/manifest.json` when running `update`/`uninstall`/`status`:
  clear error telling the user to run `init` first.
- Adapter `detect()` raising or a target path not writable: that provider is
  skipped with a warning, other providers still proceed (partial install is
  valid and recorded in the manifest).

## Testing

pytest + pytest-mock, zero external IO (no real network, no real package
registries). Filesystem operations exercised via `tmp_path`. Per Beck rules:

- `test_adapters.py`: one test per adapter for `detect()` (positive/negative
  fixture project trees) and `render()` (snapshot of rendered output).
- `test_render.py`: content -> multi-provider rendering produces expected
  file sets.
- `test_state.py`: manifest hash tracking, log append-only invariant,
  metrics aggregation from a fixture log.
- `test_cli.py`: init/update/uninstall idempotency and the "don't clobber
  user edits" behavior specifically (this is the one non-trivial branch in
  the whole system — gets a dedicated test).

## Open questions / risks flagged for the implementation plan

- Antigravity's actual skill-loading convention needs verification via web
  search before that adapter is implemented for real — do not fabricate the
  format.
- OpenCode's current convention should also be confirmed, not assumed
  identical to Codex.
