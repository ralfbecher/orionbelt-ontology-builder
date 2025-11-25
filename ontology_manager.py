"""
OntologyManager - Core class for managing OWL ontologies using rdflib.
"""

from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DC, DCTERMS
from rdflib.collection import Collection
from typing import Optional, List, Dict, Tuple, Any, Set
import owlrl


class OntologyManager:
    """Manages OWL ontology operations including CRUD for classes, properties, individuals, and restrictions."""

    # Common XSD datatypes for data properties
    XSD_DATATYPES = {
        "string": XSD.string,
        "integer": XSD.integer,
        "float": XSD.float,
        "double": XSD.double,
        "boolean": XSD.boolean,
        "date": XSD.date,
        "dateTime": XSD.dateTime,
        "time": XSD.time,
        "decimal": XSD.decimal,
        "anyURI": XSD.anyURI,
        "nonNegativeInteger": XSD.nonNegativeInteger,
        "positiveInteger": XSD.positiveInteger,
    }

    # Restriction types
    RESTRICTION_TYPES = {
        "someValuesFrom": OWL.someValuesFrom,
        "allValuesFrom": OWL.allValuesFrom,
        "hasValue": OWL.hasValue,
        "minCardinality": OWL.minCardinality,
        "maxCardinality": OWL.maxCardinality,
        "exactCardinality": OWL.cardinality,
        "minQualifiedCardinality": OWL.minQualifiedCardinality,
        "maxQualifiedCardinality": OWL.maxQualifiedCardinality,
        "qualifiedCardinality": OWL.qualifiedCardinality,
    }

    def __init__(self, base_uri: str = "http://example.org/ontology#"):
        """Initialize the ontology manager with a base URI."""
        self.graph = Graph()
        self.base_uri = base_uri
        self.namespace = Namespace(base_uri)

        # Bind common prefixes
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.graph.bind("skos", SKOS)
        self.graph.bind("dc", DC)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("", self.namespace)

        # Create ontology declaration
        self.ontology_uri = URIRef(base_uri.rstrip("#").rstrip("/"))
        self.graph.add((self.ontology_uri, RDF.type, OWL.Ontology))

    def set_ontology_metadata(self, title: str = None, description: str = None,
                              version: str = None, creator: str = None):
        """Set ontology-level metadata."""
        if title:
            self.graph.set((self.ontology_uri, DCTERMS.title, Literal(title)))
        if description:
            self.graph.set((self.ontology_uri, DCTERMS.description, Literal(description)))
        if version:
            self.graph.set((self.ontology_uri, OWL.versionInfo, Literal(version)))
        if creator:
            self.graph.set((self.ontology_uri, DCTERMS.creator, Literal(creator)))

    def get_ontology_metadata(self) -> Dict[str, str]:
        """Get ontology-level metadata."""
        metadata = {}
        for pred, key in [(DCTERMS.title, "title"), (DCTERMS.description, "description"),
                          (OWL.versionInfo, "version"), (DCTERMS.creator, "creator")]:
            value = self.graph.value(self.ontology_uri, pred)
            if value:
                metadata[key] = str(value)
        return metadata

    def set_base_uri(self, new_base_uri: str):
        """Update the base URI of the ontology. This will update all local resources."""
        if not new_base_uri:
            return

        # Ensure proper format
        if not new_base_uri.endswith("#") and not new_base_uri.endswith("/"):
            new_base_uri = new_base_uri + "#"

        old_base_uri = self.base_uri
        old_ontology_uri = self.ontology_uri

        # Update internal state
        self.base_uri = new_base_uri
        self.namespace = Namespace(new_base_uri)
        self.ontology_uri = URIRef(new_base_uri.rstrip("#").rstrip("/"))

        # Update the ontology declaration
        # First, collect all triples about the old ontology URI
        old_triples = list(self.graph.triples((old_ontology_uri, None, None)))
        for s, p, o in old_triples:
            self.graph.remove((s, p, o))
            self.graph.add((self.ontology_uri, p, o))

        # Update triples where old ontology URI is object
        old_triples = list(self.graph.triples((None, None, old_ontology_uri)))
        for s, p, o in old_triples:
            self.graph.remove((s, p, o))
            self.graph.add((s, p, self.ontology_uri))

        # Update all resources that used the old namespace
        if old_base_uri != new_base_uri:
            updates = []
            for s, p, o in self.graph:
                new_s, new_o = s, o
                if isinstance(s, URIRef) and str(s).startswith(old_base_uri):
                    local_name = str(s)[len(old_base_uri):]
                    new_s = URIRef(new_base_uri + local_name)
                if isinstance(o, URIRef) and str(o).startswith(old_base_uri):
                    local_name = str(o)[len(old_base_uri):]
                    new_o = URIRef(new_base_uri + local_name)
                if new_s != s or new_o != o:
                    updates.append(((s, p, o), (new_s, p, new_o)))

            for old_triple, new_triple in updates:
                self.graph.remove(old_triple)
                self.graph.add(new_triple)

        # Re-bind the default namespace
        self.graph.bind("", self.namespace)

    def _uri(self, local_name: str) -> URIRef:
        """Create a URI from a local name."""
        if local_name.startswith("http://") or local_name.startswith("https://"):
            return URIRef(local_name)
        return self.namespace[local_name]

    def _local_name(self, uri: URIRef) -> str:
        """Extract local name from a URI."""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        return uri_str.split("/")[-1]

    # ==================== CLASS OPERATIONS ====================

    def add_class(self, name: str, parent: str = None, label: str = None,
                  comment: str = None) -> URIRef:
        """Add a new OWL class."""
        class_uri = self._uri(name)
        self.graph.add((class_uri, RDF.type, OWL.Class))

        if parent:
            parent_uri = self._uri(parent)
            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))

        if label:
            self.graph.add((class_uri, RDFS.label, Literal(label)))
        if comment:
            self.graph.add((class_uri, RDFS.comment, Literal(comment)))

        return class_uri

    def update_class(self, name: str, new_label: str = None, new_comment: str = None,
                     new_parent: str = None, remove_parent: str = None):
        """Update an existing class."""
        class_uri = self._uri(name)

        if new_label is not None:
            self.graph.remove((class_uri, RDFS.label, None))
            if new_label:
                self.graph.add((class_uri, RDFS.label, Literal(new_label)))

        if new_comment is not None:
            self.graph.remove((class_uri, RDFS.comment, None))
            if new_comment:
                self.graph.add((class_uri, RDFS.comment, Literal(new_comment)))

        if remove_parent:
            self.graph.remove((class_uri, RDFS.subClassOf, self._uri(remove_parent)))

        if new_parent:
            self.graph.add((class_uri, RDFS.subClassOf, self._uri(new_parent)))

    def delete_class(self, name: str):
        """Delete a class and all its references."""
        class_uri = self._uri(name)
        # Remove all triples where this class is subject or object
        self.graph.remove((class_uri, None, None))
        self.graph.remove((None, None, class_uri))

    def get_classes(self) -> List[Dict[str, Any]]:
        """Get all classes with their details."""
        classes = []
        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(class_uri, BNode):
                continue  # Skip anonymous classes (restrictions)

            class_info = {
                "uri": str(class_uri),
                "name": self._local_name(class_uri),
                "label": str(self.graph.value(class_uri, RDFS.label) or ""),
                "comment": str(self.graph.value(class_uri, RDFS.comment) or ""),
                "parents": [],
                "children": []
            }

            # Get parent classes
            for parent in self.graph.objects(class_uri, RDFS.subClassOf):
                if isinstance(parent, URIRef):
                    class_info["parents"].append(self._local_name(parent))

            # Get child classes
            for child in self.graph.subjects(RDFS.subClassOf, class_uri):
                if isinstance(child, URIRef):
                    class_info["children"].append(self._local_name(child))

            classes.append(class_info)

        return sorted(classes, key=lambda x: x["name"])

    def get_class_hierarchy(self) -> Dict[str, List[str]]:
        """Get class hierarchy as adjacency list."""
        hierarchy = {}
        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(class_uri, BNode):
                continue
            name = self._local_name(class_uri)
            hierarchy[name] = []
            for child in self.graph.subjects(RDFS.subClassOf, class_uri):
                if isinstance(child, URIRef):
                    hierarchy[name].append(self._local_name(child))
        return hierarchy

    # ==================== PROPERTY OPERATIONS ====================

    def add_object_property(self, name: str, domain: str = None, range_: str = None,
                            label: str = None, comment: str = None,
                            functional: bool = False, inverse_functional: bool = False,
                            transitive: bool = False, symmetric: bool = False,
                            inverse_of: str = None) -> URIRef:
        """Add a new object property."""
        prop_uri = self._uri(name)
        self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))

        if domain:
            self.graph.add((prop_uri, RDFS.domain, self._uri(domain)))
        if range_:
            self.graph.add((prop_uri, RDFS.range, self._uri(range_)))
        if label:
            self.graph.add((prop_uri, RDFS.label, Literal(label)))
        if comment:
            self.graph.add((prop_uri, RDFS.comment, Literal(comment)))

        # Property characteristics
        if functional:
            self.graph.add((prop_uri, RDF.type, OWL.FunctionalProperty))
        if inverse_functional:
            self.graph.add((prop_uri, RDF.type, OWL.InverseFunctionalProperty))
        if transitive:
            self.graph.add((prop_uri, RDF.type, OWL.TransitiveProperty))
        if symmetric:
            self.graph.add((prop_uri, RDF.type, OWL.SymmetricProperty))
        if inverse_of:
            self.graph.add((prop_uri, OWL.inverseOf, self._uri(inverse_of)))

        return prop_uri

    def add_data_property(self, name: str, domain: str = None, range_: str = "string",
                          label: str = None, comment: str = None,
                          functional: bool = False) -> URIRef:
        """Add a new data property."""
        prop_uri = self._uri(name)
        self.graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))

        if domain:
            self.graph.add((prop_uri, RDFS.domain, self._uri(domain)))
        if range_:
            datatype = self.XSD_DATATYPES.get(range_, XSD.string)
            self.graph.add((prop_uri, RDFS.range, datatype))
        if label:
            self.graph.add((prop_uri, RDFS.label, Literal(label)))
        if comment:
            self.graph.add((prop_uri, RDFS.comment, Literal(comment)))
        if functional:
            self.graph.add((prop_uri, RDF.type, OWL.FunctionalProperty))

        return prop_uri

    def update_property(self, name: str, new_label: str = None, new_comment: str = None,
                        new_domain: str = None, new_range: str = None):
        """Update an existing property."""
        prop_uri = self._uri(name)

        if new_label is not None:
            self.graph.remove((prop_uri, RDFS.label, None))
            if new_label:
                self.graph.add((prop_uri, RDFS.label, Literal(new_label)))

        if new_comment is not None:
            self.graph.remove((prop_uri, RDFS.comment, None))
            if new_comment:
                self.graph.add((prop_uri, RDFS.comment, Literal(new_comment)))

        if new_domain is not None:
            self.graph.remove((prop_uri, RDFS.domain, None))
            if new_domain:
                self.graph.add((prop_uri, RDFS.domain, self._uri(new_domain)))

        if new_range is not None:
            self.graph.remove((prop_uri, RDFS.range, None))
            if new_range:
                # Check if it's a datatype or class
                if new_range in self.XSD_DATATYPES:
                    self.graph.add((prop_uri, RDFS.range, self.XSD_DATATYPES[new_range]))
                else:
                    self.graph.add((prop_uri, RDFS.range, self._uri(new_range)))

    def delete_property(self, name: str):
        """Delete a property and all its references."""
        prop_uri = self._uri(name)
        self.graph.remove((prop_uri, None, None))
        self.graph.remove((None, None, prop_uri))
        self.graph.remove((None, prop_uri, None))

    def get_object_properties(self) -> List[Dict[str, Any]]:
        """Get all object properties with their details."""
        properties = []
        for prop_uri in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(prop_uri, BNode):
                continue

            prop_info = {
                "uri": str(prop_uri),
                "name": self._local_name(prop_uri),
                "label": str(self.graph.value(prop_uri, RDFS.label) or ""),
                "comment": str(self.graph.value(prop_uri, RDFS.comment) or ""),
                "domain": "",
                "range": "",
                "characteristics": []
            }

            domain = self.graph.value(prop_uri, RDFS.domain)
            if domain and isinstance(domain, URIRef):
                prop_info["domain"] = self._local_name(domain)

            range_ = self.graph.value(prop_uri, RDFS.range)
            if range_ and isinstance(range_, URIRef):
                prop_info["range"] = self._local_name(range_)

            # Check characteristics
            if (prop_uri, RDF.type, OWL.FunctionalProperty) in self.graph:
                prop_info["characteristics"].append("Functional")
            if (prop_uri, RDF.type, OWL.InverseFunctionalProperty) in self.graph:
                prop_info["characteristics"].append("InverseFunctional")
            if (prop_uri, RDF.type, OWL.TransitiveProperty) in self.graph:
                prop_info["characteristics"].append("Transitive")
            if (prop_uri, RDF.type, OWL.SymmetricProperty) in self.graph:
                prop_info["characteristics"].append("Symmetric")

            inverse = self.graph.value(prop_uri, OWL.inverseOf)
            if inverse:
                prop_info["inverse_of"] = self._local_name(inverse)

            properties.append(prop_info)

        return sorted(properties, key=lambda x: x["name"])

    def get_data_properties(self) -> List[Dict[str, Any]]:
        """Get all data properties with their details."""
        properties = []
        for prop_uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(prop_uri, BNode):
                continue

            prop_info = {
                "uri": str(prop_uri),
                "name": self._local_name(prop_uri),
                "label": str(self.graph.value(prop_uri, RDFS.label) or ""),
                "comment": str(self.graph.value(prop_uri, RDFS.comment) or ""),
                "domain": "",
                "range": "",
                "functional": False
            }

            domain = self.graph.value(prop_uri, RDFS.domain)
            if domain and isinstance(domain, URIRef):
                prop_info["domain"] = self._local_name(domain)

            range_ = self.graph.value(prop_uri, RDFS.range)
            if range_:
                prop_info["range"] = self._local_name(range_)

            prop_info["functional"] = (prop_uri, RDF.type, OWL.FunctionalProperty) in self.graph

            properties.append(prop_info)

        return sorted(properties, key=lambda x: x["name"])

    # ==================== INDIVIDUAL OPERATIONS ====================

    def add_individual(self, name: str, class_name: str, label: str = None,
                       comment: str = None) -> URIRef:
        """Add a new individual (instance)."""
        ind_uri = self._uri(name)
        class_uri = self._uri(class_name)

        self.graph.add((ind_uri, RDF.type, OWL.NamedIndividual))
        self.graph.add((ind_uri, RDF.type, class_uri))

        if label:
            self.graph.add((ind_uri, RDFS.label, Literal(label)))
        if comment:
            self.graph.add((ind_uri, RDFS.comment, Literal(comment)))

        return ind_uri

    def add_individual_property(self, individual: str, property_name: str, value: Any,
                                is_object_property: bool = True):
        """Add a property assertion to an individual."""
        ind_uri = self._uri(individual)
        prop_uri = self._uri(property_name)

        if is_object_property:
            value_uri = self._uri(value)
            self.graph.add((ind_uri, prop_uri, value_uri))
        else:
            self.graph.add((ind_uri, prop_uri, Literal(value)))

    def update_individual(self, name: str, new_label: str = None, new_comment: str = None,
                          add_class: str = None, remove_class: str = None):
        """Update an existing individual."""
        ind_uri = self._uri(name)

        if new_label is not None:
            self.graph.remove((ind_uri, RDFS.label, None))
            if new_label:
                self.graph.add((ind_uri, RDFS.label, Literal(new_label)))

        if new_comment is not None:
            self.graph.remove((ind_uri, RDFS.comment, None))
            if new_comment:
                self.graph.add((ind_uri, RDFS.comment, Literal(new_comment)))

        if add_class:
            self.graph.add((ind_uri, RDF.type, self._uri(add_class)))

        if remove_class:
            self.graph.remove((ind_uri, RDF.type, self._uri(remove_class)))

    def delete_individual(self, name: str):
        """Delete an individual and all its references."""
        ind_uri = self._uri(name)
        self.graph.remove((ind_uri, None, None))
        self.graph.remove((None, None, ind_uri))

    def get_individuals(self) -> List[Dict[str, Any]]:
        """Get all individuals with their details."""
        individuals = []
        seen = set()

        for ind_uri in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            if isinstance(ind_uri, BNode) or str(ind_uri) in seen:
                continue
            seen.add(str(ind_uri))

            ind_info = {
                "uri": str(ind_uri),
                "name": self._local_name(ind_uri),
                "label": str(self.graph.value(ind_uri, RDFS.label) or ""),
                "comment": str(self.graph.value(ind_uri, RDFS.comment) or ""),
                "classes": [],
                "properties": []
            }

            # Get classes
            for class_uri in self.graph.objects(ind_uri, RDF.type):
                if isinstance(class_uri, URIRef) and class_uri != OWL.NamedIndividual:
                    ind_info["classes"].append(self._local_name(class_uri))

            # Get property assertions
            for pred, obj in self.graph.predicate_objects(ind_uri):
                if pred not in [RDF.type, RDFS.label, RDFS.comment]:
                    prop_name = self._local_name(pred)
                    if isinstance(obj, URIRef):
                        value = self._local_name(obj)
                    else:
                        value = str(obj)
                    ind_info["properties"].append({"property": prop_name, "value": value})

            individuals.append(ind_info)

        return sorted(individuals, key=lambda x: x["name"])

    # ==================== RESTRICTION OPERATIONS ====================

    def add_restriction(self, class_name: str, property_name: str, restriction_type: str,
                        value: Any, on_class: str = None) -> BNode:
        """Add a restriction to a class."""
        class_uri = self._uri(class_name)
        prop_uri = self._uri(property_name)

        restriction = BNode()
        self.graph.add((restriction, RDF.type, OWL.Restriction))
        self.graph.add((restriction, OWL.onProperty, prop_uri))

        restriction_pred = self.RESTRICTION_TYPES.get(restriction_type)
        if not restriction_pred:
            raise ValueError(f"Unknown restriction type: {restriction_type}")

        # Handle different value types
        if restriction_type in ["someValuesFrom", "allValuesFrom"]:
            self.graph.add((restriction, restriction_pred, self._uri(value)))
        elif restriction_type == "hasValue":
            if isinstance(value, str) and not value.startswith("http"):
                self.graph.add((restriction, restriction_pred, Literal(value)))
            else:
                self.graph.add((restriction, restriction_pred, self._uri(value)))
        elif restriction_type in ["minCardinality", "maxCardinality", "exactCardinality"]:
            self.graph.add((restriction, restriction_pred,
                          Literal(int(value), datatype=XSD.nonNegativeInteger)))
        elif restriction_type in ["minQualifiedCardinality", "maxQualifiedCardinality",
                                  "qualifiedCardinality"]:
            self.graph.add((restriction, restriction_pred,
                          Literal(int(value), datatype=XSD.nonNegativeInteger)))
            if on_class:
                self.graph.add((restriction, OWL.onClass, self._uri(on_class)))

        # Add as subclass of the target class
        self.graph.add((class_uri, RDFS.subClassOf, restriction))

        return restriction

    def get_restrictions(self, class_name: str = None) -> List[Dict[str, Any]]:
        """Get restrictions, optionally filtered by class."""
        restrictions = []

        for restriction in self.graph.subjects(RDF.type, OWL.Restriction):
            prop = self.graph.value(restriction, OWL.onProperty)
            if not prop:
                continue

            rest_info = {
                "property": self._local_name(prop),
                "type": None,
                "value": None,
                "on_class": None,
                "applied_to": []
            }

            # Determine restriction type
            for rtype, pred in self.RESTRICTION_TYPES.items():
                val = self.graph.value(restriction, pred)
                if val is not None:
                    rest_info["type"] = rtype
                    if isinstance(val, URIRef):
                        rest_info["value"] = self._local_name(val)
                    else:
                        rest_info["value"] = str(val)
                    break

            on_class = self.graph.value(restriction, OWL.onClass)
            if on_class:
                rest_info["on_class"] = self._local_name(on_class)

            # Find classes this restriction applies to
            for cls in self.graph.subjects(RDFS.subClassOf, restriction):
                if isinstance(cls, URIRef):
                    rest_info["applied_to"].append(self._local_name(cls))

            if class_name is None or class_name in rest_info["applied_to"]:
                restrictions.append(rest_info)

        return restrictions

    def delete_restriction(self, class_name: str, property_name: str, restriction_type: str):
        """Delete a restriction from a class."""
        class_uri = self._uri(class_name)
        prop_uri = self._uri(property_name)

        for restriction in self.graph.subjects(RDF.type, OWL.Restriction):
            if self.graph.value(restriction, OWL.onProperty) == prop_uri:
                # Check if this restriction is on the target class
                if (class_uri, RDFS.subClassOf, restriction) in self.graph:
                    # Check restriction type
                    pred = self.RESTRICTION_TYPES.get(restriction_type)
                    if pred and self.graph.value(restriction, pred) is not None:
                        self.graph.remove((class_uri, RDFS.subClassOf, restriction))
                        self.graph.remove((restriction, None, None))
                        return True
        return False

    # ==================== ANNOTATION OPERATIONS ====================

    def add_annotation(self, subject: str, predicate: str, value: str, lang: str = None):
        """Add an annotation to any resource."""
        subj_uri = self._uri(subject)

        # Map common annotation names to URIs
        annotation_predicates = {
            "label": RDFS.label,
            "comment": RDFS.comment,
            "seeAlso": RDFS.seeAlso,
            "isDefinedBy": RDFS.isDefinedBy,
            "prefLabel": SKOS.prefLabel,
            "altLabel": SKOS.altLabel,
            "definition": SKOS.definition,
            "example": SKOS.example,
            "note": SKOS.note,
            "title": DCTERMS.title,
            "description": DCTERMS.description,
            "creator": DCTERMS.creator,
            "contributor": DCTERMS.contributor,
            "date": DCTERMS.date,
            "deprecated": OWL.deprecated,
        }

        pred_uri = annotation_predicates.get(predicate, self._uri(predicate))

        if lang:
            literal = Literal(value, lang=lang)
        else:
            literal = Literal(value)

        self.graph.add((subj_uri, pred_uri, literal))

    def get_annotations(self, subject: str) -> List[Dict[str, str]]:
        """Get all annotations for a resource."""
        subj_uri = self._uri(subject)
        annotations = []

        annotation_properties = [
            RDFS.label, RDFS.comment, RDFS.seeAlso, RDFS.isDefinedBy,
            SKOS.prefLabel, SKOS.altLabel, SKOS.definition, SKOS.example, SKOS.note,
            DCTERMS.title, DCTERMS.description, DCTERMS.creator,
            DCTERMS.contributor, DCTERMS.date,
            OWL.deprecated
        ]

        for pred in annotation_properties:
            for obj in self.graph.objects(subj_uri, pred):
                ann = {
                    "predicate": self._local_name(pred),
                    "value": str(obj)
                }
                if hasattr(obj, 'language') and obj.language:
                    ann["language"] = obj.language
                annotations.append(ann)

        return annotations

    def delete_annotation(self, subject: str, predicate: str, value: str = None):
        """Delete an annotation from a resource."""
        subj_uri = self._uri(subject)

        annotation_predicates = {
            "label": RDFS.label, "comment": RDFS.comment,
            "prefLabel": SKOS.prefLabel, "altLabel": SKOS.altLabel,
            "definition": SKOS.definition, "note": SKOS.note,
        }

        pred_uri = annotation_predicates.get(predicate, self._uri(predicate))

        if value:
            self.graph.remove((subj_uri, pred_uri, Literal(value)))
        else:
            self.graph.remove((subj_uri, pred_uri, None))

    # ==================== RELATIONS OPERATIONS ====================

    # Class relation types
    CLASS_RELATIONS = {
        "subClassOf": RDFS.subClassOf,
        "equivalentClass": OWL.equivalentClass,
        "disjointWith": OWL.disjointWith,
    }

    # Property relation types
    PROPERTY_RELATIONS = {
        "subPropertyOf": RDFS.subPropertyOf,
        "equivalentProperty": OWL.equivalentProperty,
        "inverseOf": OWL.inverseOf,
    }

    # Individual relation types
    INDIVIDUAL_RELATIONS = {
        "sameAs": OWL.sameAs,
        "differentFrom": OWL.differentFrom,
    }

    def add_class_relation(self, class1: str, relation_type: str, class2: str):
        """Add a relation between two classes."""
        class1_uri = self._uri(class1)
        class2_uri = self._uri(class2)
        relation = self.CLASS_RELATIONS.get(relation_type)
        if relation:
            self.graph.add((class1_uri, relation, class2_uri))

    def remove_class_relation(self, class1: str, relation_type: str, class2: str):
        """Remove a relation between two classes."""
        class1_uri = self._uri(class1)
        class2_uri = self._uri(class2)
        relation = self.CLASS_RELATIONS.get(relation_type)
        if relation:
            self.graph.remove((class1_uri, relation, class2_uri))

    def get_class_relations(self, class_name: str = None) -> List[Dict[str, str]]:
        """Get all class relations, optionally filtered by class."""
        relations = []
        for rel_name, rel_pred in self.CLASS_RELATIONS.items():
            for subj, obj in self.graph.subject_objects(rel_pred):
                if isinstance(subj, URIRef) and isinstance(obj, URIRef):
                    subj_name = self._local_name(subj)
                    obj_name = self._local_name(obj)
                    if class_name is None or class_name in [subj_name, obj_name]:
                        relations.append({
                            "subject": subj_name,
                            "relation": rel_name,
                            "object": obj_name
                        })
        return relations

    def add_property_relation(self, prop1: str, relation_type: str, prop2: str):
        """Add a relation between two properties."""
        prop1_uri = self._uri(prop1)
        prop2_uri = self._uri(prop2)
        relation = self.PROPERTY_RELATIONS.get(relation_type)
        if relation:
            self.graph.add((prop1_uri, relation, prop2_uri))

    def remove_property_relation(self, prop1: str, relation_type: str, prop2: str):
        """Remove a relation between two properties."""
        prop1_uri = self._uri(prop1)
        prop2_uri = self._uri(prop2)
        relation = self.PROPERTY_RELATIONS.get(relation_type)
        if relation:
            self.graph.remove((prop1_uri, relation, prop2_uri))

    def get_property_relations(self, prop_name: str = None) -> List[Dict[str, str]]:
        """Get all property relations, optionally filtered by property."""
        relations = []
        for rel_name, rel_pred in self.PROPERTY_RELATIONS.items():
            for subj, obj in self.graph.subject_objects(rel_pred):
                if isinstance(subj, URIRef) and isinstance(obj, URIRef):
                    subj_name = self._local_name(subj)
                    obj_name = self._local_name(obj)
                    if prop_name is None or prop_name in [subj_name, obj_name]:
                        relations.append({
                            "subject": subj_name,
                            "relation": rel_name,
                            "object": obj_name
                        })
        return relations

    def add_individual_relation(self, ind1: str, relation_type: str, ind2: str):
        """Add a relation between two individuals (sameAs, differentFrom)."""
        ind1_uri = self._uri(ind1)
        ind2_uri = self._uri(ind2)
        relation = self.INDIVIDUAL_RELATIONS.get(relation_type)
        if relation:
            self.graph.add((ind1_uri, relation, ind2_uri))

    def remove_individual_relation(self, ind1: str, relation_type: str, ind2: str):
        """Remove a relation between two individuals."""
        ind1_uri = self._uri(ind1)
        ind2_uri = self._uri(ind2)
        relation = self.INDIVIDUAL_RELATIONS.get(relation_type)
        if relation:
            self.graph.remove((ind1_uri, relation, ind2_uri))

    def get_individual_relations(self, ind_name: str = None) -> List[Dict[str, str]]:
        """Get all individual relations (sameAs, differentFrom)."""
        relations = []
        for rel_name, rel_pred in self.INDIVIDUAL_RELATIONS.items():
            for subj, obj in self.graph.subject_objects(rel_pred):
                if isinstance(subj, URIRef) and isinstance(obj, URIRef):
                    subj_name = self._local_name(subj)
                    obj_name = self._local_name(obj)
                    if ind_name is None or ind_name in [subj_name, obj_name]:
                        relations.append({
                            "subject": subj_name,
                            "relation": rel_name,
                            "object": obj_name
                        })
        return relations

    def get_all_relations(self) -> Dict[str, List[Dict[str, str]]]:
        """Get all relations organized by type."""
        return {
            "class_relations": self.get_class_relations(),
            "property_relations": self.get_property_relations(),
            "individual_relations": self.get_individual_relations()
        }

    # ==================== IMPORT/EXPORT OPERATIONS ====================

    def load_from_file(self, file_path: str, format: str = "turtle"):
        """Load ontology from a file."""
        self.graph = Graph()
        self.graph.parse(file_path, format=format)
        self._update_namespace_from_graph()

    def load_from_string(self, data: str, format: str = "turtle"):
        """Load ontology from a string."""
        self.graph = Graph()
        self.graph.parse(data=data, format=format)
        self._update_namespace_from_graph()

    def _update_namespace_from_graph(self):
        """Update namespace based on loaded ontology."""
        # Try to find the ontology URI
        for ont in self.graph.subjects(RDF.type, OWL.Ontology):
            if isinstance(ont, URIRef):
                self.ontology_uri = ont
                uri_str = str(ont)
                if uri_str.endswith("#"):
                    self.base_uri = uri_str
                else:
                    self.base_uri = uri_str + "#"
                self.namespace = Namespace(self.base_uri)
                break

        # Re-bind prefixes
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.graph.bind("skos", SKOS)
        self.graph.bind("dc", DC)
        self.graph.bind("dcterms", DCTERMS)

    def export_to_string(self, format: str = "turtle") -> str:
        """Export ontology to a string."""
        return self.graph.serialize(format=format)

    def export_to_file(self, file_path: str, format: str = "turtle"):
        """Export ontology to a file."""
        self.graph.serialize(destination=file_path, format=format)

    # ==================== VALIDATION & REASONING ====================

    def validate(self) -> List[Dict[str, str]]:
        """Validate the ontology and return issues."""
        issues = []

        # Check for classes without labels
        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(class_uri, BNode):
                continue
            if not self.graph.value(class_uri, RDFS.label):
                issues.append({
                    "severity": "warning",
                    "type": "missing_label",
                    "subject": self._local_name(class_uri),
                    "message": f"Class '{self._local_name(class_uri)}' has no label"
                })

        # Check for properties without domain/range
        for prop_uri in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            if isinstance(prop_uri, BNode):
                continue
            if not self.graph.value(prop_uri, RDFS.domain):
                issues.append({
                    "severity": "info",
                    "type": "missing_domain",
                    "subject": self._local_name(prop_uri),
                    "message": f"Object property '{self._local_name(prop_uri)}' has no domain"
                })
            if not self.graph.value(prop_uri, RDFS.range):
                issues.append({
                    "severity": "info",
                    "type": "missing_range",
                    "subject": self._local_name(prop_uri),
                    "message": f"Object property '{self._local_name(prop_uri)}' has no range"
                })

        for prop_uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(prop_uri, BNode):
                continue
            if not self.graph.value(prop_uri, RDFS.domain):
                issues.append({
                    "severity": "info",
                    "type": "missing_domain",
                    "subject": self._local_name(prop_uri),
                    "message": f"Data property '{self._local_name(prop_uri)}' has no domain"
                })

        # Check for orphan classes (no parent, no children, not used)
        all_classes = set()
        used_classes = set()

        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(class_uri, URIRef):
                all_classes.add(str(class_uri))

        # Classes used as domain/range
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            domain = self.graph.value(prop, RDFS.domain)
            range_ = self.graph.value(prop, RDFS.range)
            if domain:
                used_classes.add(str(domain))
            if range_:
                used_classes.add(str(range_))

        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            domain = self.graph.value(prop, RDFS.domain)
            if domain:
                used_classes.add(str(domain))

        # Classes with instances
        for ind in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            for cls in self.graph.objects(ind, RDF.type):
                if isinstance(cls, URIRef):
                    used_classes.add(str(cls))

        # Classes in hierarchy
        for cls in self.graph.subjects(RDFS.subClassOf, None):
            if isinstance(cls, URIRef):
                used_classes.add(str(cls))
        for cls in self.graph.objects(None, RDFS.subClassOf):
            if isinstance(cls, URIRef):
                used_classes.add(str(cls))

        # Check individuals have at least one class
        for ind_uri in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            classes = [c for c in self.graph.objects(ind_uri, RDF.type)
                      if c != OWL.NamedIndividual]
            if not classes:
                issues.append({
                    "severity": "warning",
                    "type": "untyped_individual",
                    "subject": self._local_name(ind_uri),
                    "message": f"Individual '{self._local_name(ind_uri)}' has no class type"
                })

        return issues

    def apply_reasoning(self, profile: str = "rdfs") -> int:
        """Apply reasoning to infer new triples."""
        initial_count = len(self.graph)

        if profile == "rdfs":
            owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self.graph)
        elif profile == "owl-rl":
            owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.graph)
        elif profile == "owl-rl-ext":
            owlrl.DeductiveClosure(owlrl.OWLRL_Extension).expand(self.graph)

        return len(self.graph) - initial_count

    # ==================== STATISTICS ====================

    def get_statistics(self) -> Dict[str, int]:
        """Get ontology statistics."""
        stats = {
            "classes": 0,
            "object_properties": 0,
            "data_properties": 0,
            "individuals": 0,
            "restrictions": 0,
            "total_triples": len(self.graph)
        }

        for _ in self.graph.subjects(RDF.type, OWL.Class):
            stats["classes"] += 1

        for _ in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            stats["object_properties"] += 1

        for _ in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            stats["data_properties"] += 1

        for _ in self.graph.subjects(RDF.type, OWL.NamedIndividual):
            stats["individuals"] += 1

        for _ in self.graph.subjects(RDF.type, OWL.Restriction):
            stats["restrictions"] += 1

        return stats
