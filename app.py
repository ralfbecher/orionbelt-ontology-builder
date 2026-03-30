"""
OrionBelt Ontology Builder - A Streamlit application for building, editing,
and managing OWL ontologies.
"""

import streamlit as st
import json

APP_VERSION = "0.9.0"

# Page configuration
st.set_page_config(
    page_title="OrionBelt Ontology Builder",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    .success-message {
        padding: 10px;
        background-color: #d4edda;
        border-radius: 4px;
        color: #155724;
    }
    .warning-message {
        padding: 10px;
        background-color: #fff3cd;
        border-radius: 4px;
        color: #856404;
    }
    .error-message {
        padding: 10px;
        background-color: #f8d7da;
        border-radius: 4px;
        color: #721c24;
    }
    /* Reduce top margin/padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0.5rem !important;
    }
    .stMainBlockContainer {
        padding-top: 2rem !important;
        padding-bottom: 0.5rem !important;
    }
    /* Reduce iframe container margins */
    iframe {
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_ontology_manager_class():
    """Lazy load the OntologyManager class."""
    from ontology_manager import OntologyManager
    return OntologyManager


def init_session_state():
    """Initialize session state variables."""
    if "ontology" not in st.session_state:
        with st.spinner("Loading ontology engine..."):
            OntologyManager = get_ontology_manager_class()
            st.session_state.ontology = OntologyManager()
    if "undo_manager" not in st.session_state:
        try:
            from ontology_manager import UndoManager
            st.session_state.undo_manager = UndoManager(st.session_state.ontology)
        except ImportError as e:
            st.error(f"Failed to load UndoManager: {e}")
            st.session_state.undo_manager = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "flash_message" not in st.session_state:
        st.session_state.flash_message = None


def save_checkpoint(label: str = "Edit"):
    """Save a snapshot to the undo history after a mutation."""
    if st.session_state.get("undo_manager"):
        st.session_state.undo_manager.checkpoint(label)


def show_message(message: str, type: str = "info"):
    """Display a message to the user."""
    if type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    else:
        st.info(message)


def set_flash_message(message: str, type: str = "info"):
    """Set a flash message to be displayed after rerun."""
    st.session_state.flash_message = {"message": message, "type": type}


def display_flash_message():
    """Display and clear any pending flash message."""
    if st.session_state.get("flash_message"):
        msg = st.session_state.flash_message
        show_message(msg["message"], msg["type"])
        st.session_state.flash_message = None


def confirm_delete(resource_name: str, resource_type: str, key_suffix: str) -> bool:
    """Show delete impact and confirmation UI. Returns True when confirmed."""
    ont = st.session_state.ontology
    confirm_key = f"confirm_delete_{key_suffix}"

    if st.session_state.get(confirm_key):
        impact = ont.get_delete_impact(resource_name, resource_type)
        summary = ont.format_delete_impact(impact)
        st.warning(summary)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Confirm Delete", key=f"yes_{confirm_key}", type="primary"):
                st.session_state[confirm_key] = False
                return True
        with col_no:
            if st.button("Cancel", key=f"no_{confirm_key}"):
                st.session_state[confirm_key] = False
                st.rerun()
    return False


def format_label_name(name: str, label: str) -> str:
    """Format display string as 'Label (name)' if label exists and differs from name."""
    if label and label != name:
        return f"{label} ({name})"
    return name


def build_class_options(classes: list, include_none: bool = False) -> tuple:
    """Build class dropdown options with 'Label (name)' format, sorted by display text.

    Returns:
        tuple: (display_options, name_lookup_dict)
    """
    options = []
    lookup = {}

    # Build display strings and sort
    items = []
    for c in classes:
        display = format_label_name(c["name"], c.get("label"))
        items.append(display)
        lookup[display] = c["name"]

    # Sort alphabetically by display text (case-insensitive)
    items.sort(key=lambda x: x.lower())

    if include_none:
        options.append("None")
        lookup["None"] = None

    options.extend(items)
    return options, lookup


def build_property_options(properties: list, include_none: bool = False) -> tuple:
    """Build property dropdown options with 'Label (name)' format, sorted by display text.

    Returns:
        tuple: (display_options, name_lookup_dict)
    """
    options = []
    lookup = {}

    # Build display strings and sort
    items = []
    for p in properties:
        display = format_label_name(p["name"], p.get("label"))
        items.append(display)
        lookup[display] = p["name"]

    # Sort alphabetically by display text (case-insensitive)
    items.sort(key=lambda x: x.lower())

    if include_none:
        options.append("None")
        lookup["None"] = None

    options.extend(items)
    return options, lookup


def build_individual_options(individuals: list, include_none: bool = False) -> tuple:
    """Build individual dropdown options with 'Label (name)' format, sorted by display text.

    Returns:
        tuple: (display_options, name_lookup_dict)
    """
    options = []
    lookup = {}

    # Build display strings and sort
    items = []
    for i in individuals:
        display = format_label_name(i["name"], i.get("label"))
        items.append(display)
        lookup[display] = i["name"]

    # Sort alphabetically by display text (case-insensitive)
    items.sort(key=lambda x: x.lower())

    if include_none:
        options.append("None")
        lookup["None"] = None

    options.extend(items)
    return options, lookup


def render_dashboard():
    """Render the dashboard/overview page."""
    st.header("Dashboard")

    ont = st.session_state.ontology
    stats = ont.get_statistics()
    metadata = ont.get_ontology_metadata()

    # Ontology metadata section
    st.subheader("Ontology Information")
    col1, col2 = st.columns(2)

    with col1:
        base_uri = st.text_input("Base URI", value=ont.base_uri,
                                 help="The namespace URI for your ontology (e.g., http://example.org/ontology#)")
        label = st.text_input("Label (rdfs:label)", value=metadata.get("label", ""))
        comment = st.text_area("Comment (rdfs:comment)", value=metadata.get("comment", ""))

    with col2:
        version_iri = st.text_input("Version IRI", value=metadata.get("version_iri", ""),
                                    help="Optional IRI identifying this version of the ontology")
        creator = st.text_input("Creator", value=metadata.get("creator", ""))

        if st.button("Update Metadata"):
            # Update base URI if changed
            if base_uri and base_uri != ont.base_uri:
                ont.set_base_uri(base_uri)
                show_message(f"Base URI updated to: {ont.base_uri}", "success")

            ont.set_ontology_metadata(label=label, comment=comment,
                                      creator=creator,
                                      version_iri=version_iri if version_iri else None)
            save_checkpoint("Update metadata")
            show_message("Metadata updated successfully!", "success")
            st.rerun()

    # Imports section
    st.subheader("Ontology Imports")
    imports = ont.get_imports()

    if imports:
        for imp in imports:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.code(imp)
            with col2:
                if st.button("Remove", key=f"rm_import_{imp}"):
                    ont.remove_import(imp)
                    st.rerun()

    with st.expander("Add Import"):
        new_import = st.text_input("Import URI", placeholder="http://example.org/other-ontology")
        if st.button("Add Import"):
            if new_import:
                ont.add_import(new_import)
                show_message(f"Import added: {new_import}", "success")
                st.rerun()

    # Prefixes section
    st.subheader("Namespace Prefixes")
    all_prefixes = ont.get_all_prefixes()

    if all_prefixes:
        prefix_data = {"Prefix": [], "Namespace": [], "Source": []}
        for p in all_prefixes:
            prefix_data["Prefix"].append(p["prefix"])
            prefix_data["Namespace"].append(p["namespace"])
            prefix_data["Source"].append(p["source"])
        st.dataframe(prefix_data, width="stretch", hide_index=True)
    else:
        st.info("No prefixes defined.")

    with st.expander("Add Custom Prefix"):
        col_pfx, col_ns = st.columns(2)
        with col_pfx:
            new_prefix = st.text_input("Prefix", placeholder="foaf", key="new_prefix_name")
        with col_ns:
            new_ns = st.text_input("Namespace URI",
                                   placeholder="http://xmlns.com/foaf/0.1/",
                                   key="new_prefix_ns")
        if st.button("Add Prefix", key="add_prefix_btn"):
            if new_prefix and new_ns:
                ont.add_prefix(new_prefix, new_ns)
                save_checkpoint("Add prefix")
                set_flash_message(f"Added prefix '{new_prefix}'", "success")
                st.rerun()
            else:
                show_message("Both prefix and namespace URI are required.", "warning")

    # Show remove buttons for custom prefixes
    custom_pfx = [p for p in all_prefixes if p["source"] == "custom"]
    if custom_pfx:
        st.caption("Remove custom prefixes:")
        for p in custom_pfx:
            col_name, col_rm = st.columns([4, 1])
            with col_name:
                st.text(f"{p['prefix']}: {p['namespace']}")
            with col_rm:
                if st.button("Remove", key=f"rm_pfx_{p['prefix']}"):
                    ont.remove_prefix(p["prefix"])
                    save_checkpoint("Remove prefix")
                    set_flash_message(f"Removed prefix '{p['prefix']}'", "success")
                    st.rerun()

    st.divider()

    # Statistics
    st.subheader("Statistics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Classes", stats["classes"])
    with col2:
        st.metric("Object Properties", stats["object_properties"])
    with col3:
        st.metric("Data Properties", stats["data_properties"])
    with col4:
        st.metric("Individuals", stats["individuals"])
    with col5:
        st.metric("Restrictions", stats["restrictions"])
    with col6:
        st.metric("Content Triples", stats["content_triples"])

    st.divider()

    # Quick validation section
    st.subheader("Quick Validation")
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("🔍 Validate Ontology", type="primary"):
            issues = ont.validate()
            st.session_state.validation_results = issues

    with col2:
        if "validation_results" in st.session_state:
            issues = st.session_state.validation_results
            if not issues:
                st.success("✅ No issues found! The ontology is valid.")
            else:
                errors = [i for i in issues if i["severity"] == "error"]
                warnings = [i for i in issues if i["severity"] == "warning"]
                infos = [i for i in issues if i["severity"] == "info"]

                if errors:
                    st.error(f"❌ {len(errors)} error(s)")
                if warnings:
                    st.warning(f"⚠️ {len(warnings)} warning(s)")
                if infos:
                    st.info(f"ℹ️ {len(infos)} info message(s)")

                with st.expander("View Details"):
                    for issue in issues:
                        icon = "❌" if issue["severity"] == "error" else "⚠️" if issue["severity"] == "warning" else "ℹ️"
                        st.write(f"{icon} **{issue['subject']}**: {issue['message']}")


def render_classes():
    """Render the classes management page."""
    st.header("Classes")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]

    tab1, tab2, tab3 = st.tabs(["View Classes", "Add Class", "Edit/Delete Class"])

    with tab1:
        if not classes:
            st.info("No classes defined yet. Add a class to get started.")
        else:
            # Class hierarchy view
            st.subheader("Class Hierarchy")

            # Sort classes by display name, but put actively viewed class first
            sorted_classes = sorted(classes, key=lambda c: format_label_name(c['name'], c.get('label')).lower())
            _active_cls = next((c for c in sorted_classes if st.session_state.get(f"view_class_{c['name']}", False) or st.session_state.get(f"edit_class_{c['name']}", False)), None)
            if _active_cls:
                for c in sorted_classes:
                    if c["name"] != _active_cls["name"]:
                        st.session_state.pop(f"view_class_{c['name']}", None)
                        st.session_state.pop(f"edit_class_{c['name']}", None)

            for cls in sorted_classes:
                display_name = format_label_name(cls['name'], cls.get('label'))
                _cls_expanded = st.session_state.get(f"view_class_{cls['name']}", False) or st.session_state.get(f"edit_class_{cls['name']}", False)
                with st.expander(f"📦 **{display_name}**", expanded=_cls_expanded):
                    st.write(f"**URI:** {cls['uri']}")

                    btn_view, btn_edit, btn_del, _ = st.columns([1, 1, 1, 4])
                    with btn_view:
                        if st.button("👁️ View", key=f"btn_view_class_{cls['name']}", use_container_width=True):
                            st.session_state[f"view_class_{cls['name']}"] = not st.session_state.get(f"view_class_{cls['name']}", False)
                            st.session_state[f"edit_class_{cls['name']}"] = False
                            st.rerun()
                    with btn_edit:
                        if st.button("✏️ Edit", key=f"btn_edit_class_{cls['name']}", use_container_width=True):
                            st.session_state[f"edit_class_{cls['name']}"] = not st.session_state.get(f"edit_class_{cls['name']}", False)
                            st.session_state[f"view_class_{cls['name']}"] = False
                            st.rerun()
                    with btn_del:
                        if st.button("🗑️ Delete", key=f"btn_del_class_{cls['name']}", use_container_width=True):
                            st.session_state[f"confirm_delete_class_{cls['name']}"] = True
                            st.rerun()

                    # View details
                    if st.session_state.get(f"view_class_{cls['name']}", False):
                        st.divider()
                        st.write(f"**Name:** {cls['name']}")
                        st.write(f"**Label:** {cls['label'] or '—'}")
                        st.write(f"**Comment:** {cls['comment'] or '—'}")
                        st.write(f"**Parent Class:** {', '.join(cls['parents']) if cls['parents'] else '—'}")
                        if cls["children"]:
                            st.write(f"**Children:** {', '.join(cls['children'])}")
                        if st.button("✏️ Edit", key=f"btn_view_to_edit_class_{cls['name']}"):
                            st.session_state[f"view_class_{cls['name']}"] = False
                            st.session_state[f"edit_class_{cls['name']}"] = True
                            st.rerun()

                    if confirm_delete(cls["name"], "class", f"class_{cls['name']}"):
                        ont.delete_class(cls["name"])
                        save_checkpoint("Delete class")
                        set_flash_message(f"Class '{cls['name']}' deleted!", "success")
                        st.rerun()

                    # Inline edit form
                    if st.session_state.get(f"edit_class_{cls['name']}", False):
                        st.divider()
                        with st.form(f"edit_class_form_{cls['name']}"):
                            new_name = st.text_input("Name (URI local part)", value=cls["name"], key=f"name_{cls['name']}")
                            new_label = st.text_input("Label", value=cls["label"], key=f"lbl_{cls['name']}")
                            new_comment = st.text_area("Comment", value=cls["comment"], key=f"cmt_{cls['name']}")
                            other_classes = [c for c in class_names if c != cls["name"]]
                            current_parent = cls["parents"][0] if cls["parents"] else "None"
                            new_parent = st.selectbox("Parent Class",
                                options=["None"] + other_classes,
                                index=0 if current_parent == "None" else
                                      (other_classes.index(current_parent) + 1 if current_parent in other_classes else 0),
                                key=f"par_{cls['name']}")

                            if st.form_submit_button("Save Changes"):
                                # Handle rename first
                                if new_name and new_name != cls["name"]:
                                    if ont.rename_class(cls["name"], new_name):
                                        current_name = new_name
                                        save_checkpoint("Rename class")
                                        show_message(f"Class renamed to '{new_name}'", "success")
                                    else:
                                        show_message(f"Cannot rename: '{new_name}' already exists!", "error")
                                        st.rerun()
                                else:
                                    current_name = cls["name"]

                                if cls["parents"] and new_parent != cls["parents"][0]:
                                    ont.update_class(current_name, remove_parent=cls["parents"][0])
                                ont.update_class(current_name,
                                    new_label=new_label,
                                    new_comment=new_comment,
                                    new_parent=new_parent if new_parent != "None" else None)
                                save_checkpoint("Update class")
                                st.session_state[f"edit_class_{cls['name']}"] = False
                                show_message(f"Class '{current_name}' updated!", "success")
                                st.rerun()

            # Table view
            st.subheader("All Classes")
            class_data = []
            for c in sorted_classes:
                class_data.append({
                    "Name": c["name"],
                    "Label": c["label"],
                    "Parents": ", ".join(c["parents"]),
                    "Children": ", ".join(c["children"]),
                    "Comment": c["comment"][:50] + "..." if len(c["comment"]) > 50 else c["comment"]
                })
            st.dataframe(class_data, width="stretch")

    with tab2:
        st.subheader("Add New Class")

        with st.form("add_class_form"):
            name = st.text_input("Class Name *", help="Local name for the class (e.g., 'Person')")
            label = st.text_input("Label", help="Human-readable label")
            comment = st.text_area("Comment", help="Description of the class")
            parent_options, parent_lookup = build_class_options(classes, include_none=True)
            parent_display = st.selectbox("Parent Class", options=parent_options,
                                 help="Select a parent class for hierarchy")

            submitted = st.form_submit_button("Add Class")
            if submitted:
                if not name:
                    show_message("Class name is required!", "error")
                elif name in [c["name"] for c in classes]:
                    show_message(f"Class '{name}' already exists!", "error")
                else:
                    parent_val = parent_lookup.get(parent_display)
                    ont.add_class(name, parent=parent_val, label=label, comment=comment)
                    save_checkpoint("Add class")
                    show_message(f"Class '{name}' added successfully!", "success")
                    st.rerun()

    with tab3:
        st.subheader("Edit or Delete Class")

        if not classes:
            st.info("No classes to edit.")
        else:
            # Build options with Label (name) format
            class_options, class_lookup = build_class_options(classes)
            selected_display = st.selectbox("Select Class", options=class_options, key="edit_class_select")
            selected_class = class_lookup.get(selected_display)

            if selected_class:
                class_info = next((c for c in classes if c["name"] == selected_class), None)

                if class_info:
                    st.subheader(f"Edit: {selected_class}")

                    with st.form("edit_class_form"):
                        new_label = st.text_input("Label", value=class_info["label"])
                        new_comment = st.text_area("Comment", value=class_info["comment"])

                        other_classes = [c for c in class_names if c != selected_class]
                        current_parent = class_info["parents"][0] if class_info["parents"] else "None"
                        new_parent = st.selectbox("Parent Class",
                                                  options=["None"] + other_classes,
                                                  index=0 if current_parent == "None"
                                                  else (other_classes.index(current_parent) + 1
                                                       if current_parent in other_classes else 0))

                        col1, col2 = st.columns(2)
                        with col1:
                            update_btn = st.form_submit_button("Update Class")
                        with col2:
                            delete_btn = st.form_submit_button("Delete Class", type="secondary")

                        if update_btn:
                            # Remove old parent if changed
                            if class_info["parents"] and new_parent != class_info["parents"][0]:
                                ont.update_class(selected_class,
                                               remove_parent=class_info["parents"][0])

                            ont.update_class(selected_class,
                                           new_label=new_label,
                                           new_comment=new_comment,
                                           new_parent=new_parent if new_parent != "None" else None)
                            save_checkpoint("Update class")
                            show_message(f"Class '{selected_class}' updated!", "success")
                            st.rerun()

                        if delete_btn:
                            st.session_state[f"confirm_delete_class_detail_{selected_class}"] = True
                            st.rerun()

                if confirm_delete(selected_class, "class", f"class_detail_{selected_class}"):
                    ont.delete_class(selected_class)
                    save_checkpoint("Delete class")
                    set_flash_message(f"Class '{selected_class}' deleted!", "success")
                    st.rerun()

                # Resource usages / backlinks
                with st.expander("Show Usages"):
                    usages = ont.get_resource_usages(selected_class)
                    if usages["inbound"]:
                        st.markdown("**Referenced by:**")
                        for u in usages["inbound"]:
                            st.write(f"- {u['subject']} *{u['predicate']}*")
                    if usages["outbound"]:
                        st.markdown("**References:**")
                        for u in usages["outbound"]:
                            st.write(f"- *{u['predicate']}* {u['object']}")
                    if not usages["inbound"] and not usages["outbound"]:
                        st.caption("No usages found.")


def render_properties():
    """Render the properties management page."""
    st.header("Properties")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    obj_prop_names = [p["name"] for p in object_props]
    data_prop_names = [p["name"] for p in data_props]

    tab1, tab2, tab3, tab4 = st.tabs([
        "Object Properties", "Data Properties",
        "Add Object Property", "Add Data Property"
    ])

    with tab1:
        st.subheader("Object Properties")
        if not object_props:
            st.info("No object properties defined yet.")
        else:
            # Filter by domain class
            filter_class_obj = st.selectbox(
                "Filter by Domain Class",
                options=["All"] + class_names + ["(No domain)"],
                key="filter_obj_prop_class"
            )

            filtered_obj_props = object_props
            if filter_class_obj == "(No domain)":
                filtered_obj_props = [p for p in object_props if not p["domain"]]
            elif filter_class_obj != "All":
                filtered_obj_props = [p for p in object_props if p["domain"] == filter_class_obj]

            st.caption(f"Showing {len(filtered_obj_props)} of {len(object_props)} properties")

            _active_op = next((p for p in filtered_obj_props if st.session_state.get(f"view_objprop_{p['name']}", False) or st.session_state.get(f"edit_objprop_{p['name']}", False)), None)
            if _active_op:
                for p in filtered_obj_props:
                    if p["name"] != _active_op["name"]:
                        st.session_state.pop(f"view_objprop_{p['name']}", None)
                        st.session_state.pop(f"edit_objprop_{p['name']}", None)

            for prop in filtered_obj_props:
                _op_expanded = st.session_state.get(f"view_objprop_{prop['name']}", False) or st.session_state.get(f"edit_objprop_{prop['name']}", False)
                with st.expander(f"🔗 **{prop['name']}** ({prop['domain'] or '?'} → {prop['range'] or '?'})", expanded=_op_expanded):
                    st.write(f"**URI:** {prop['uri']}")

                    btn_view, btn_edit, btn_del, _ = st.columns([1, 1, 1, 4])
                    with btn_view:
                        if st.button("👁️ View", key=f"btn_view_objprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"view_objprop_{prop['name']}"] = not st.session_state.get(f"view_objprop_{prop['name']}", False)
                            st.session_state[f"edit_objprop_{prop['name']}"] = False
                            st.rerun()
                    with btn_edit:
                        if st.button("✏️ Edit", key=f"btn_edit_objprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"edit_objprop_{prop['name']}"] = not st.session_state.get(f"edit_objprop_{prop['name']}", False)
                            st.session_state[f"view_objprop_{prop['name']}"] = False
                            st.rerun()
                    with btn_del:
                        if st.button("🗑️ Delete", key=f"btn_del_objprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"confirm_delete_objprop_{prop['name']}"] = True
                            st.rerun()

                    # View details
                    if st.session_state.get(f"view_objprop_{prop['name']}", False):
                        st.divider()
                        st.write(f"**Name:** {prop['name']}")
                        st.write(f"**Label:** {prop['label'] or '—'}")
                        st.write(f"**Comment:** {prop['comment'] or '—'}")
                        st.write(f"**Domain:** {prop['domain'] or '—'}")
                        st.write(f"**Range:** {prop['range'] or '—'}")
                        st.write(f"**Characteristics:** {', '.join(prop['characteristics']) if prop['characteristics'] else '—'}")
                        st.write(f"**Inverse of:** {prop.get('inverse_of') or '—'}")
                        if st.button("✏️ Edit", key=f"btn_view_to_edit_objprop_{prop['name']}"):
                            st.session_state[f"view_objprop_{prop['name']}"] = False
                            st.session_state[f"edit_objprop_{prop['name']}"] = True
                            st.rerun()

                    if confirm_delete(prop["name"], "property", f"objprop_{prop['name']}"):
                        ont.delete_property(prop["name"])
                        save_checkpoint("Delete property")
                        set_flash_message(f"Property '{prop['name']}' deleted!", "success")
                        st.rerun()

                    # Inline edit form
                    if st.session_state.get(f"edit_objprop_{prop['name']}", False):
                        st.divider()
                        with st.form(f"edit_objprop_form_{prop['name']}"):
                            new_name = st.text_input("Name (URI local part)", value=prop["name"], key=f"objp_name_{prop['name']}")
                            new_label = st.text_input("Label", value=prop["label"], key=f"objp_lbl_{prop['name']}")
                            new_comment = st.text_area("Comment", value=prop["comment"], key=f"objp_cmt_{prop['name']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                new_domain = st.selectbox("Domain", options=["None"] + class_names,
                                    index=0 if not prop["domain"] else (class_names.index(prop["domain"]) + 1 if prop["domain"] in class_names else 0),
                                    key=f"objp_dom_{prop['name']}")
                            with col2:
                                new_range = st.selectbox("Range", options=["None"] + class_names,
                                    index=0 if not prop["range"] else (class_names.index(prop["range"]) + 1 if prop["range"] in class_names else 0),
                                    key=f"objp_rng_{prop['name']}")

                            if st.form_submit_button("Save Changes"):
                                # Handle rename first
                                if new_name and new_name != prop["name"]:
                                    if ont.rename_property(prop["name"], new_name):
                                        current_name = new_name
                                        save_checkpoint("Rename property")
                                        show_message(f"Property renamed to '{new_name}'", "success")
                                    else:
                                        show_message(f"Cannot rename: '{new_name}' already exists!", "error")
                                        st.rerun()
                                else:
                                    current_name = prop["name"]

                                ont.update_property(current_name,
                                    new_label=new_label,
                                    new_comment=new_comment,
                                    new_domain=new_domain if new_domain != "None" else "",
                                    new_range=new_range if new_range != "None" else "")
                                save_checkpoint("Update property")
                                st.session_state[f"edit_objprop_{prop['name']}"] = False
                                show_message(f"Property '{current_name}' updated!", "success")
                                st.rerun()

    with tab2:
        st.subheader("Data Properties")
        if not data_props:
            st.info("No data properties defined yet.")
        else:
            # Filter by domain class
            filter_class_data = st.selectbox(
                "Filter by Domain Class",
                options=["All"] + class_names + ["(No domain)"],
                key="filter_data_prop_class"
            )

            filtered_data_props = data_props
            if filter_class_data == "(No domain)":
                filtered_data_props = [p for p in data_props if not p["domain"]]
            elif filter_class_data != "All":
                filtered_data_props = [p for p in data_props if p["domain"] == filter_class_data]

            st.caption(f"Showing {len(filtered_data_props)} of {len(data_props)} properties")

            datatypes = list(get_ontology_manager_class().XSD_DATATYPES.keys())

            _active_dp = next((p for p in filtered_data_props if st.session_state.get(f"view_dataprop_{p['name']}", False) or st.session_state.get(f"edit_dataprop_{p['name']}", False)), None)
            if _active_dp:
                for p in filtered_data_props:
                    if p["name"] != _active_dp["name"]:
                        st.session_state.pop(f"view_dataprop_{p['name']}", None)
                        st.session_state.pop(f"edit_dataprop_{p['name']}", None)

            for prop in filtered_data_props:
                _dp_expanded = st.session_state.get(f"view_dataprop_{prop['name']}", False) or st.session_state.get(f"edit_dataprop_{prop['name']}", False)
                with st.expander(f"📝 **{prop['name']}** ({prop['domain'] or '?'} → {prop['range']})", expanded=_dp_expanded):
                    st.write(f"**URI:** {prop['uri']}")

                    btn_view, btn_edit, btn_del, _ = st.columns([1, 1, 1, 4])
                    with btn_view:
                        if st.button("👁️ View", key=f"btn_view_dataprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"view_dataprop_{prop['name']}"] = not st.session_state.get(f"view_dataprop_{prop['name']}", False)
                            st.session_state[f"edit_dataprop_{prop['name']}"] = False
                            st.rerun()
                    with btn_edit:
                        if st.button("✏️ Edit", key=f"btn_edit_dataprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"edit_dataprop_{prop['name']}"] = not st.session_state.get(f"edit_dataprop_{prop['name']}", False)
                            st.session_state[f"view_dataprop_{prop['name']}"] = False
                            st.rerun()
                    with btn_del:
                        if st.button("🗑️ Delete", key=f"btn_del_dataprop_{prop['name']}", use_container_width=True):
                            st.session_state[f"confirm_delete_dataprop_{prop['name']}"] = True
                            st.rerun()

                    # View details
                    if st.session_state.get(f"view_dataprop_{prop['name']}", False):
                        st.divider()
                        st.write(f"**Name:** {prop['name']}")
                        st.write(f"**Label:** {prop['label'] or '—'}")
                        st.write(f"**Comment:** {prop['comment'] or '—'}")
                        st.write(f"**Domain:** {prop['domain'] or '—'}")
                        st.write(f"**Range (Datatype):** {prop['range']}")
                        st.write(f"**Functional:** {'Yes' if prop['functional'] else 'No'}")
                        if st.button("✏️ Edit", key=f"btn_view_to_edit_dataprop_{prop['name']}"):
                            st.session_state[f"view_dataprop_{prop['name']}"] = False
                            st.session_state[f"edit_dataprop_{prop['name']}"] = True
                            st.rerun()

                    if confirm_delete(prop["name"], "property", f"dataprop_{prop['name']}"):
                        ont.delete_property(prop["name"])
                        save_checkpoint("Delete property")
                        set_flash_message(f"Property '{prop['name']}' deleted!", "success")
                        st.rerun()

                    # Inline edit form
                    if st.session_state.get(f"edit_dataprop_{prop['name']}", False):
                        st.divider()
                        with st.form(f"edit_dataprop_form_{prop['name']}"):
                            new_name = st.text_input("Name (URI local part)", value=prop["name"], key=f"dp_name_{prop['name']}")
                            new_label = st.text_input("Label", value=prop["label"], key=f"dp_lbl_{prop['name']}")
                            new_comment = st.text_area("Comment", value=prop["comment"], key=f"dp_cmt_{prop['name']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                new_domain = st.selectbox("Domain", options=["None"] + class_names,
                                    index=0 if not prop["domain"] else (class_names.index(prop["domain"]) + 1 if prop["domain"] in class_names else 0),
                                    key=f"dp_dom_{prop['name']}")
                            with col2:
                                current_range = prop["range"] if prop["range"] in datatypes else "string"
                                new_range = st.selectbox("Range (Datatype)", options=datatypes,
                                    index=datatypes.index(current_range) if current_range in datatypes else 0,
                                    key=f"dp_rng_{prop['name']}")

                            if st.form_submit_button("Save Changes"):
                                # Handle rename first
                                if new_name and new_name != prop["name"]:
                                    if ont.rename_property(prop["name"], new_name):
                                        current_name = new_name
                                        save_checkpoint("Rename property")
                                        show_message(f"Property renamed to '{new_name}'", "success")
                                    else:
                                        show_message(f"Cannot rename: '{new_name}' already exists!", "error")
                                        st.rerun()
                                else:
                                    current_name = prop["name"]

                                ont.update_property(current_name,
                                    new_label=new_label,
                                    new_comment=new_comment,
                                    new_domain=new_domain if new_domain != "None" else "",
                                    new_range=new_range)
                                save_checkpoint("Update property")
                                st.session_state[f"edit_dataprop_{prop['name']}"] = False
                                show_message(f"Property '{current_name}' updated!", "success")
                                st.rerun()

    with tab3:
        st.subheader("Add Object Property")

        with st.form("add_obj_prop_form"):
            name = st.text_input("Property Name *")
            label = st.text_input("Label")
            comment = st.text_area("Comment")

            col1, col2 = st.columns(2)
            with col1:
                domain = st.selectbox("Domain (Class)", options=["None"] + class_names)
            with col2:
                range_ = st.selectbox("Range (Class)", options=["None"] + class_names)

            st.write("**Property Characteristics:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                functional = st.checkbox("Functional")
                asymmetric = st.checkbox("Asymmetric")
            with col2:
                inverse_functional = st.checkbox("Inverse Functional")
                reflexive = st.checkbox("Reflexive")
            with col3:
                transitive = st.checkbox("Transitive")
                irreflexive = st.checkbox("Irreflexive")
            with col4:
                symmetric = st.checkbox("Symmetric")

            inverse_of = st.selectbox("Inverse Of", options=["None"] + obj_prop_names)

            submitted = st.form_submit_button("Add Object Property")
            if submitted:
                if not name:
                    show_message("Property name is required!", "error")
                elif name in obj_prop_names or name in data_prop_names:
                    show_message(f"Property '{name}' already exists!", "error")
                else:
                    ont.add_object_property(
                        name,
                        domain=domain if domain != "None" else None,
                        range_=range_ if range_ != "None" else None,
                        label=label,
                        comment=comment,
                        functional=functional,
                        inverse_functional=inverse_functional,
                        transitive=transitive,
                        symmetric=symmetric,
                        asymmetric=asymmetric,
                        reflexive=reflexive,
                        irreflexive=irreflexive,
                        inverse_of=inverse_of if inverse_of != "None" else None
                    )
                    save_checkpoint("Add object property")
                    show_message(f"Object property '{name}' added!", "success")
                    st.rerun()

    with tab4:
        st.subheader("Add Data Property")

        with st.form("add_data_prop_form"):
            name = st.text_input("Property Name *", key="data_prop_name")
            label = st.text_input("Label", key="data_prop_label")
            comment = st.text_area("Comment", key="data_prop_comment")

            col1, col2 = st.columns(2)
            with col1:
                domain = st.selectbox("Domain (Class)", options=["None"] + class_names,
                                     key="data_prop_domain")
            with col2:
                datatypes = list(get_ontology_manager_class().XSD_DATATYPES.keys())
                range_ = st.selectbox("Range (Datatype)", options=datatypes,
                                     key="data_prop_range")

            functional = st.checkbox("Functional", key="data_prop_functional")

            submitted = st.form_submit_button("Add Data Property")
            if submitted:
                if not name:
                    show_message("Property name is required!", "error")
                elif name in obj_prop_names or name in data_prop_names:
                    show_message(f"Property '{name}' already exists!", "error")
                else:
                    ont.add_data_property(
                        name,
                        domain=domain if domain != "None" else None,
                        range_=range_,
                        label=label,
                        comment=comment,
                        functional=functional
                    )
                    save_checkpoint("Add data property")
                    show_message(f"Data property '{name}' added!", "success")
                    st.rerun()


def render_individuals():
    """Render the individuals management page."""
    st.header("Individuals")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]
    individuals = ont.get_individuals()
    ind_names = [i["name"] for i in individuals]
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()

    tab1, tab2, tab3 = st.tabs(["View Individuals", "Add Individual", "Add Property Value"])

    with tab1:
        if not individuals:
            st.info("No individuals defined yet.")
        else:
            _active_ind = next((i for i in individuals if st.session_state.get(f"view_ind_{i['name']}", False) or st.session_state.get(f"edit_ind_{i['name']}", False)), None)
            if _active_ind:
                for i in individuals:
                    if i["name"] != _active_ind["name"]:
                        st.session_state.pop(f"view_ind_{i['name']}", None)
                        st.session_state.pop(f"edit_ind_{i['name']}", None)

            for ind in individuals:
                classes_str = ", ".join(ind["classes"]) if ind["classes"] else "No class"
                _ind_expanded = st.session_state.get(f"view_ind_{ind['name']}", False) or st.session_state.get(f"edit_ind_{ind['name']}", False)
                with st.expander(f"👤 **{ind['name']}** ({classes_str})", expanded=_ind_expanded):
                    st.write(f"**URI:** {ind['uri']}")

                    btn_view, btn_edit, btn_del, _ = st.columns([1, 1, 1, 4])
                    with btn_view:
                        if st.button("👁️ View", key=f"btn_view_ind_{ind['name']}", use_container_width=True):
                            st.session_state[f"view_ind_{ind['name']}"] = not st.session_state.get(f"view_ind_{ind['name']}", False)
                            st.session_state[f"edit_ind_{ind['name']}"] = False
                            st.rerun()
                    with btn_edit:
                        if st.button("✏️ Edit", key=f"btn_edit_ind_{ind['name']}", use_container_width=True):
                            st.session_state[f"edit_ind_{ind['name']}"] = not st.session_state.get(f"edit_ind_{ind['name']}", False)
                            st.session_state[f"view_ind_{ind['name']}"] = False
                            st.rerun()
                    with btn_del:
                        if st.button("🗑️ Delete", key=f"btn_del_ind_{ind['name']}", use_container_width=True):
                            st.session_state[f"confirm_delete_ind_{ind['name']}"] = True
                            st.rerun()

                    # View details
                    if st.session_state.get(f"view_ind_{ind['name']}", False):
                        st.divider()
                        st.write(f"**Name:** {ind['name']}")
                        st.write(f"**Label:** {ind['label'] or '—'}")
                        st.write(f"**Comment:** {ind['comment'] or '—'}")
                        st.write(f"**Classes:** {', '.join(ind['classes']) if ind['classes'] else '—'}")
                        if ind["properties"]:
                            st.write("**Property Values:**")
                            for prop in ind["properties"]:
                                st.write(f"  - {prop['property']}: {prop['value']}")
                        else:
                            st.write("**Property Values:** —")
                        if st.button("✏️ Edit", key=f"btn_view_to_edit_ind_{ind['name']}"):
                            st.session_state[f"view_ind_{ind['name']}"] = False
                            st.session_state[f"edit_ind_{ind['name']}"] = True
                            st.rerun()

                    if confirm_delete(ind["name"], "individual", f"ind_{ind['name']}"):
                        ont.delete_individual(ind["name"])
                        save_checkpoint("Delete individual")
                        set_flash_message(f"Individual '{ind['name']}' deleted!", "success")
                        st.rerun()

                    # Resource usages
                    with st.expander("Show Usages", expanded=False):
                        usages = ont.get_resource_usages(ind["name"])
                        if usages["inbound"]:
                            st.markdown("**Referenced by:**")
                            for u in usages["inbound"]:
                                st.write(f"- {u['subject']} *{u['predicate']}*")
                        if usages["outbound"]:
                            st.markdown("**References:**")
                            for u in usages["outbound"]:
                                st.write(f"- *{u['predicate']}* {u['object']}")
                        if not usages["inbound"] and not usages["outbound"]:
                            st.caption("No usages found.")

                    # Inline edit form
                    if st.session_state.get(f"edit_ind_{ind['name']}", False):
                        st.divider()
                        with st.form(f"edit_ind_form_{ind['name']}"):
                            new_name = st.text_input("Name (URI local part)", value=ind["name"], key=f"ind_name_{ind['name']}")
                            new_label = st.text_input("Label", value=ind["label"], key=f"ind_lbl_{ind['name']}")
                            new_comment = st.text_area("Comment", value=ind["comment"], key=f"ind_cmt_{ind['name']}")

                            st.write("**Manage Classes:**")
                            current_classes = ind["classes"]
                            available_classes = [c for c in class_names if c not in current_classes]

                            col1, col2 = st.columns(2)
                            with col1:
                                add_class = st.selectbox("Add to Class",
                                    options=["None"] + available_classes,
                                    key=f"ind_add_cls_{ind['name']}")
                            with col2:
                                remove_class = st.selectbox("Remove from Class",
                                    options=["None"] + current_classes,
                                    key=f"ind_rem_cls_{ind['name']}")

                            if st.form_submit_button("Save Changes"):
                                # Handle rename first
                                if new_name and new_name != ind["name"]:
                                    if ont.rename_individual(ind["name"], new_name):
                                        current_name = new_name
                                        save_checkpoint("Rename individual")
                                        show_message(f"Individual renamed to '{new_name}'", "success")
                                    else:
                                        show_message(f"Cannot rename: '{new_name}' already exists!", "error")
                                        st.rerun()
                                else:
                                    current_name = ind["name"]

                                ont.update_individual(current_name,
                                    new_label=new_label,
                                    new_comment=new_comment,
                                    add_class=add_class if add_class != "None" else None,
                                    remove_class=remove_class if remove_class != "None" else None)
                                save_checkpoint("Update individual")
                                st.session_state[f"edit_ind_{ind['name']}"] = False
                                show_message(f"Individual '{current_name}' updated!", "success")
                                st.rerun()

    with tab2:
        st.subheader("Add Individual")

        if not class_names:
            st.warning("Please create at least one class before adding individuals.")
        else:
            with st.form("add_individual_form"):
                name = st.text_input("Individual Name *")
                label = st.text_input("Label")
                comment = st.text_area("Comment")
                class_type = st.selectbox("Class Type *", options=class_names)

                submitted = st.form_submit_button("Add Individual")
                if submitted:
                    if not name:
                        show_message("Individual name is required!", "error")
                    elif name in ind_names:
                        show_message(f"Individual '{name}' already exists!", "error")
                    else:
                        ont.add_individual(name, class_type, label=label, comment=comment)
                        save_checkpoint("Add individual")
                        show_message(f"Individual '{name}' added!", "success")
                        st.rerun()

    with tab3:
        st.subheader("Add Property Value to Individual")

        if not individuals:
            st.warning("Please create at least one individual first.")
        elif not object_props and not data_props:
            st.warning("Please create at least one property first.")
        else:
            with st.form("add_prop_value_form"):
                individual = st.selectbox("Select Individual", options=ind_names)

                prop_type = st.radio("Property Type", ["Object Property", "Data Property"])

                if prop_type == "Object Property":
                    prop_options = [p["name"] for p in object_props]
                    property_name = st.selectbox("Property", options=prop_options if prop_options else ["No properties"])
                    value = st.selectbox("Value (Individual)", options=ind_names)
                    is_object = True
                else:
                    prop_options = [p["name"] for p in data_props]
                    property_name = st.selectbox("Property", options=prop_options if prop_options else ["No properties"])
                    value = st.text_input("Value")
                    is_object = False

                submitted = st.form_submit_button("Add Property Value")
                if submitted:
                    if not property_name or property_name == "No properties":
                        show_message("Please select a property!", "error")
                    elif not value:
                        show_message("Please provide a value!", "error")
                    else:
                        ont.add_individual_property(individual, property_name, value,
                                                   is_object_property=is_object)
                        save_checkpoint("Add property assertion")
                        show_message(f"Property value added to '{individual}'!", "success")
                        st.rerun()


def render_restrictions():
    """Render the restrictions management page."""
    st.header("Restrictions")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    all_props = [p["name"] for p in object_props] + [p["name"] for p in data_props]
    restrictions = ont.get_restrictions()

    tab1, tab2 = st.tabs(["View Restrictions", "Add Restriction"])

    with tab1:
        if not restrictions:
            st.info("No restrictions defined yet.")
        else:
            for i, rest in enumerate(restrictions):
                with st.expander(f"🔒 {rest['type']} on {rest['property']}"):
                    st.write(f"**Property:** {rest['property']}")
                    st.write(f"**Restriction Type:** {rest['type']}")
                    st.write(f"**Value:** {rest['value']}")
                    if rest["on_class"]:
                        st.write(f"**Qualified on Class:** {rest['on_class']}")
                    st.write(f"**Applied to Classes:** {', '.join(rest['applied_to'])}")

                    if rest['applied_to']:
                        if st.button(f"Delete", key=f"del_rest_{i}"):
                            ont.delete_restriction(rest['applied_to'][0],
                                                  rest['property'],
                                                  rest['type'])
                            save_checkpoint("Delete restriction")
                            show_message("Restriction deleted!", "success")
                            st.rerun()

    with tab2:
        st.subheader("Add Restriction")

        if not class_names:
            st.warning("Please create at least one class first.")
        elif not all_props:
            st.warning("Please create at least one property first.")
        else:
            with st.form("add_restriction_form"):
                target_class = st.selectbox("Apply to Class", options=class_names)
                property_name = st.selectbox("On Property", options=all_props)

                restriction_types = [
                    "someValuesFrom", "allValuesFrom", "hasValue",
                    "minCardinality", "maxCardinality", "exactCardinality",
                    "minQualifiedCardinality", "maxQualifiedCardinality", "qualifiedCardinality"
                ]
                restriction_type = st.selectbox("Restriction Type", options=restriction_types)

                st.write("**Restriction Value:**")
                if restriction_type in ["someValuesFrom", "allValuesFrom"]:
                    value = st.selectbox("Value (Class)", options=class_names, key="rest_class_value")
                elif restriction_type == "hasValue":
                    value_type = st.radio("Value Type", ["Literal", "Individual"])
                    if value_type == "Literal":
                        value = st.text_input("Literal Value")
                    else:
                        ind_names = [i["name"] for i in ont.get_individuals()]
                        value = st.selectbox("Individual", options=ind_names if ind_names else ["No individuals"])
                else:
                    value = st.number_input("Cardinality", min_value=0, value=1)

                on_class = None
                if "Qualified" in restriction_type:
                    on_class = st.selectbox("Qualified on Class", options=class_names,
                                           key="qualified_class")

                submitted = st.form_submit_button("Add Restriction")
                if submitted:
                    try:
                        ont.add_restriction(target_class, property_name, restriction_type,
                                          value, on_class=on_class)
                        save_checkpoint("Add restriction")
                        show_message("Restriction added!", "success")
                        st.rerun()
                    except Exception as e:
                        show_message(f"Error adding restriction: {str(e)}", "error")


def render_relations():
    """Render the relations management page."""
    st.header("Relations")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    all_prop_names = [p["name"] for p in object_props] + [p["name"] for p in data_props]
    individuals = ont.get_individuals()
    ind_names = [i["name"] for i in individuals]

    tab1, tab2, tab3, tab4 = st.tabs([
        "View Relations", "Class Relations", "Property Relations", "Individual Relations"
    ])

    with tab1:
        st.subheader("All Relations")

        # Class relations
        class_relations = ont.get_class_relations()
        if class_relations:
            st.write("**Class Relations:**")
            for rel in class_relations:
                col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                with col1:
                    st.write(f"📦 {rel['subject']}")
                with col2:
                    st.write(f"➡️ {rel['relation']}")
                with col3:
                    st.write(f"📦 {rel['object']}")
                with col4:
                    if st.button("🗑️", key=f"del_crel_{rel['subject']}_{rel['relation']}_{rel['object']}"):
                        ont.remove_class_relation(rel['subject'], rel['relation'], rel['object'])
                        save_checkpoint("Delete class relation")
                        show_message("Relation deleted!", "success")
                        st.rerun()
        else:
            st.info("No class relations defined.")

        st.divider()

        # Property relations
        prop_relations = ont.get_property_relations()
        if prop_relations:
            st.write("**Property Relations:**")
            for rel in prop_relations:
                col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                with col1:
                    st.write(f"🔗 {rel['subject']}")
                with col2:
                    st.write(f"➡️ {rel['relation']}")
                with col3:
                    st.write(f"🔗 {rel['object']}")
                with col4:
                    if st.button("🗑️", key=f"del_prel_{rel['subject']}_{rel['relation']}_{rel['object']}"):
                        ont.remove_property_relation(rel['subject'], rel['relation'], rel['object'])
                        save_checkpoint("Delete property relation")
                        show_message("Relation deleted!", "success")
                        st.rerun()
        else:
            st.info("No property relations defined.")

        st.divider()

        # Individual relations
        ind_relations = ont.get_individual_relations()
        if ind_relations:
            st.write("**Individual Relations:**")
            for rel in ind_relations:
                col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                with col1:
                    st.write(f"👤 {rel['subject']}")
                with col2:
                    st.write(f"➡️ {rel['relation']}")
                with col3:
                    st.write(f"👤 {rel['object']}")
                with col4:
                    if st.button("🗑️", key=f"del_irel_{rel['subject']}_{rel['relation']}_{rel['object']}"):
                        ont.remove_individual_relation(rel['subject'], rel['relation'], rel['object'])
                        save_checkpoint("Delete individual relation")
                        show_message("Relation deleted!", "success")
                        st.rerun()
        else:
            st.info("No individual relations defined.")

    with tab2:
        st.subheader("Add Class Relation")

        if len(class_names) < 2:
            st.warning("Need at least 2 classes to create relations.")
        else:
            with st.form("add_class_relation_form"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    class1 = st.selectbox("Class 1", options=class_names, key="crel_class1")
                with col2:
                    relation_type = st.selectbox("Relation Type", options=[
                        "subClassOf",
                        "equivalentClass",
                        "disjointWith"
                    ], key="crel_type")
                with col3:
                    class2 = st.selectbox("Class 2", options=class_names, key="crel_class2")

                st.caption("""
                - **subClassOf**: Class 1 is a subclass of Class 2
                - **equivalentClass**: Class 1 and Class 2 have the same instances
                - **disjointWith**: Class 1 and Class 2 have no common instances
                """)

                submitted = st.form_submit_button("Add Class Relation")
                if submitted:
                    if class1 == class2:
                        show_message("Please select two different classes!", "error")
                    else:
                        ont.add_class_relation(class1, relation_type, class2)
                        save_checkpoint("Add class relation")
                        show_message(f"Relation added: {class1} {relation_type} {class2}", "success")
                        st.rerun()

    with tab3:
        st.subheader("Add Property Relation")

        if len(all_prop_names) < 2:
            st.warning("Need at least 2 properties to create relations.")
        else:
            with st.form("add_property_relation_form"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    prop1 = st.selectbox("Property 1", options=all_prop_names, key="prel_prop1")
                with col2:
                    relation_type = st.selectbox("Relation Type", options=[
                        "subPropertyOf",
                        "equivalentProperty",
                        "inverseOf"
                    ], key="prel_type")
                with col3:
                    prop2 = st.selectbox("Property 2", options=all_prop_names, key="prel_prop2")

                st.caption("""
                - **subPropertyOf**: Property 1 is a sub-property of Property 2
                - **equivalentProperty**: Property 1 and Property 2 have the same meaning
                - **inverseOf**: Property 1 is the inverse of Property 2 (e.g., hasParent / hasChild)
                """)

                submitted = st.form_submit_button("Add Property Relation")
                if submitted:
                    if prop1 == prop2:
                        show_message("Please select two different properties!", "error")
                    else:
                        ont.add_property_relation(prop1, relation_type, prop2)
                        save_checkpoint("Add property relation")
                        show_message(f"Relation added: {prop1} {relation_type} {prop2}", "success")
                        st.rerun()

    with tab4:
        st.subheader("Add Individual Relation")

        if len(ind_names) < 2:
            st.warning("Need at least 2 individuals to create relations.")
        else:
            with st.form("add_individual_relation_form"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    ind1 = st.selectbox("Individual 1", options=ind_names, key="irel_ind1")
                with col2:
                    relation_type = st.selectbox("Relation Type", options=[
                        "sameAs",
                        "differentFrom"
                    ], key="irel_type")
                with col3:
                    ind2 = st.selectbox("Individual 2", options=ind_names, key="irel_ind2")

                st.caption("""
                - **sameAs**: Individual 1 and Individual 2 refer to the same entity
                - **differentFrom**: Individual 1 and Individual 2 are definitely different entities
                """)

                submitted = st.form_submit_button("Add Individual Relation")
                if submitted:
                    if ind1 == ind2:
                        show_message("Please select two different individuals!", "error")
                    else:
                        ont.add_individual_relation(ind1, relation_type, ind2)
                        save_checkpoint("Add individual relation")
                        show_message(f"Relation added: {ind1} {relation_type} {ind2}", "success")
                        st.rerun()


def render_annotations():
    """Render the annotations management page."""
    st.header("Annotations")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    individuals = ont.get_individuals()

    # Build resources with labels for display: "Label (name)" format
    def format_resource(name, label, res_type):
        if label and label != name:
            return f"{label} ({name})"
        return name

    # Combine all resources with their labels
    all_resources = []
    for c in classes:
        display = format_resource(c["name"], c.get("label"), "Class")
        all_resources.append({"name": c["name"], "label": c.get("label"), "type": "Class", "display": display})
    for p in object_props:
        display = format_resource(p["name"], p.get("label"), "Object Property")
        all_resources.append({"name": p["name"], "label": p.get("label"), "type": "Object Property", "display": display})
    for p in data_props:
        display = format_resource(p["name"], p.get("label"), "Data Property")
        all_resources.append({"name": p["name"], "label": p.get("label"), "type": "Data Property", "display": display})
    for i in individuals:
        display = format_resource(i["name"], i.get("label"), "Individual")
        all_resources.append({"name": i["name"], "label": i.get("label"), "type": "Individual", "display": display})

    # Sort all resources by display text
    all_resources.sort(key=lambda r: r["display"].lower())

    tab1, tab2 = st.tabs(["View Annotations", "Add Annotation"])

    with tab1:
        if not all_resources:
            st.info("No resources to annotate. Create classes, properties, or individuals first.")
        else:
            # Filter by resource type
            col1, col2 = st.columns([1, 3])
            with col1:
                filter_types = ["All"] + list(set(r["type"] for r in all_resources))
                selected_type = st.selectbox("Filter by Type", options=filter_types, key="filter_type")

            # Filter resources based on selection
            if selected_type == "All":
                filtered_resources = all_resources
            else:
                filtered_resources = [r for r in all_resources if r["type"] == selected_type]

            with col2:
                if filtered_resources:
                    selected = st.selectbox(
                        "Select Resource",
                        options=[r["display"] for r in filtered_resources],
                        key="view_annotations_select"
                    )
                else:
                    selected = None
                    st.info(f"No {selected_type} resources found.")

            if selected:
                # Find the actual resource name from display string
                resource = next((r for r in filtered_resources if r["display"] == selected), None)
                if resource:
                    resource_name = resource["name"]
                    annotations = ont.get_annotations(resource_name)

                    if not annotations:
                        st.info(f"No annotations found for '{resource_name}'")
                    else:
                        st.subheader(f"Annotations for {selected}")
                        for ann in annotations:
                            col1, col2, col3 = st.columns([2, 4, 1])
                            with col1:
                                # Show prefixed predicate (e.g., rdfs:label, skos:prefLabel)
                                predicate_display = ann.get('predicate_prefixed', ann['predicate'])
                                st.write(f"**{predicate_display}**")
                            with col2:
                                lang_str = f" @{ann['language']}" if ann.get('language') else ""
                                dtype_str = f" ({ann['datatype']})" if ann.get('datatype') else ""
                                st.write(f"{ann['value']}{lang_str}{dtype_str}")
                            with col3:
                                if st.button("🗑️", key=f"del_ann_{resource_name}_{ann['predicate']}_{hash(ann['value'])}"):
                                    ont.delete_annotation(
                                        resource_name, ann['predicate'], ann['value'],
                                        lang=ann.get('language'), datatype=ann.get('datatype')
                                    )
                                    save_checkpoint("Delete annotation")
                                    show_message("Annotation deleted!", "success")
                                    st.rerun()

    with tab2:
        st.subheader("Add Annotation")

        if not all_resources:
            st.warning("Please create at least one resource first.")
        else:
            # Get predicates used in the ontology
            used_predicates = ont.get_used_annotation_predicates()

            # Build predicate options: standard ones + used from ontology
            standard_predicates = [
                {"local_name": "label", "uri": "label", "prefix": "rdfs"},
                {"local_name": "comment", "uri": "comment", "prefix": "rdfs"},
                {"local_name": "seeAlso", "uri": "seeAlso", "prefix": "rdfs"},
                {"local_name": "isDefinedBy", "uri": "isDefinedBy", "prefix": "rdfs"},
                {"local_name": "prefLabel", "uri": "prefLabel", "prefix": "skos"},
                {"local_name": "altLabel", "uri": "altLabel", "prefix": "skos"},
                {"local_name": "definition", "uri": "definition", "prefix": "skos"},
                {"local_name": "example", "uri": "example", "prefix": "skos"},
                {"local_name": "note", "uri": "note", "prefix": "skos"},
                {"local_name": "title", "uri": "title", "prefix": "dcterms"},
                {"local_name": "description", "uri": "description", "prefix": "dcterms"},
                {"local_name": "creator", "uri": "creator", "prefix": "dcterms"},
                {"local_name": "contributor", "uri": "contributor", "prefix": "dcterms"},
                {"local_name": "date", "uri": "date", "prefix": "dcterms"},
                {"local_name": "deprecated", "uri": "deprecated", "prefix": "owl"},
            ]

            # Combine and deduplicate (used predicates take priority as they have full URIs)
            predicate_options = []
            predicate_lookup = {}  # display -> uri

            # Add used predicates first (from ontology)
            seen_names = set()
            for p in used_predicates:
                display = f"{p['prefix']}:{p['local_name']}" if p['prefix'] else p['local_name']
                if display not in seen_names:
                    predicate_options.append(display)
                    predicate_lookup[display] = p['uri']
                    seen_names.add(display)
                    seen_names.add(p['local_name'])  # Also mark local name as seen

            # Add standard predicates that aren't already included
            for p in standard_predicates:
                display = f"{p['prefix']}:{p['local_name']}"
                if p['local_name'] not in seen_names and display not in seen_names:
                    predicate_options.append(display)
                    predicate_lookup[display] = p['uri']  # Use short name for standard ones

            # Sort options
            predicate_options.sort(key=lambda x: x.lower())

            with st.form("add_annotation_form"):
                # Use display format with label
                resource_options = [f"{r['display']} [{r['type']}]" for r in all_resources]
                selected = st.selectbox("Select Resource", options=resource_options)

                predicate_display = st.selectbox("Annotation Type", options=predicate_options)

                value = st.text_area("Value")

                language = st.text_input("Language Tag (optional)", placeholder="en, de, fr...")

                submitted = st.form_submit_button("Add Annotation")
                if submitted:
                    if not value:
                        show_message("Value is required!", "error")
                    else:
                        # Find the resource by matching the option string
                        idx = resource_options.index(selected)
                        resource_name = all_resources[idx]["name"]
                        predicate_uri = predicate_lookup.get(predicate_display, predicate_display)
                        ont.add_annotation(resource_name, predicate_uri, value,
                                         lang=language if language else None)
                        save_checkpoint("Add annotation")
                        show_message("Annotation added!", "success")
                        st.rerun()


def render_import_export():
    """Render the import/export page."""
    st.header("Import / Export")

    # Display any flash messages from previous actions
    display_flash_message()

    ont = st.session_state.ontology

    tab1, tab2, tab3 = st.tabs(["Import", "Export", "New Ontology"])

    with tab1:
        st.subheader("Import Ontology")

        # Initialize import preview state
        if "import_preview" not in st.session_state:
            st.session_state.import_preview = None
        if "import_content" not in st.session_state:
            st.session_state.import_content = None
        if "import_format" not in st.session_state:
            st.session_state.import_format = None

        # Step 1: Source selection (only when no preview active)
        if st.session_state.import_preview is None:
            import_method = st.radio("Import Method", ["Upload File", "Paste Content"])

            if import_method == "Upload File":
                uploaded_file = st.file_uploader(
                    "Choose an ontology file",
                    type=["ttl", "owl", "rdf", "xml", "n3", "nt", "jsonld", "json"],
                    help="Supported formats: Turtle (.ttl), RDF/XML (.owl, .rdf, .xml), N3 (.n3), N-Triples (.nt), JSON-LD (.jsonld, .json)"
                )

                if uploaded_file:
                    format_map = {
                        "ttl": "turtle",
                        "owl": "xml",
                        "rdf": "xml",
                        "xml": "xml",
                        "n3": "n3",
                        "nt": "nt",
                        "jsonld": "json-ld",
                        "json": "json-ld",
                    }
                    ext = uploaded_file.name.split(".")[-1].lower()
                    format_ = format_map.get(ext, "turtle")

                    if st.button("Preview Import"):
                        try:
                            content = uploaded_file.read().decode("utf-8")
                            preview = ont.preview_import(content, format=format_)
                            st.session_state.import_preview = preview
                            st.session_state.import_content = content
                            st.session_state.import_format = format_
                            st.rerun()
                        except Exception as e:
                            show_message(f"Error parsing file: {str(e)}", "error")

            else:
                content = st.text_area("Paste Ontology Content", height=300)
                format_ = st.selectbox("Format", ["turtle", "xml", "n3", "nt", "json-ld"])

                if st.button("Preview Import"):
                    if not content:
                        show_message("Please paste ontology content!", "error")
                    else:
                        try:
                            preview = ont.preview_import(content, format=format_)
                            st.session_state.import_preview = preview
                            st.session_state.import_content = content
                            st.session_state.import_format = format_
                            st.rerun()
                        except Exception as e:
                            show_message(f"Error parsing content: {str(e)}", "error")

        # Step 2: Review panel
        else:
            preview = st.session_state.import_preview
            diff = preview["diff"]
            diff_stats = diff["stats"]

            st.info("Review the import changes below, then choose an import mode and apply.")

            # Import mode selector
            from ontology_manager import IMPORT_REPLACE, IMPORT_MERGE, IMPORT_MERGE_OVERWRITE
            strategy = st.radio(
                "Import Mode",
                ["Replace", "Merge", "Merge (Overwrite)"],
                captions=[
                    "Replace current ontology with imported content",
                    "Add imported content to current ontology (keep both)",
                    "Add imported content, overwrite conflicts with imported values",
                ],
                key="import_strategy_radio",
            )
            strategy_map = {
                "Replace": IMPORT_REPLACE,
                "Merge": IMPORT_MERGE,
                "Merge (Overwrite)": IMPORT_MERGE_OVERWRITE,
            }
            selected_strategy = strategy_map[strategy]

            # Statistics comparison
            st.subheader("Statistics Comparison")
            current_stats = ont.get_statistics()
            incoming_stats = preview["incoming_stats"]

            col_cur, col_inc = st.columns(2)
            with col_cur:
                st.caption("Current Ontology")
                st.metric("Classes", current_stats["classes"])
                st.metric("Object Properties", current_stats["object_properties"])
                st.metric("Data Properties", current_stats["data_properties"])
                st.metric("Individuals", current_stats["individuals"])
                st.metric("Total Triples", current_stats["total_triples"])
            with col_inc:
                st.caption("Incoming Content")
                st.metric("Classes", incoming_stats["classes"])
                st.metric("Object Properties", incoming_stats["object_properties"])
                st.metric("Data Properties", incoming_stats["data_properties"])
                st.metric("Individuals", incoming_stats["individuals"])
                st.metric("Total Triples", incoming_stats["total_triples"])

            # Diff summary
            with st.expander(
                f"Changes: {diff_stats['added']} triples added, "
                f"{diff_stats['removed']} removed, "
                f"{diff_stats['resources_modified']} resources modified",
                expanded=True,
            ):
                if diff["summary"]:
                    for line in diff["summary"]:
                        # Color-code by change type
                        if line.startswith("Added"):
                            st.markdown(f":green[{line}]")
                        elif line.startswith("Removed"):
                            st.markdown(f":red[{line}]")
                        elif line.startswith("Modified"):
                            st.markdown(f":orange[{line}]")
                        else:
                            st.write(line)
                else:
                    st.write("No changes detected.")

            # Conflicts (for merge modes)
            if selected_strategy != IMPORT_REPLACE:
                conflicts = preview.get("conflicts", [])
                if conflicts:
                    st.warning(f"{len(conflicts)} conflict(s) detected")
                    conflict_data = {
                        "Subject": [c["subject"] for c in conflicts],
                        "Predicate": [c["predicate"] for c in conflicts],
                        "Current Value": [", ".join(c["current_values"]) for c in conflicts],
                        "Incoming Value": [c["incoming_value"] for c in conflicts],
                    }
                    st.dataframe(conflict_data, width="stretch", hide_index=True)

            # Prefix conflicts
            prefix_conflicts = preview.get("prefix_conflicts", [])
            if prefix_conflicts:
                with st.expander(f"Prefix Changes ({len(prefix_conflicts)} conflicts)"):
                    pfx_data = {
                        "Prefix": [c["prefix"] for c in prefix_conflicts],
                        "Current Namespace": [c["current_namespace"] for c in prefix_conflicts],
                        "Incoming Namespace": [c["incoming_namespace"] for c in prefix_conflicts],
                    }
                    st.dataframe(pfx_data, width="stretch", hide_index=True)

            # Change report download
            report = ont.format_diff_report(diff, report_format="markdown")
            st.download_button(
                "Download Change Report",
                data=report,
                file_name="change_report.md",
                mime="text/markdown",
            )

            # Step 3: Apply / Cancel
            col_apply, col_cancel = st.columns(2)
            with col_apply:
                if st.button("Apply Import", type="primary", use_container_width=True):
                    try:
                        content = st.session_state.import_content
                        format_ = st.session_state.import_format
                        if selected_strategy == IMPORT_REPLACE:
                            ont.load_from_string(content, format=format_)
                        else:
                            result = ont.merge_from_string(
                                content, format=format_, strategy=selected_strategy
                            )
                        st.session_state.ontology = ont
                        save_checkpoint("Import ontology")
                        # Clear preview state
                        st.session_state.import_preview = None
                        st.session_state.import_content = None
                        st.session_state.import_format = None
                        triples = len(ont.graph)
                        set_flash_message(
                            f"Ontology imported successfully! ({triples} triples)",
                            "success",
                        )
                        st.rerun()
                    except Exception as e:
                        show_message(f"Error applying import: {str(e)}", "error")
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.import_preview = None
                    st.session_state.import_content = None
                    st.session_state.import_format = None
                    st.rerun()

    with tab2:
        st.subheader("Export Ontology")

        format_options = {
            "Turtle (.ttl)": "turtle",
            "RDF/XML (.owl)": "xml",
            "N-Triples (.nt)": "nt",
            "N3 (.n3)": "n3",
            "JSON-LD (.jsonld)": "json-ld"
        }

        selected_format = st.selectbox("Export Format", options=list(format_options.keys()))
        format_ = format_options[selected_format]

        file_extensions = {
            "turtle": "ttl",
            "xml": "owl",
            "nt": "nt",
            "n3": "n3",
            "json-ld": "jsonld"
        }

        if st.button("Generate Export"):
            try:
                content = ont.export_to_string(format=format_)
                st.text_area("Exported Content", value=content, height=400)

                ext = file_extensions[format_]
                st.download_button(
                    label=f"Download .{ext} file",
                    data=content,
                    file_name=f"ontology.{ext}",
                    mime="text/plain"
                )
            except Exception as e:
                show_message(f"Error exporting ontology: {str(e)}", "error")

    with tab3:
        st.subheader("Create New Ontology")

        st.warning("This will clear the current ontology. Make sure to export first if needed.")

        with st.form("new_ontology_form"):
            base_uri = st.text_input("Base URI *",
                                    value="http://example.org/ontology#",
                                    help="The base namespace URI for your ontology")
            label = st.text_input("Label (rdfs:label)")
            comment = st.text_area("Comment (rdfs:comment)")
            creator = st.text_input("Creator")

            submitted = st.form_submit_button("Create New Ontology")
            if submitted:
                if not base_uri:
                    show_message("Base URI is required!", "error")
                else:
                    st.session_state.ontology = get_ontology_manager_class()(base_uri=base_uri)
                    st.session_state.ontology.set_ontology_metadata(
                        label=label, comment=comment,
                        creator=creator
                    )
                    from ontology_manager import UndoManager
                    st.session_state.undo_manager = UndoManager(st.session_state.ontology)
                    show_message("New ontology created!", "success")
                    st.rerun()


def render_advanced():
    """Render the advanced OWL features page."""
    st.header("Advanced OWL Features")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    class_names = [c["name"] for c in classes]
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    all_prop_names = [p["name"] for p in object_props] + [p["name"] for p in data_props]
    individuals = ont.get_individuals()
    ind_names = [i["name"] for i in individuals]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Class Expressions", "Property Chains", "Disjoint Union", "All Different", "Has Key"
    ])

    with tab1:
        st.subheader("Class Expressions")
        st.caption("Define complex class expressions using set operations")

        # View existing expressions
        expressions = ont.get_class_expressions()
        if expressions:
            st.write("**Existing Expressions:**")
            for expr in expressions:
                st.write(f"- **{expr['class']}** {expr['type']}: {', '.join(expr['members'])}")
        else:
            st.info("No class expressions defined yet.")

        st.divider()

        if len(class_names) < 2:
            st.warning("Need at least 2 classes to create expressions.")
        else:
            with st.form("add_class_expression_form"):
                target_class = st.selectbox("Target Class", options=class_names,
                    help="The class to define with this expression")

                expr_type = st.selectbox("Expression Type", options=[
                    "unionOf", "intersectionOf", "complementOf", "oneOf"
                ])

                st.write("**Select members:**")
                if expr_type == "complementOf":
                    complement_class = st.selectbox("Complement of Class", options=class_names)
                    selected_classes = [complement_class] if complement_class else []
                    selected_individuals = []
                elif expr_type == "oneOf":
                    selected_individuals = st.multiselect("Individuals (enumeration)",
                        options=ind_names)
                    selected_classes = []
                else:
                    selected_classes = st.multiselect("Classes", options=class_names)
                    selected_individuals = []

                submitted = st.form_submit_button("Add Expression")
                if submitted:
                    if expr_type == "oneOf" and selected_individuals:
                        ont.add_class_expression(target_class, expr_type,
                            individuals=selected_individuals)
                        save_checkpoint("Add class expression")
                        show_message(f"Expression added to {target_class}", "success")
                        st.rerun()
                    elif selected_classes:
                        ont.add_class_expression(target_class, expr_type,
                            classes=selected_classes)
                        save_checkpoint("Add class expression")
                        show_message(f"Expression added to {target_class}", "success")
                        st.rerun()
                    else:
                        show_message("Please select at least one member!", "error")

    with tab2:
        st.subheader("Property Chains")
        st.caption("Define property chain axioms (e.g., hasParent o hasBrother = hasUncle)")

        # View existing chains
        chains = ont.get_property_chains()
        if chains:
            st.write("**Existing Property Chains:**")
            for chain in chains:
                st.write(f"- **{chain['property']}** = {' o '.join(chain['chain'])}")
        else:
            st.info("No property chains defined yet.")

        st.divider()

        obj_prop_names = [p["name"] for p in object_props]
        if len(obj_prop_names) < 2:
            st.warning("Need at least 2 object properties to create chains.")
        else:
            with st.form("add_property_chain_form"):
                result_prop = st.selectbox("Result Property",
                    options=obj_prop_names,
                    help="The property that results from following the chain")

                chain_props = st.multiselect("Chain Properties (in order)",
                    options=obj_prop_names,
                    help="Select properties in the order they should be followed")

                submitted = st.form_submit_button("Add Property Chain")
                if submitted:
                    if len(chain_props) < 2:
                        show_message("Chain must have at least 2 properties!", "error")
                    else:
                        ont.add_property_chain(result_prop, chain_props)
                        show_message(f"Property chain added for {result_prop}", "success")
                        st.rerun()

    with tab3:
        st.subheader("Disjoint Union")
        st.caption("Define a class as the disjoint union of other classes")

        # View existing disjoint unions
        unions = ont.get_disjoint_unions()
        if unions:
            st.write("**Existing Disjoint Unions:**")
            for union in unions:
                st.write(f"- **{union['class']}** = disjointUnionOf({', '.join(union['members'])})")
        else:
            st.info("No disjoint unions defined yet.")

        st.divider()

        if len(class_names) < 3:
            st.warning("Need at least 3 classes (1 parent + 2 children) for disjoint union.")
        else:
            with st.form("add_disjoint_union_form"):
                parent_class = st.selectbox("Parent Class",
                    options=class_names,
                    help="The class that is the disjoint union")

                member_classes = st.multiselect("Member Classes",
                    options=class_names,
                    help="Classes that make up the disjoint union")

                submitted = st.form_submit_button("Add Disjoint Union")
                if submitted:
                    if len(member_classes) < 2:
                        show_message("Need at least 2 member classes!", "error")
                    elif parent_class in member_classes:
                        show_message("Parent class cannot be a member!", "error")
                    else:
                        ont.add_disjoint_union(parent_class, member_classes)
                        show_message(f"Disjoint union added for {parent_class}", "success")
                        st.rerun()

    with tab4:
        st.subheader("All Different")
        st.caption("Declare that a set of individuals are all mutually different")

        # View existing AllDifferent declarations
        all_diffs = ont.get_all_different()
        if all_diffs:
            st.write("**Existing AllDifferent Declarations:**")
            for i, diff in enumerate(all_diffs):
                st.write(f"- AllDifferent: {', '.join(diff)}")
        else:
            st.info("No AllDifferent declarations yet.")

        st.divider()

        if len(ind_names) < 2:
            st.warning("Need at least 2 individuals for AllDifferent.")
        else:
            with st.form("add_all_different_form"):
                selected_inds = st.multiselect("Select Individuals",
                    options=ind_names,
                    help="All selected individuals will be declared mutually different")

                submitted = st.form_submit_button("Add AllDifferent")
                if submitted:
                    if len(selected_inds) < 2:
                        show_message("Select at least 2 individuals!", "error")
                    else:
                        ont.add_all_different(selected_inds)
                        show_message("AllDifferent declaration added!", "success")
                        st.rerun()

    with tab5:
        st.subheader("Has Key")
        st.caption("Define key properties that uniquely identify instances of a class")

        # View existing hasKey declarations
        keys = ont.get_has_keys()
        if keys:
            st.write("**Existing hasKey Declarations:**")
            for key in keys:
                st.write(f"- **{key['class']}** hasKey: {', '.join(key['properties'])}")
        else:
            st.info("No hasKey declarations yet.")

        st.divider()

        if not class_names:
            st.warning("Need at least 1 class.")
        elif not all_prop_names:
            st.warning("Need at least 1 property.")
        else:
            with st.form("add_has_key_form"):
                target_class = st.selectbox("Class", options=class_names)

                key_props = st.multiselect("Key Properties",
                    options=all_prop_names,
                    help="Properties that together uniquely identify instances")

                submitted = st.form_submit_button("Add hasKey")
                if submitted:
                    if not key_props:
                        show_message("Select at least 1 property!", "error")
                    else:
                        ont.add_has_key(target_class, key_props)
                        show_message(f"hasKey added for {target_class}", "success")
                        st.rerun()


def render_validation():
    """Render the validation and reasoning page."""
    st.header("Validation & Reasoning")

    ont = st.session_state.ontology

    tab1, tab2 = st.tabs(["Validation", "Reasoning"])

    with tab1:
        st.subheader("Ontology Validation")

        if st.button("Run Validation"):
            issues = ont.validate()

            if not issues:
                show_message("No issues found! The ontology looks good.", "success")
            else:
                st.write(f"Found {len(issues)} issue(s):")

                # Group by severity
                errors = [i for i in issues if i["severity"] == "error"]
                warnings = [i for i in issues if i["severity"] == "warning"]
                infos = [i for i in issues if i["severity"] == "info"]

                if errors:
                    st.error(f"**Errors ({len(errors)}):**")
                    for issue in errors:
                        st.write(f"  - {issue['message']}")

                if warnings:
                    st.warning(f"**Warnings ({len(warnings)}):**")
                    for issue in warnings:
                        st.write(f"  - {issue['message']}")

                if infos:
                    st.info(f"**Information ({len(infos)}):**")
                    for issue in infos:
                        st.write(f"  - {issue['message']}")

    with tab2:
        st.subheader("Apply Reasoning")

        st.write("""
        Reasoning can infer new triples based on the ontology structure.
        This uses OWL-RL (Rule Language) reasoning.
        """)

        profile = st.selectbox("Reasoning Profile", [
            ("RDFS", "rdfs"),
            ("OWL-RL", "owl-rl"),
            ("OWL-RL Extended", "owl-rl-ext")
        ], format_func=lambda x: x[0])

        current_triples = len(ont.graph)
        st.write(f"Current triple count: {current_triples}")

        if st.button("Apply Reasoning"):
            try:
                new_triples = ont.apply_reasoning(profile=profile[1])
                save_checkpoint("Apply reasoning")
                show_message(f"Reasoning complete! {new_triples} new triples inferred.", "success")
                st.write(f"New triple count: {len(ont.graph)}")
            except Exception as e:
                show_message(f"Error during reasoning: {str(e)}", "error")


def render_visualization():
    """Render the visualization page."""
    st.header("Visualization")

    ont = st.session_state.ontology
    classes = ont.get_classes()
    object_props = ont.get_object_properties()
    data_props = ont.get_data_properties()
    individuals = ont.get_individuals()

    stats = ont.get_statistics()

    if stats["content_triples"] == 0:
        st.info("No content to visualize. Add classes, properties, or individuals first.")
        return

    tab1, tab2, tab3 = st.tabs(["Interactive Graph", "Class Hierarchy", "Statistics"])

    with tab1:
        st.subheader("Interactive Ontology Graph")

        # Graph options - row 1: what to show
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            show_classes = st.checkbox("Classes", value=True)
        with col2:
            show_properties = st.checkbox("Obj Props", value=True)
        with col3:
            show_data_props = st.checkbox("Data Props", value=False)
        with col4:
            show_annotations = st.checkbox("Annotations", value=False)
        with col5:
            show_individuals = st.checkbox("Individuals", value=False)

        # Graph options - row 2: layout controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            height = st.slider("Graph Height", 400, 1200, 700, step=100)
        with col2:
            node_spacing = st.slider(
                "Node Spacing",
                50, 300, 150,
                help="Distance between nodes. Increase for less overlap."
            )
        with col3:
            render_graph = st.button("Render Graph", type="primary", use_container_width=True)

        # Validation highlighting option
        highlight_issues = st.checkbox("Highlight validation issues", value=False)
        validation_subjects = set()
        if highlight_issues:
            issues = ont.validate()
            validation_subjects = {i["subject"] for i in issues}

        # Class filter
        all_class_names = [c["name"] for c in classes] if classes else []
        with st.expander("Filter Classes", expanded=False):
            selected_classes = st.multiselect(
                "Select classes to display",
                options=all_class_names,
                default=all_class_names,
                help="Choose which classes to show in the graph"
            )

        # Store graph settings in session state for caching
        selected_classes_key = "_".join(sorted(selected_classes)) if selected_classes else "none"
        _graph_ver = 11  # Bump to invalidate cached graph data after code changes
        graph_key = f"v{_graph_ver}_{show_classes}_{show_properties}_{show_data_props}_{show_annotations}_{show_individuals}_{height}_{node_spacing}_{highlight_issues}_{hash(selected_classes_key)}"
        if "last_graph_key" not in st.session_state:
            st.session_state.last_graph_key = None
            st.session_state.last_graph_data = None

        # Rebuild graph data when settings change or button clicked
        needs_rebuild = st.session_state.last_graph_key != graph_key or render_graph or st.session_state.last_graph_data is None

        if needs_rebuild:
            # Build the graph
            from pyvis.network import Network
            import tempfile
            import os

            status = st.empty()
            status.info("Building graph...")

            net = Network(height=f"{height - 32}px", width="100%", bgcolor="#ffffff",
                         font_color="#f0f0f0", directed=True)

            # Fast layout - disable stabilization completely to avoid hanging
            net.set_options(f'''
            var options = {{
                "physics": {{
                    "enabled": true,
                    "barnesHut": {{
                        "gravitationalConstant": -5000,
                        "centralGravity": 0.3,
                        "springLength": {node_spacing},
                        "springConstant": 0.04,
                        "avoidOverlap": 0.3
                    }},
                    "stabilization": {{
                        "enabled": false
                    }}
                }},
                "nodes": {{
                    "font": {{
                        "color": "#f0f0f0",
                        "size": 12
                    }}
                }},
                "edges": {{
                    "font": {{
                        "color": "#cccccc",
                        "size": 10,
                        "strokeWidth": 2,
                        "strokeColor": "#ffffff"
                    }},
                    "smooth": {{
                        "enabled": true,
                        "type": "curvedCW",
                        "roundness": 0.2
                    }}
                }}
            }}
            ''')

            # Limit total nodes to prevent browser hanging
            max_nodes = 500
            node_count = 0

            # Build set of class names for edge validation (only selected classes)
            class_names = set(selected_classes) if selected_classes else set()

            # Add classes as nodes (only selected classes)
            if show_classes and selected_classes:
                for cls in classes:
                    if node_count >= max_nodes:
                        break
                    if cls["name"] not in selected_classes:
                        continue
                    label = cls["label"] if cls["label"] else cls["name"]
                    title = f"Class: {cls['name']}"
                    if cls["label"]:
                        title += f"\nLabel: {cls['label']}"
                    if cls["comment"]:
                        title += f"\nComment: {cls['comment'][:100]}"

                    has_issue = cls["name"] in validation_subjects
                    node_color = ({"background": "#4CAF50", "border": "#F44336", "highlight": {"border": "#F44336"}}
                                  if has_issue
                                  else {"background": "#4CAF50", "border": "#388E3C"})
                    border_width = 3 if has_issue else 1
                    if has_issue:
                        title += "\n⚠ Has validation issues"
                    net.add_node(cls["name"], label=label, title=title,
                               color=node_color, borderWidth=border_width,
                               shape="box", size=25,
                               ntype="Class", ename=cls["name"])
                    node_count += 1

                # Add class hierarchy edges (only if parent node exists in graph)
                for cls in classes:
                    for parent in cls["parents"]:
                        if parent in class_names:
                            net.add_edge(cls["name"], parent, label="subClassOf",
                                       title=f"Subclass relation:\n{cls['name']} is a subclass of {parent}",
                                       color="#81C784", arrows="to")

            # Add object properties as labeled edges between domain and range
            if show_properties and object_props and show_classes:
                for prop in object_props:
                    # Only show if both domain and range exist as class nodes
                    if prop["domain"] and prop["range"] and prop["domain"] in class_names and prop["range"] in class_names:
                        label = prop["label"] if prop["label"] else prop["name"]
                        title = f"Object Property: {prop['name']}"
                        if prop["label"]:
                            title += f"\nLabel: {prop['label']}"
                        net.add_edge(prop["domain"], prop["range"],
                                   label=label,
                                   title=title,
                                   color="#2196F3", arrows="to",
                                   ntype="Object Property", ename=prop["name"])

            # Add data properties (only those connected to displayed classes)
            if show_data_props and data_props and show_classes and node_count < max_nodes:
                added_datatypes = set()
                for prop in data_props:
                    if node_count >= max_nodes:
                        break
                    # Only show if domain exists as a class node
                    if not prop["domain"] or prop["domain"] not in class_names:
                        continue

                    label = prop["label"] if prop["label"] else prop["name"]
                    title = f"Data Property: {prop['name']}"
                    if prop["domain"]:
                        title += f"\nDomain: {prop['domain']}"
                    if prop["range"]:
                        title += f"\nRange: {prop['range']}"
                    if prop["functional"]:
                        title += "\nFunctional: Yes"

                    net.add_node(f"dprop_{prop['name']}", label=label, title=title,
                               color={"background": "#9C27B0", "border": "#7B1FA2"},
                               shape="ellipse", size=12, font={"color": "#f0f0f0"},
                               ntype="Data Property", ename=prop["name"])
                    node_count += 1

                    # Connect to domain class
                    net.add_edge(prop["domain"], f"dprop_{prop['name']}",
                               title=f"Domain:\n{prop['name']} has domain {prop['domain']}",
                               color="#CE93D8", arrows="to", dashes=True)

                    # Add range as a literal type node
                    if prop["range"] and prop["range"] not in added_datatypes and node_count < max_nodes:
                        range_node_id = f"dtype_{prop['range']}"
                        net.add_node(range_node_id, label=prop["range"],
                                   title=f"Datatype: {prop['range']}",
                                   color={"background": "#607D8B", "border": "#455A64"},
                                   shape="box", size=10, font={"color": "#f0f0f0"})
                        added_datatypes.add(prop["range"])
                        node_count += 1

                    if prop["range"]:
                        net.add_edge(f"dprop_{prop['name']}", f"dtype_{prop['range']}",
                                   title=f"Range:\n{prop['name']} has range {prop['range']}",
                                   color="#CE93D8", arrows="to", dashes=True)

            # Add individuals
            if show_individuals and individuals and node_count < max_nodes:
                for ind in individuals:
                    if node_count >= max_nodes:
                        break
                    label = ind["label"] if ind["label"] else ind["name"]
                    title = f"Individual: {ind['name']}"
                    if ind["classes"]:
                        title += f"\nType: {', '.join(ind['classes'])}"

                    has_issue = ind["name"] in validation_subjects
                    ind_color = ({"background": "#FF9800", "border": "#F44336", "highlight": {"border": "#F44336"}}
                                 if has_issue
                                 else {"background": "#FF9800", "border": "#F57C00"})
                    border_width = 3 if has_issue else 1
                    if has_issue:
                        title += "\n⚠ Has validation issues"
                    net.add_node(f"ind_{ind['name']}", label=label, title=title,
                               color=ind_color, borderWidth=border_width,
                               shape="dot", size=20,
                               ntype="Individual", ename=ind["name"])
                    node_count += 1

                    # Connect to classes
                    if show_classes:
                        for cls_name in ind["classes"]:
                            if any(c["name"] == cls_name for c in classes):
                                net.add_edge(f"ind_{ind['name']}", cls_name,
                                           label="type",
                                           title=f"Instance of:\n{ind['name']} is an instance of {cls_name}",
                                           color="#FFB74D", arrows="to")

            # Add class relations (only if both nodes exist)
            class_relations = ont.get_class_relations()
            if show_classes and classes:
                for rel in class_relations:
                    if rel["subject"] in class_names and rel["object"] in class_names:
                        if rel["relation"] == "equivalentClass":
                            net.add_edge(rel["subject"], rel["object"],
                                       label="equivalentClass",
                                       title=f"Equivalent classes:\n{rel['subject']} and {rel['object']} represent the same concept",
                                       color="#9C27B0", arrows="to")
                        elif rel["relation"] == "disjointWith":
                            net.add_edge(rel["subject"], rel["object"],
                                       label="disjointWith",
                                       title=f"Disjoint classes:\n{rel['subject']} and {rel['object']} cannot share instances",
                                       color="#F44336", arrows="to")

            # Add annotations for classes and individuals
            if show_annotations and node_count < max_nodes:
                annotation_counter = 0
                # Annotations for classes
                if show_classes and classes:
                    for cls in classes:
                        if node_count >= max_nodes:
                            break
                        try:
                            annotations = ont.get_annotations(cls["name"])
                            for ann in annotations:
                                if node_count >= max_nodes:
                                    break
                                # Skip label and comment as they're already shown in tooltip
                                if ann["predicate"] in ["label", "comment"]:
                                    continue
                                annotation_counter += 1
                                ann_id = f"ann_{annotation_counter}"
                                # Use prefixed predicate name
                                pred_display = ann.get("predicate_prefixed", ann["predicate"])
                                # Truncate long values
                                value_display = ann["value"][:30] + "..." if len(ann["value"]) > 30 else ann["value"]
                                net.add_node(ann_id, label=value_display,
                                           title=f"{pred_display}: {ann['value']}",
                                           color={"background": "#795548", "border": "#5D4037"},
                                           shape="box", size=8, font={"size": 10, "color": "#f0f0f0"})
                                node_count += 1
                                net.add_edge(cls["name"], ann_id,
                                           title=f"Annotation: {pred_display}",
                                           color="#A1887F", arrows="to", dashes=True)
                        except Exception:
                            pass  # Skip problematic annotations

                # Annotations for individuals
                if show_individuals and individuals:
                    for ind in individuals:
                        if node_count >= max_nodes:
                            break
                        try:
                            annotations = ont.get_annotations(ind["name"])
                            for ann in annotations:
                                if node_count >= max_nodes:
                                    break
                                if ann["predicate"] in ["label", "comment"]:
                                    continue
                                annotation_counter += 1
                                ann_id = f"ann_{annotation_counter}"
                                pred_display = ann.get("predicate_prefixed", ann["predicate"])
                                value_display = ann["value"][:30] + "..." if len(ann["value"]) > 30 else ann["value"]
                                net.add_node(ann_id, label=value_display,
                                           title=f"{pred_display}: {ann['value']}",
                                           color={"background": "#795548", "border": "#5D4037"},
                                           shape="box", size=8, font={"size": 10, "color": "#f0f0f0"})
                                node_count += 1
                                net.add_edge(f"ind_{ind['name']}", ann_id,
                                           title=f"Annotation: {pred_display}",
                                           color="#A1887F", arrows="to", dashes=True)
                        except Exception:
                            pass  # Skip problematic annotations

            # Generate and display the graph using custom component
            try:
                import json as _json

                nodes_json = _json.dumps(net.nodes)
                edges_json = _json.dumps(net.edges)
                options_json = _json.dumps(net.options)

                # Cache graph data for reuse on rerun
                st.session_state.last_graph_key = graph_key
                st.session_state.last_graph_data = {
                    "nodes": nodes_json,
                    "edges": edges_json,
                    "options": options_json,
                }
                status.empty()

            except Exception as e:
                status.empty()
                st.error(f"Error building graph: {str(e)}")

        # Always display the graph component (even on rerun after selection)
        gdata = st.session_state.get("last_graph_data")
        if gdata:
            import os as _os
            _component_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "lib", "graph_viewer")
            _graph_component = st.components.v1.declare_component("graph_viewer", path=_component_path)

            selection = _graph_component(
                nodes=gdata["nodes"], edges=gdata["edges"], options=gdata["options"],
                height=height - 80, key="graph_viewer", default=None
            )

            # Status bar outside iframe — dark styled
            _type_to_page = {"Class": "Classes", "Object Property": "Properties",
                             "Data Property": "Properties", "Individual": "Individuals"}
            _view_key_map = {
                "Class": lambda n: f"view_class_{n}",
                "Object Property": lambda n: f"view_objprop_{n}",
                "Data Property": lambda n: f"view_dataprop_{n}",
                "Individual": lambda n: f"view_ind_{n}",
            }

            # Status bar with View button
            has_selection = selection and isinstance(selection, dict) and selection.get("selected")
            ntype = selection.get("ntype") if has_selection else None
            ename = selection.get("ename") if has_selection else None
            show_view = has_selection and ntype and ename and ntype in _type_to_page

            if has_selection:
                title_text = (selection.get("title") or "").replace("\n", " | ")
                prefix = "Edge: " if selection.get("isEdge") else ""
                sel_html = f"<b>{prefix}{selection.get('label', '')}</b> — {title_text}"
            else:
                sel_html = "Click a node or edge to see details"

            # Inject CSS to remove gap between status bar columns
            st.markdown("""<style>
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) { gap: 0 !important; }
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) [data-testid="stBaseButton-secondary"] button,
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) button[kind] ,
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) button {
                background: #4CAF50 !important; color: white !important;
                border: none !important; border-radius: 0 4px 4px 0 !important;
                height: 36px !important; min-height: 36px !important; max-height: 36px !important;
                padding: 0 16px !important; line-height: 36px !important;
                margin: 0 !important;
            }
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) [data-testid="stVerticalBlockBorderWrapper"] {
                height: 36px !important; overflow: hidden;
            }
            div[data-testid="stHorizontalBlock"]:has(#graph-status-bar) button:hover {
                background: #388E3C !important;
            }
            </style>""", unsafe_allow_html=True)

            if show_view:
                col_info, col_btn = st.columns([20, 1])
                with col_info:
                    st.markdown(
                        f'<div id="graph-status-bar" style="background:#1e1e1e;color:#fff;padding:6px 12px;'
                        f'border-radius:4px 0 0 4px;font-size:14px;display:flex;align-items:center;gap:8px;'
                        f'height:36px;">'
                        f'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{sel_html}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with col_btn:
                    if st.button("View", key="graph_view_btn", use_container_width=True):
                        page = _type_to_page[ntype]
                        vk = _view_key_map[ntype](ename)
                        st.session_state.search_navigate_to = page
                        st.session_state[vk] = True
                        st.rerun()
            else:
                st.markdown(
                    f'<div id="graph-status-bar" style="background:#1e1e1e;color:#fff;padding:6px 12px;'
                    f'border-radius:4px;font-size:14px;display:flex;align-items:center;gap:8px;'
                    f'height:36px;">'
                    f'<span style="opacity:0.5;font-size:11px;white-space:nowrap;">'
                    f'\U0001f7e2 Classes \U0001f535 Obj Props \U0001f7e3 Data Props \U0001f7e0 Individuals \U0001f7e4 Annotations</span>'
                    f'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{sel_html}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    with tab2:
        st.subheader("Class Hierarchy (Text)")

        if not classes:
            st.info("No classes defined.")
        else:
            # Build hierarchy text
            def build_tree_text(classes):
                roots = [c for c in classes if not c["parents"]]
                if not roots:
                    roots = classes[:1]

                lines = []

                def add_class(cls_name, level=0):
                    cls = next((c for c in classes if c["name"] == cls_name), None)
                    if cls:
                        prefix = "  " * level + ("└── " if level > 0 else "")
                        label = f" ({cls['label']})" if cls["label"] else ""
                        lines.append(f"{prefix}{cls['name']}{label}")
                        for child in cls["children"]:
                            add_class(child, level + 1)

                for root in roots:
                    add_class(root["name"])

                return "\n".join(lines)

            tree_text = build_tree_text(classes)
            st.code(tree_text, language=None)

    with tab3:
        st.subheader("Ontology Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Element Distribution:**")
            chart_data = {
                "Element": ["Classes", "Object Props", "Data Props", "Individuals"],
                "Count": [stats["classes"], stats["object_properties"],
                         stats["data_properties"], stats["individuals"]]
            }
            st.bar_chart(chart_data, x="Element", y="Count")

        with col2:
            st.write("**Quick Stats:**")
            st.write(f"- Total Classes: {stats['classes']}")
            st.write(f"- Total Object Properties: {stats['object_properties']}")
            st.write(f"- Total Data Properties: {stats['data_properties']}")
            st.write(f"- Total Individuals: {stats['individuals']}")
            st.write(f"- Total Restrictions: {stats['restrictions']}")
            st.write(f"- Content Triples: {stats['content_triples']}")


def main():
    """Main application entry point."""
    init_session_state()

    # Sidebar navigation
    st.sidebar.image("docs/assets/ORIONBELT Logo.png", width=200)
    st.sidebar.markdown("# Ontology Builder")
    st.sidebar.markdown("\u00a9 2025 [RALFORION d.o.o.](https://ralforion.com)")
    st.sidebar.caption(f"v{APP_VERSION}")

    pages = {
        "Dashboard": render_dashboard,
        "Classes": render_classes,
        "Properties": render_properties,
        "Individuals": render_individuals,
        "Relations": render_relations,
        "Restrictions": render_restrictions,
        "Advanced": render_advanced,
        "Annotations": render_annotations,
        "Import / Export": render_import_export,
        "Validation": render_validation,
        "Visualization": render_visualization
    }

    # Handle graph view navigation (from visualization click)
    _qp = st.query_params
    if "graph_view_type" in _qp and "graph_view_name" in _qp:
        _gv_type = _qp["graph_view_type"]
        _gv_name = _qp["graph_view_name"]
        _type_to_page = {"Class": "Classes", "Object Property": "Properties", "Data Property": "Properties", "Individual": "Individuals"}
        _view_key_map = {
            "Class": f"view_class_{_gv_name}",
            "Object Property": f"view_objprop_{_gv_name}",
            "Data Property": f"view_dataprop_{_gv_name}",
            "Individual": f"view_ind_{_gv_name}",
        }
        _nav_page = _type_to_page.get(_gv_type)
        if _nav_page:
            st.session_state.search_navigate_to = _nav_page
            _vk = _view_key_map.get(_gv_type)
            if _vk:
                st.session_state[_vk] = True
        st.query_params.clear()
        st.rerun()

    # Handle search navigation
    nav_override = st.session_state.pop("search_navigate_to", None)
    if nav_override and nav_override in pages:
        st.session_state["nav_radio"] = nav_override
    selection = st.sidebar.radio("Navigation", list(pages.keys()), key="nav_radio")

    # Undo / Redo controls
    um = st.session_state.undo_manager
    if um:
        undo_col, redo_col = st.sidebar.columns(2)
        with undo_col:
            if st.button("Undo", disabled=not um.can_undo(), use_container_width=True, key="btn_undo"):
                label = um.undo()
                set_flash_message(f"Undid: {label}", "info")
                st.rerun()
        with redo_col:
            if st.button("Redo", disabled=not um.can_redo(), use_container_width=True, key="btn_redo"):
                label = um.redo()
                set_flash_message(f"Redid: {label}", "info")
                st.rerun()

    st.sidebar.divider()

    # Global search
    type_to_page = {
        "Class": "Classes",
        "Object Property": "Properties",
        "Data Property": "Properties",
        "Individual": "Individuals",
    }
    search_query = st.sidebar.text_input("Search", placeholder="Search resources...", key="global_search")
    if search_query:
        results = st.session_state.ontology.search(search_query)
        if results:
            # Group by type
            grouped: dict[str, list] = {}
            for r in results[:20]:
                grouped.setdefault(r["type"], []).append(r)
            for type_label, items in grouped.items():
                st.sidebar.caption(type_label)
                page = type_to_page.get(type_label, "Dashboard")
                for r in items:
                    label_str = f" ({r['label']})" if r["label"] and r["label"] != r["name"] else ""
                    if st.sidebar.button(f"{r['name']}{label_str}", key=f"search_{type_label}_{r['name']}",
                                         use_container_width=True):
                        st.session_state.search_navigate_to = page
                        # Set the view pane open for the selected resource
                        view_key_map = {
                            "Class": f"view_class_{r['name']}",
                            "Object Property": f"view_objprop_{r['name']}",
                            "Data Property": f"view_dataprop_{r['name']}",
                            "Individual": f"view_ind_{r['name']}",
                        }
                        view_key = view_key_map.get(type_label)
                        if view_key:
                            st.session_state[view_key] = True
                        st.rerun()
        else:
            st.sidebar.caption("No results found.")

    st.sidebar.divider()

    # Quick stats in sidebar
    stats = st.session_state.ontology.get_statistics()
    st.sidebar.caption("Quick Stats")
    st.sidebar.write(f"📦 Classes: {stats['classes']}")
    st.sidebar.write(f"🔗 Object Props: {stats['object_properties']}")
    st.sidebar.write(f"📝 Data Props: {stats['data_properties']}")
    st.sidebar.write(f"👤 Individuals: {stats['individuals']}")
    st.sidebar.write(f"📊 Triples: {stats['content_triples']}")

    # Render selected page
    pages[selection]()


if __name__ == "__main__":
    main()
