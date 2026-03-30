<p align="center">
  <img src="docs/assets/ORIONBELT Logo.png" alt="OrionBelt Logo" width="400">
</p>

<h1 align="center">OrionBelt Ontology Builder</h1>

<p align="center"><strong>Build, edit, and manage OWL ontologies visually with a Streamlit web application</strong></p>

[![GitHub stars](https://img.shields.io/github/stars/ralfbecher/orionbelt-ontology-builder?style=social)](https://github.com/ralfbecher/orionbelt-ontology-builder)
[![Version 0.9.0](https://img.shields.io/badge/version-0.9.0-purple.svg)](https://github.com/ralfbecher/orionbelt-ontology-builder/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-orange.svg)](https://github.com/ralfbecher/orionbelt-ontology-builder/blob/main/LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![rdflib](https://img.shields.io/badge/rdflib-7.0+-2E86C1.svg)](https://rdflib.readthedocs.io)
[![OWL-RL](https://img.shields.io/badge/OWL--RL-reasoning-green.svg)](https://owl-rl.readthedocs.io)
[![vis-network](https://img.shields.io/badge/vis--network-9.1-97C2FC.svg)](https://visjs.github.io/vis-network/docs/network/)

**Try it now:** [orionbelt.streamlit.app](https://orionbelt.streamlit.app/)

## Features

### Core Functionality

- **Create & Edit Ontologies** - Build ontologies from scratch or modify existing ones
- **Import/Export** - Support for Turtle (.ttl), RDF/XML (.owl), N-Triples (.nt), N3 (.n3), and JSON-LD formats
- **Validation** - Check for missing labels, domains, ranges, and other issues
- **Reasoning** - Apply RDFS and OWL-RL reasoning to infer new triples
- **Undo/Redo** - Full undo/redo history for all ontology modifications
- **Global Search** - Search across all ontology elements
- **Graph Visualization** - Interactive vis-network graph with class filtering and layout options

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

## Quick Start

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/ralfbecher/orionbelt-ontology-builder.git
cd orionbelt-ontology-builder
pip install -r requirements.txt
```

### Run the Application

```bash
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

- Interactive graph visualization with vis-network
- Class hierarchy tree view
- Statistics charts
- Class filter and configurable graph limits

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
├── pyproject.toml         # Project metadata
├── lib/                   # Frontend vendor libraries
│   ├── vis-9.1.2/         # vis-network for graph visualization
│   ├── tom-select/        # Tom Select for enhanced dropdowns
│   └── bindings/          # JavaScript utility bindings
└── docs/
    └── assets/            # Logo assets
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

## Companion Project

### [OrionBelt Analytics](https://github.com/ralfbecher/orionbelt-analytics)

OrionBelt Analytics is an ontology-based MCP server that analyzes relational database schemas and generates RDF/OWL ontologies with embedded SQL mappings. It connects to PostgreSQL, Snowflake, and Dremio, providing AI assistants with deep structural and semantic understanding of your data. Together with the Ontology Builder, they form a comprehensive toolkit for ontology-driven data modeling.

## License

Copyright 2025 [RALFORION d.o.o.](https://ralforion.com)

Licensed under the [Business Source License 1.1](LICENSE). The Licensed Work will convert to Apache License 2.0 on 2030-03-30.

By contributing to this project, you agree to the [Contributor License Agreement](CLA.md).

---

<p align="center">
  <a href="https://ralforion.com">
    <img src="docs/assets/RALFORION doo Logo.png" alt="RALFORION d.o.o." width="200">
  </a>
</p>
