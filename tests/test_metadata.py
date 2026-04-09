"""Tests for ontology metadata operations."""

from rdflib import RDFS
from rdflib.namespace import DCTERMS, OWL


def test_set_metadata(om):
    om.set_ontology_metadata(label="My Ontology", comment="A test", creator="Tester")
    label = om.graph.value(om.ontology_uri, RDFS.label)
    assert str(label) == "My Ontology"
    comment = om.graph.value(om.ontology_uri, RDFS.comment)
    assert str(comment) == "A test"
    creator = om.graph.value(om.ontology_uri, DCTERMS.creator)
    assert str(creator) == "Tester"


def test_clear_metadata(om):
    """Regression: empty string should clear metadata, not leave it unchanged."""
    om.set_ontology_metadata(label="My Ontology", comment="A test", creator="Tester")
    om.set_ontology_metadata(label="", comment="", creator="")
    assert om.graph.value(om.ontology_uri, RDFS.label) is None
    assert om.graph.value(om.ontology_uri, RDFS.comment) is None
    assert om.graph.value(om.ontology_uri, DCTERMS.creator) is None


def test_clear_version_iri(om):
    om.set_ontology_metadata(version_iri="http://example.org/v1")
    assert om.graph.value(om.ontology_uri, OWL.versionIRI) is not None
    om.set_ontology_metadata(version_iri="")
    assert om.graph.value(om.ontology_uri, OWL.versionIRI) is None


def test_omitted_params_leave_unchanged(om):
    om.set_ontology_metadata(label="Keep")
    om.set_ontology_metadata(comment="New comment")
    assert str(om.graph.value(om.ontology_uri, RDFS.label)) == "Keep"
    assert str(om.graph.value(om.ontology_uri, RDFS.comment)) == "New comment"
