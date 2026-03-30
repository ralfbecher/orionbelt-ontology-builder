"""Tests for export and serialization."""

from ontology_manager import OntologyManager


def test_roundtrip_turtle(populated_om):
    """Export to Turtle and re-import preserves classes."""
    ttl = populated_om.export_to_string(format="turtle")
    m2 = OntologyManager()
    m2.load_from_string(ttl, format="turtle")
    original_names = sorted(c["name"] for c in populated_om.get_classes())
    reimported_names = sorted(c["name"] for c in m2.get_classes())
    assert original_names == reimported_names


def test_roundtrip_xml(populated_om):
    """Export to RDF/XML and re-import preserves classes."""
    xml = populated_om.export_to_string(format="xml")
    m2 = OntologyManager()
    m2.load_from_string(xml, format="xml")
    original_names = sorted(c["name"] for c in populated_om.get_classes())
    reimported_names = sorted(c["name"] for c in m2.get_classes())
    assert original_names == reimported_names


def test_export_contains_individuals(populated_om):
    ttl = populated_om.export_to_string(format="turtle")
    assert "alice" in ttl
    assert "acme" in ttl
