import pytest
from factorysoftware.construction.triage import decide_dimensions

def test_decide_dimensions_defaults():
    diff_text = "some standard code"
    plan_text = "a simple plan"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices"}

def test_decide_dimensions_security_diff():
    diff_text = "a/b/auth/login.py"
    plan_text = "plan"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices", "security"}

def test_decide_dimensions_security_plan():
    diff_text = "some standard code"
    plan_text = "rol: seguridad required"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices", "security"}

def test_decide_dimensions_efficiency_for_for():
    diff_text = "for i in items:\n  for j in subitems:"
    plan_text = "plan"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices", "efficiency"}

def test_decide_dimensions_efficiency_select():
    diff_text = "SELECT * FROM users"
    plan_text = "plan"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices", "efficiency"}

def test_decide_dimensions_all():
    diff_text = "auth/login.py SELECT"
    plan_text = "plan"
    result = decide_dimensions(diff_text, plan_text)
    assert set(result) == {"functionality", "practices", "security", "efficiency"}
