import re

_UI_PATH_RE = re.compile(r'\.(tsx|jsx|vue|svelte)$|/components/|/screens/|/views/', re.MULTILINE)

def decide_dimensions(diff_text: str, plan_text: str) -> list[str]:
    dims = ["functionality", "practices"]

    if "auth/" in diff_text or "rol: seguridad" in plan_text:
        dims.append("security")

    if re.search(r'for.*for', diff_text, flags=re.DOTALL) or "SELECT" in diff_text:
        dims.append("efficiency")

    if "rol: frontend" in plan_text or "rol: mobile" in plan_text or _UI_PATH_RE.search(diff_text):
        dims.append("fidelity")
        dims.append("usability")

    return dims
