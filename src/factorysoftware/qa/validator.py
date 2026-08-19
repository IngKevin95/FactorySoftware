from pathlib import Path

def validate_qa(project_root: Path) -> list[str]:
    """
    Validaciones estructurales de la fase de QA.
    Actualmente devuelve lista vacía.
    
    Futuras validaciones a implementar aquí:
    - Que todos los archivos de test mencionados en traceability tengan su archivo real.
    - Consistencia entre NFRs requeridos y NFRs cubiertos.
    - Cruces de completitud con Requerimientos y Construcción.
    """
    return []
