# Orionbelt Ontology Builder

A Python-based web application for building, editing, maintaining, importing, and exporting OWL ontologies using the Turtle (TTL) format.

**Try it now:** The application is publicly available at [orionbelt.streamlit.app](https://orionbelt.streamlit.app/)

## Features

### Core Functionality

- **Create & Edit Ontologies** - Build ontologies from scratch or modify existing ones
- **Import/Export** - Support for Turtle (.ttl), RDF/XML (.owl), N-Triples (.nt), N3 (.n3), and JSON-LD formats
- **Validation** - Check for missing labels, domains, ranges, and other issues
- **Reasoning** - Apply RDFS and OWL-RL reasoning to infer new triples

### Ontology Elements

| Element               | Operations                                               |
| --------------------- | -------------------------------------------------------- |
| **Classes**           | Create, edit, delete with hierarchy (subClassOf)         |
| **Object Properties** | Domain/range, functional, transitive, symmetric, inverse |
| **Data Properties**   | XSD datatypes (string, integer, date, boolean, etc.)     |
| **Individuals**       | Create instances, assign classes, property values        |
| **Restrictions**      | someValuesFrom, allValuesFrom, cardinality constraints   |
| **Annotations**       | RDFS labels/comments, SKOS, Dublin Core metadata         |
| **Relations**         | equivalentClass, disjointWith, sameAs, differentFrom     |

## Installation

### Prerequisites

- Python 3.9+

### Setup

```bash
# Clone the repository
git clone https://github.com/ralfbecher/orionbelt-ontology-builder.git
cd orionbelt-ontology-builder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Start the Application

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
streamlit run app.py
```

Open your browser at http://localhost:8501

### Workflow

1. **Create New or Import** - Start with a new ontology or import an existing .ttl file
2. **Define Classes** - Create your class hierarchy
3. **Add Properties** - Define object and data properties
4. **Create Individuals** - Add instances of your classes
5. **Define Relations** - Set up class/property/individual relationships
6. **Add Restrictions** - Apply constraints to classes
7. **Validate** - Check for issues using the validation button
8. **Export** - Download your ontology as .ttl or other formats

## Pages Overview

### Dashboard

- Ontology metadata (title, description, version, creator)
- Base URI configuration
- Statistics overview
- Quick validation button

### Classes

- View class hierarchy
- Add/edit/delete classes
- Set parent classes (subClassOf)

### Properties

- **Object Properties** - Relations between individuals
  - Characteristics: Functional, InverseFunctional, Transitive, Symmetric
  - Domain and range (classes)
- **Data Properties** - Attributes with literal values
  - XSD datatypes: string, integer, float, boolean, date, dateTime, etc.

### Individuals

- Create named individuals
- Assign to classes
- Add property values (object or data)

### Relations

- **Class Relations**: subClassOf, equivalentClass, disjointWith
- **Property Relations**: subPropertyOf, equivalentProperty, inverseOf
- **Individual Relations**: sameAs, differentFrom

### Restrictions

- someValuesFrom / allValuesFrom
- hasValue
- Cardinality (min, max, exact)
- Qualified cardinality

### Annotations

- RDFS: label, comment, seeAlso, isDefinedBy
- SKOS: prefLabel, altLabel, definition, example, note
- Dublin Core: title, description, creator, contributor, date

### Import / Export

- **Import**: Upload files or paste content
- **Export**: Generate and download in multiple formats
- **New Ontology**: Create a fresh ontology with custom base URI

### Validation

- Check for missing labels, domains, ranges
- Identify untyped individuals
- Apply OWL reasoning (RDFS, OWL-RL)

### Visualization

- Class hierarchy tree view
- Statistics charts

## Supported Formats

| Format    | Extension  | Import | Export |
| --------- | ---------- | ------ | ------ |
| Turtle    | .ttl       | ✅     | ✅     |
| RDF/XML   | .owl, .rdf | ✅     | ✅     |
| N-Triples | .nt        | ✅     | ✅     |
| N3        | .n3        | ✅     | ✅     |
| JSON-LD   | .jsonld    | ❌     | ✅     |

## Project Structure

```
orionbelt-ontology-builder/
├── app.py                 # Streamlit UI application
├── ontology_manager.py    # Core OWL operations using rdflib
├── requirements.txt       # Python dependencies
├── lib/                   # Frontend vendor libraries
│   ├── vis-9.1.2/         # vis-network for graph visualization
│   ├── tom-select/        # Tom Select for enhanced dropdowns
│   └── bindings/          # JavaScript utility bindings
├── .gitignore
├── README.md
└── venv/                  # Virtual environment (not in repo)
```

## Dependencies

- **streamlit** - Web UI framework
- **rdflib** - RDF/OWL parsing and serialization
- **owlrl** - OWL-RL reasoning
- **networkx** - Graph operations
- **pyvis** - Network visualization

## OWL Concepts Reference

### Class Axioms

```turtle
:Person a owl:Class .
:Student rdfs:subClassOf :Person .
:Male owl:disjointWith :Female .
```

### Property Axioms

```turtle
:hasParent a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Person ;
    owl:inverseOf :hasChild .

:hasAge a owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:range xsd:integer .
```

### Restrictions

```turtle
:Parent rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty :hasChild ;
    owl:someValuesFrom :Person
] .
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

Orionbelt is a project by RALFORION d.o.o.
