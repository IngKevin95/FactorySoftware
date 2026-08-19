import re

def decide_dimensions(diff_text: str, plan_text: str) -> list[str]:
    dims = ["functionality", "practices"]
    
    if "auth/" in diff_text or "rol: seguridad" in plan_text:
        dims.append("security")
        
    if re.search(r'for.*for', diff_text, flags=re.DOTALL) or "SELECT" in diff_text:
        dims.append("efficiency")
        
    return dims
