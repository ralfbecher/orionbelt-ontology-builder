"""Tests for annotation operations, including language-tagged and typed literals."""


def test_add_annotation(populated_om):
    populated_om.add_annotation("Person", "label", "Persona", lang="es")
    anns = populated_om.get_annotations("Person")
    values = [a["value"] for a in anns]
    assert "Persona" in values


def test_delete_plain_annotation(populated_om):
    populated_om.add_annotation("Person", "comment", "A human being")
    populated_om.delete_annotation("Person", "comment", "A human being")
    anns = populated_om.get_annotations("Person")
    comments = [a for a in anns if a["predicate"] == "comment"]
    assert not any(a["value"] == "A human being" for a in comments)


def test_delete_language_tagged_annotation(populated_om):
    """Regression: delete must match language-tagged literals."""
    populated_om.add_annotation("Person", "label", "Persona", lang="es")
    populated_om.delete_annotation("Person", "label", "Persona", lang="es")
    anns = populated_om.get_annotations("Person")
    assert not any(a["value"] == "Persona" and a.get("language") == "es" for a in anns)


def test_delete_annotation_without_lang_removes_all_matching_values(populated_om):
    """When no lang/datatype is provided, remove all literals with that string value."""
    populated_om.add_annotation("Person", "label", "Persona", lang="es")
    populated_om.add_annotation("Person", "label", "Persona", lang="fr")
    populated_om.delete_annotation("Person", "label", "Persona")
    anns = populated_om.get_annotations("Person")
    assert not any(a["value"] == "Persona" for a in anns)


def test_delete_annotation_by_predicate_only(populated_om):
    """Passing value=None removes all annotations for that predicate."""
    populated_om.add_annotation("Person", "comment", "Note 1")
    populated_om.add_annotation("Person", "comment", "Note 2")
    populated_om.delete_annotation("Person", "comment")
    anns = populated_om.get_annotations("Person")
    assert not any(a["predicate"] == "comment" for a in anns)
