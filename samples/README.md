# Sample Ontologies

Real-world ontologies for testing and demonstration.

## Included

| File | Source | Description |
|------|--------|-------------|
| `pizza.owl` | [Stanford/Manchester](https://protege.stanford.edu/ontologies/pizza/pizza.owl) | Classic OWL tutorial ontology, 100+ classes |
| `wine.owl` | [W3C OWL Guide](https://www.w3.org/TR/owl-guide/wine.rdf) | Wine ontology with rich class/property structure |
| `foaf.rdf` | [FOAF Project](http://xmlns.com/foaf/spec/) | Friend of a Friend vocabulary |
| `prov-o.ttl` | [W3C PROV](https://www.w3.org/ns/prov-o) | Provenance Ontology |
| `goodrelations.owl` | [GoodRelations](http://purl.org/goodrelations/v1) | E-commerce ontology |
| `dcterms.ttl` | [Dublin Core](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) | Dublin Core metadata terms |

## Large files (not in repo)

Download these separately if needed:

```bash
# Schema.org (~1.1 MB, 800+ classes)
curl -sL -o samples/schema-org.ttl "https://schema.org/version/latest/schemaorg-current-https.ttl"

# UNESCO Thesaurus (~3 MB, 4000+ SKOS concepts)
curl -sL -o samples/unesco-thesaurus.ttl "https://vocabularies.unesco.org/exports/thesaurus/latest/unesco-thesaurus.ttl"
```
