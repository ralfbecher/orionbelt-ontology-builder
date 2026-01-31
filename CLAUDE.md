# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app runs at http://localhost:8501

## Architecture

This is a Streamlit web application for building and managing OWL ontologies. It has two main components:

### app.py - UI Layer (~2500 lines)
Single-file Streamlit application with tabbed interface. Key patterns:
- Uses `st.session_state.ontology` to hold the `OntologyManager` instance
- Flash messages via `set_flash_message()` / `display_flash_message()` for post-rerun notifications
- Graph visualization uses vis-network (loaded from `lib/vis-9.1.2/`) via HTML components
- Enhanced dropdowns use Tom Select (loaded from `lib/tom-select/`)

UI tabs: Dashboard, Classes, Properties, Individuals, Relations, Restrictions, Annotations, Import/Export, Validation, Visualization

### ontology_manager.py - Core Logic (~1500 lines)
Wraps rdflib for OWL ontology operations. Key patterns:
- `self.graph` is the rdflib Graph containing all triples
- `self.namespace` is the Namespace for the ontology's base URI
- Uses rdflib's OWL, RDF, RDFS, XSD, SKOS, DC, DCTERMS namespaces
- Reasoning via owlrl (RDFS and OWL-RL)

Key methods: `add_class()`, `add_object_property()`, `add_data_property()`, `add_individual()`, `add_restriction()`, `validate()`, `apply_reasoning()`, `load_from_*()`, `serialize()`

## Deployed Version

Live at: orionbelt.streamlit.app

## Future Enhancements

### User Session Storage (Browser Local Storage)
For per-user settings on Streamlit Cloud, use `streamlit-local-storage` instead of .env files:

```python
from streamlit_local_storage import LocalStorage
local_storage = LocalStorage()
local_storage.setItem("openai_api_key", user_api_key)
local_storage.setItem("user_settings", json.dumps(settings_dict))
```
