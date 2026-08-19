from __future__ import annotations

import argparse
import sys
from pathlib import Path

from factorysoftware.adapters import registry
from factorysoftware.installer import install_all, update_all, uninstall_all
from factorysoftware.state import read_manifest


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

    providers_override = args.providers.split(",") if getattr(args, "providers", None) else None
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
