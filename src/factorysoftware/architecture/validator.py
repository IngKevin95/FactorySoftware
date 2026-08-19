from pathlib import Path
import yaml
import re

def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
        return yaml.safe_load(text[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}

def validate_architecture(project_root: Path) -> list[str]:
    docs = project_root / "docs"
    arch = docs / "architecture"
    reqs = docs / "requirements"
    errors = []
    
    hu_files = list((reqs / "stories").glob("HU-*.md")) if (reqs / "stories").exists() else []
    hu_active = {f.stem for f in hu_files if "retiradas" not in f.parts}
    
    apis = list((arch / "apis").glob("API-*.md")) if (arch / "apis").exists() else []
    api_ids = {f.stem for f in apis}
    
    screens = list((arch / "screens").glob("SCREEN-*.md")) if (arch / "screens").exists() else []
    screen_ids = {f.stem for f in screens}
    
    # 1. & 2. HU with anexo
    for hu_path in hu_files:
        if "retiradas" in hu_path.parts:
            continue
        text = hu_path.read_text(encoding="utf-8")
        if "anexo endpoint" in text.lower():
            implemented = False
            for api in apis:
                fm = _parse_frontmatter(api.read_text(encoding="utf-8"))
                if hu_path.stem in fm.get("implementa", []):
                    implemented = True
                    break
            if not implemented:
                errors.append(f"Check 1: HU '{hu_path.stem}' requests an endpoint but no API-N.md implements it")
        
        if "anexo pantalla" in text.lower():
            implemented = False
            for screen in screens:
                fm = _parse_frontmatter(screen.read_text(encoding="utf-8"))
                if hu_path.stem in fm.get("implementa", []):
                    implemented = True
                    break
            if not implemented:
                errors.append(f"Check 2: HU '{hu_path.stem}' requests a screen but no SCREEN-N.md implements it")
                
    # 3. apis_consumidas must exist
    for screen in screens:
        fm = _parse_frontmatter(screen.read_text(encoding="utf-8"))
        for api_ref in fm.get("apis_consumidas", []):
            if api_ref not in api_ids:
                errors.append(f"Check 3: {screen.stem} apis_consumidas '{api_ref}' not found")
                
    # 4. implementa valid HU
    for f in apis + screens:
        fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
        for hu in fm.get("implementa", []):
            if hu not in hu_active:
                errors.append(f"Check 4: {f.stem} implements '{hu}' which is not active")

    # 6. screens have prototypes
    proto_dir = project_root / "prototype"
    proto_files = {f.stem for f in proto_dir.glob("*")} if proto_dir.exists() else set()
    for sid in screen_ids:
        if sid not in proto_files:
            errors.append(f"Check 6: SCREEN '{sid}' lacks a UI prototipo in prototype/")

    # Check e: NFR applied
    constraints = arch / "constraints.md"
    nfrs = set()
    if constraints.exists():
        for match in re.finditer(r'\| (NFR-\d+) \|', constraints.read_text(encoding="utf-8")):
            nfrs.add(match.group(1))
            
    adrs = list((arch / "adrs").glob("ADR-*.md")) if (arch / "adrs").exists() else []
    applied_nfrs = set()
    for adr in adrs:
        fm = _parse_frontmatter(adr.read_text(encoding="utf-8"))
        applied_nfrs.update(fm.get("nfr_aplicados", []))
        
    for nfr in nfrs - applied_nfrs:
        errors.append(f"Check e: NFR '{nfr}' is not applied in any ADR")
            
    return errors