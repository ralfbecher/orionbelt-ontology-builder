"""Tests for global ontology search."""


def test_search_by_name(populated_om):
    results = populated_om.search("Person")
    assert any(r["name"] == "Person" for r in results)


def test_search_by_label(populated_om):
    results = populated_om.search("Alice")
    assert any(r["name"] == "alice" for r in results)


def test_search_case_insensitive(populated_om):
    results = populated_om.search("person")
    assert any(r["name"] == "Person" for r in results)


def test_search_partial_match(populated_om):
    results = populated_om.search("Emp")
    assert any(r["name"] == "Employee" for r in results)


def test_search_returns_type(populated_om):
    results = populated_om.search("worksFor")
    match = next((r for r in results if r["name"] == "worksFor"), None)
    assert match is not None
    assert match["type"] == "Object Property"


def test_search_empty_query(populated_om):
    assert populated_om.search("") == []
    assert populated_om.search("   ") == []


def test_search_no_results(populated_om):
    assert populated_om.search("zzzznotfound") == []


def test_search_finds_individuals(populated_om):
    results = populated_om.search("acme")
    assert any(r["name"] == "acme" and r["type"] == "Individual" for r in results)


def test_search_name_matches_rank_first(populated_om):
    """Name matches should appear before label/comment matches."""
    populated_om.add_class("Alpha", label="Zeta")
    populated_om.add_class("Zeta", label="Alpha")
    results = populated_om.search("Alpha")
    names = [r["name"] for r in results]
    assert names.index("Alpha") < names.index("Zeta")
