import pytest
from factorysoftware.construction.dependencies import compute_dependencies

def test_compute_dependencies_basic():
    epics_data = {
        "epic-1": {},
        "epic-2": {}
    }
    hu_data = {
        "hu-1": {"epic": "epic-1", "depende_de": ["hu-2"]},
        "hu-2": {"epic": "epic-2", "depende_de": []}
    }
    result = compute_dependencies(epics_data, hu_data)
    assert result == {"epic-1": ["epic-2"], "epic-2": []}

def test_compute_dependencies_no_dependencies():
    epics_data = {
        "epic-1": {},
        "epic-2": {}
    }
    hu_data = {
        "hu-1": {"epic": "epic-1"},
        "hu-2": {"epic": "epic-2"}
    }
    result = compute_dependencies(epics_data, hu_data)
    assert result == {"epic-1": [], "epic-2": []}

def test_compute_dependencies_same_epic():
    epics_data = {
        "epic-1": {}
    }
    hu_data = {
        "hu-1": {"epic": "epic-1", "depende_de": ["hu-2"]},
        "hu-2": {"epic": "epic-1"}
    }
    result = compute_dependencies(epics_data, hu_data)
    assert result == {"epic-1": []} # Should not depend on itself

def test_compute_dependencies_multiple():
    epics_data = {
        "epic-1": {},
        "epic-2": {},
        "epic-3": {}
    }
    hu_data = {
        "hu-1": {"epic": "epic-1", "depende_de": ["hu-2", "hu-3"]},
        "hu-2": {"epic": "epic-2"},
        "hu-3": {"epic": "epic-3"}
    }
    result = compute_dependencies(epics_data, hu_data)
    # Return lists should probably be unique and sorted, or we can just check sets for the values
    assert set(result["epic-1"]) == {"epic-2", "epic-3"}
    assert result["epic-2"] == []
    assert result["epic-3"] == []
