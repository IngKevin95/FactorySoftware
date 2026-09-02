from pathlib import Path
import re

VALID_ROLES = {"backend", "data", "frontend", "seguridad", "automatizaciones", "mobile"}

def validate_construction(
    project_root: Path, content_roles_dir: Path | None = None
) -> list[str]:
    errors = []
    
    # Collect valid implementations
    valid_impls = set()
    apis_dir = project_root / "docs" / "architecture" / "apis"
    if apis_dir.exists():
        for p in apis_dir.glob("*.md"):
            valid_impls.add(p.stem)
            
    screens_dir = project_root / "docs" / "architecture" / "screens"
    if screens_dir.exists():
        for p in screens_dir.glob("*.md"):
            valid_impls.add(p.stem)

    # Parse tasks
    plan_dir = project_root / "docs" / "construction" / "plan"
    if not plan_dir.exists():
        return errors

    tasks = {}

    for file_path in plan_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        current_task = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("### TASK-"):
                current_task = line.replace("###", "").strip()
                tasks[current_task] = {"rol": None, "implementa": None, "depende_de": []}
            elif current_task:
                if line.startswith("- rol:"):
                    tasks[current_task]["rol"] = line.split(":", 1)[1].strip()
                elif line.startswith("- implementa:"):
                    tasks[current_task]["implementa"] = line.split(":", 1)[1].strip()
                elif line.startswith("- depende_de:"):
                    deps_str = line.split(":", 1)[1].strip()
                    if deps_str.startswith("[") and deps_str.endswith("]"):
                        deps = [d.strip() for d in deps_str[1:-1].split(",") if d.strip()]
                        tasks[current_task]["depende_de"] = deps
    
    # Validate
    for task_id, t in tasks.items():
        if t["rol"] and t["rol"] not in VALID_ROLES:
            errors.append(f"Task {task_id} has invalid role: {t['rol']}")
        elif t["rol"] and content_roles_dir is not None:
            pack = content_roles_dir / f"{t['rol']}.md"
            if not pack.exists():
                errors.append(
                    f"Task {task_id} uses role '{t['rol']}' with no content pack "
                    f"at {pack} — no hay agente real para despachar esta tarea"
                )

        if t["implementa"] and t["implementa"] not in valid_impls:
            errors.append(f"Task {task_id} references missing implementation: {t['implementa']}")
            
    # Check circular dependencies
    def has_cycle(node, visited, path):
        visited.add(node)
        path.add(node)
        for dep in tasks.get(node, {}).get("depende_de", []):
            if dep not in visited:
                if has_cycle(dep, visited, path):
                    return True
            elif dep in path:
                return True
        path.remove(node)
        return False

    visited = set()
    for task_id in tasks:
        if task_id not in visited:
            path = set()
            if has_cycle(task_id, visited, path):
                errors.append(f"Circular dependency detected involving {task_id}")

    return errors
