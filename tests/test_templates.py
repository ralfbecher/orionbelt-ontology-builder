"""Tests for ontology templates."""

import pytest
from rdflib import Graph
from templates import get_template_names, get_template, render_template
from ontology_manager import OntologyManager


class TestTemplateDefinitions:
    def test_template_names(self):
        names = get_template_names()
        assert len(names) == 5
        assert "Organization" in names
        assert "SKOS Thesaurus" in names

    def test_get_template(self):
        t = get_template("Organization")
        assert t is not None
        assert "description" in t
        assert "turtle" in t

    def test_get_nonexistent_template(self):
        assert get_template("Nonexistent") is None

    def test_render_replaces_base_uri(self):
        t = get_template("Organization")
        rendered = render_template(t, "http://example.org/ont#")
        assert "http://example.org/ont#" in rendered
        assert "{base_uri}" not in rendered


class TestTemplateValidity:
    @pytest.mark.parametrize("name", get_template_names())
    def test_valid_turtle(self, name):
        t = get_template(name)
        rendered = render_template(t, "http://test.org/ont#")
        g = Graph()
        g.parse(data=rendered, format="turtle")
        assert len(g) > 0


class TestTemplateApplication:
    def test_merge_template(self):
        om = OntologyManager(base_uri="http://test.org/ont#")
        om.add_class("ExistingClass")
        t = get_template("Organization")
        rendered = render_template(t, "http://test.org/ont#")
        om.merge_from_string(rendered, "turtle")
        classes = [c["name"] for c in om.get_classes()]
        assert "Organization" in classes
        assert "ExistingClass" in classes  # preserved

    def test_replace_template(self):
        om = OntologyManager(base_uri="http://test.org/ont#")
        om.add_class("ExistingClass")
        t = get_template("Organization")
        rendered = render_template(t, "http://test.org/ont#")
        om.load_from_string(rendered, "turtle")
        classes = [c["name"] for c in om.get_classes()]
        assert "Organization" in classes
        assert "ExistingClass" not in classes  # replaced

    def test_skos_template_creates_concepts(self):
        om = OntologyManager(base_uri="http://test.org/ont#")
        t = get_template("SKOS Thesaurus")
        rendered = render_template(t, "http://test.org/ont#")
        om.load_from_string(rendered, "turtle")
        schemes = om.get_concept_schemes()
        assert len(schemes) >= 1
        concepts = om.get_concepts()
        assert len(concepts) >= 5
