"""Tests for class CRUD operations."""


def test_add_class(om):
    om.add_class("Animal", label="Animal")
    classes = om.get_classes()
    names = [c["name"] for c in classes]
    assert "Animal" in names


def test_add_class_with_parent(om):
    om.add_class("Animal")
    om.add_class("Dog", parent="Animal")
    classes = {c["name"]: c for c in om.get_classes()}
    assert "Animal" in classes["Dog"]["parents"]


def test_rename_class(populated_om):
    result = populated_om.rename_class("Person", "Human")
    assert result is True
    names = [c["name"] for c in populated_om.get_classes()]
    assert "Human" in names
    assert "Person" not in names


def test_delete_class_removes_class(populated_om):
    populated_om.delete_class("Organization")
    names = [c["name"] for c in populated_om.get_classes()]
    assert "Organization" not in names


def test_delete_class_removes_individual_typing(populated_om):
    """Regression: deleting a class strips rdf:type from its instances."""
    populated_om.delete_class("Employee")
    # alice should still exist as NamedIndividual but lose Employee type
    individuals = populated_om.get_individuals()
    alice = next((i for i in individuals if i["name"] == "alice"), None)
    assert alice is not None
    # The Employee type is gone; alice may have no class type left
    assert "Employee" not in alice.get("types", [])


def test_get_class_hierarchy(populated_om):
    hierarchy = populated_om.get_class_hierarchy()
    assert "Person" in hierarchy
    assert "Employee" in hierarchy["Person"]
