def compute_dependencies(epics_data: dict, hu_data: dict) -> dict[str, list[str]]:
    dependencies = {epic_id: set() for epic_id in epics_data}
    
    for hu_id, hu_info in hu_data.items():
        epic_id = hu_info.get("epic")
        if not epic_id or epic_id not in epics_data:
            continue
            
        depends_on = hu_info.get("depende_de", [])
        for dep_hu_id in depends_on:
            dep_hu_info = hu_data.get(dep_hu_id)
            if not dep_hu_info:
                continue
                
            dep_epic_id = dep_hu_info.get("epic")
            if dep_epic_id and dep_epic_id in epics_data and dep_epic_id != epic_id:
                dependencies[epic_id].add(dep_epic_id)
                
    return {epic_id: sorted(list(deps)) for epic_id, deps in dependencies.items()}
