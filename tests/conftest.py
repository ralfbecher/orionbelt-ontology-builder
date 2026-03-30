import pytest
from ontology_manager import OntologyManager


@pytest.fixture
def om():
    """Fresh OntologyManager with default namespace."""
    return OntologyManager()


@pytest.fixture
def populated_om():
    """OntologyManager with a small class/property/individual graph."""
    m = OntologyManager(base_uri="http://test.org/ont#")
    m.add_class("Person", label="Person")
    m.add_class("Organization", label="Organization")
    m.add_class("Employee", parent="Person", label="Employee")
    m.add_object_property("worksFor", domain="Person", range_="Organization")
    m.add_data_property("hasName", domain="Person", range_="string")
    m.add_individual("alice", "Employee", label="Alice")
    m.add_individual("acme", "Organization", label="ACME Corp")
    return m
