"""Tests for individual CRUD operations."""


def test_add_individual(populated_om):
    populated_om.add_individual("bob", "Person", label="Bob")
    individuals = populated_om.get_individuals()
    names = [i["name"] for i in individuals]
    assert "bob" in names


def test_delete_individual(populated_om):
    populated_om.delete_individual("alice")
    individuals = populated_om.get_individuals()
    names = [i["name"] for i in individuals]
    assert "alice" not in names


def test_rename_individual(populated_om):
    result = populated_om.rename_individual("alice", "alice_smith")
    assert result is True
    names = [i["name"] for i in populated_om.get_individuals()]
    assert "alice_smith" in names
    assert "alice" not in names
