from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factorysoftware.adapters import registry
from factorysoftware.architecture.validator import validate_architecture as _validate_arch
from factorysoftware.installer import install_all, update_all, uninstall_all
from factorysoftware.requirements.validator import validate_requirements
from factorysoftware.construction.validator import validate_construction
from factorysoftware.construction.triage import decide_dimensions
from factorysoftware.state import (
    append_log,
    read_log,
    read_manifest,
    query_step_status,
    write_board,
    write_metrics,
)


def _default_content_dir() -> Path:
    return Path(__file__).parent / "content"


def _resolve_adapters(project_root: Path, providers_override: list[str] | None):
    if providers_override:
        return registry.select(providers_override)
    return registry.detect(project_root)


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    content_dir = Path(args.content_dir) if args.content_dir else _default_content_dir()

    if read_manifest(project_root) is not None:
        return cmd_update(args)

    providers_override = args.providers.split(",") if args.providers else None
    adapters = _resolve_adapters(project_root, providers_override)
    if not adapters:
        print(
            "No se detectó ningún proveedor en este proyecto. "
            "Usá --providers <nombre> para forzar uno.",
            file=sys.stderr,
        )
        return 1

    install_all(project_root, content_dir, adapters)
    print(f"Instalado para: {', '.join(a.name for a in adapters)}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    content_dir = Path(args.content_dir) if args.content_dir else _default_content_dir()

    manifest = read_manifest(project_root)
    if manifest is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1

    providers_override = args.providers.split(",") if args.providers else None
    adapters = _resolve_adapters(project_root, providers_override)
    if not adapters:
        adapters = registry.select(manifest.providers)

    _, warnings = update_all(project_root, content_dir, adapters)
    for w in warnings:
        print(f"Advertencia: {w}", file=sys.stderr)
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    if read_manifest(project_root) is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1
    warnings = uninstall_all(project_root)
    for w in warnings:
        print(f"Advertencia: {w}", file=sys.stderr)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    manifest = read_manifest(project_root)
    if manifest is None:
        print("No hay instalación previa. Corré 'factory init' primero.", file=sys.stderr)
        return 1

    write_metrics(project_root)

    if args.step:
        if "." not in args.step:
            print(
                f"--step debe tener el formato <fase>.<paso> (recibido: '{args.step}').",
                file=sys.stderr,
            )
            return 1
        phase, step_id = args.step.split(".", 1)
        print(query_step_status(project_root, phase, step_id, args.fan_out_index))
        return 0

    if args.write:
        write_board(project_root)
        print("Tablero regenerado en .factory/board.md")
        return 0

    print(f"Versión instalada: {manifest.version}")
    print(f"Proveedores: {', '.join(manifest.providers)}")
    events = read_log(project_root)
    print(f"Eventos registrados: {len(events)}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    try:
        data = json.loads(args.data) if args.data else {}
    except json.JSONDecodeError as e:
        print(f"--data no es JSON válido: {e}", file=sys.stderr)
        return 1
    append_log(project_root, args.event_type, data)
    return 0


def cmd_validate_requirements(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root)
    log_path = Path(args.log)
    errors = validate_requirements(project_root, log_path)
    for e in errors:
        print(e)
    return 1 if errors else 0


def cmd_validate_architecture(args) -> int:
    errors = _validate_arch(Path(args.project_root))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


def cmd_validate_construction(args: argparse.Namespace) -> int:
    errors = validate_construction(Path(args.project_root))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


def cmd_audit_triage(args: argparse.Namespace) -> int:
    import subprocess
    project_root = Path(args.project_root)
    epic = args.epic
    base = args.base
    plan_path = project_root / "docs" / "construction" / "plan" / f"{epic}.md"
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    try:
        diff_text = subprocess.run(
            ["git", "diff", f"{base}...HEAD"], capture_output=True, text=True, cwd=project_root
        ).stdout
    except FileNotFoundError:
        diff_text = ""
        
    dims = decide_dimensions(diff_text, plan_text)
    print(", ".join(dims))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="factory")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn in (("init", cmd_init), ("update", cmd_update)):
        p = sub.add_parser(name)
        p.add_argument("--project-root", default=".")
        p.add_argument("--content-dir", default=None)
        p.add_argument("--providers", default=None)
        p.set_defaults(func=fn)

    p = sub.add_parser("uninstall")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("status")
    p.add_argument("--project-root", default=".")
    p.add_argument("--write", action="store_true")
    p.add_argument("--step", default=None, help="<phase>.<step_id>")
    p.add_argument("--fan-out-index", type=int, default=None)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("log")
    p.add_argument("event_type")
    p.add_argument("--project-root", default=".")
    p.add_argument("--data", default=None)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("audit-triage")
    p.add_argument("--epic", required=True)
    p.add_argument("--base", default="develop", help="Base branch for git diff")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_audit_triage)

    # validate <subcommand>
    validate_p = sub.add_parser("validate")
    validate_sub = validate_p.add_subparsers(dest="validate_command", required=True)

    p = validate_sub.add_parser("requirements")
    p.add_argument("--project-root", default=".")
    p.add_argument("--log", default=".factory/log.jsonl")
    p.set_defaults(func=cmd_validate_requirements)

    p = validate_sub.add_parser("architecture")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_validate_architecture)

    p = validate_sub.add_parser("construction")
    p.add_argument("--project-root", default=".")
    p.set_defaults(func=cmd_validate_construction)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
