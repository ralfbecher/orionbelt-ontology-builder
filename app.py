"""
OrionBelt Ontology Builder - A Streamlit application for building, editing,
and managing OWL ontologies.
"""

import streamlit as st
from ontology_manager import OntologyManager
import json

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
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "ontology" not in st.session_state:
        st.session_state.ontology = OntologyManager()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "flash_message" not in st.session_state:
        st.session_state.flash_message = None


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
        title = st.text_input("Title", value=metadata.get("title", ""))
        description = st.text_area("Description", value=metadata.get("description", ""))

    with col2:
        version = st.text_input("Version", value=metadata.get("version", ""))
        version_iri = st.text_input("Version IRI", value=metadata.get("version_iri", ""),
                                    help="Optional IRI identifying this version of the ontology")
        creator = st.text_input("Creator", value=metadata.get("creator", ""))

        if st.button("Update Metadata"):
            # Update base URI if changed
            if base_uri and base_uri != ont.base_uri:
                ont.set_base_uri(base_uri)
                show_message(f"Base URI updated to: {ont.base_uri}", "success")

            ont.set_ontology_metadata(title=title, description=description,
                                      version=version, creator=creator,
                                      version_iri=version_iri if version_iri else None)
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

            # Find root classes (no parents)
            root_classes = [c for c in classes if not c["parents"]]

            for cls in classes:
                with st.expander(f"📦 **{cls['name']}**" + (f" - {cls['label']}" if cls['label'] else "")):
                    col_info, col_actions = st.columns([4, 1])

                    with col_info:
                        st.write(f"**URI:** {cls['uri']}")
                        if cls["comment"]:
                            st.write(f"**Comment:** {cls['comment']}")
                        if cls["parents"]:
                            st.write(f"**Parents:** {', '.join(cls['parents'])}")
                        if cls["children"]:
                            st.write(f"**Children:** {', '.join(cls['children'])}")

                    with col_actions:
                        # Edit functionality
                        if f"edit_class_{cls['name']}" not in st.session_state:
                            st.session_state[f"edit_class_{cls['name']}"] = False

                        if st.button("✏️ Edit", key=f"btn_edit_class_{cls['name']}"):
                            st.session_state[f"edit_class_{cls['name']}"] = not st.session_state[f"edit_class_{cls['name']}"]

                        if st.button("🗑️ Delete", key=f"btn_del_class_{cls['name']}"):
                            ont.delete_class(cls["name"])
                            show_message(f"Class '{cls['name']}' deleted!", "success")
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
                                st.session_state[f"edit_class_{cls['name']}"] = False
                                show_message(f"Class '{current_name}' updated!", "success")
                                st.rerun()

            # Table view
            st.subheader("All Classes")
            class_data = []
            for c in classes:
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
            parent = st.selectbox("Parent Class", options=["None"] + class_names,
                                 help="Select a parent class for hierarchy")

            submitted = st.form_submit_button("Add Class")
            if submitted:
                if not name:
                    show_message("Class name is required!", "error")
                elif name in class_names:
                    show_message(f"Class '{name}' already exists!", "error")
                else:
                    parent_val = parent if parent != "None" else None
                    ont.add_class(name, parent=parent_val, label=label, comment=comment)
                    show_message(f"Class '{name}' added successfully!", "success")
                    st.rerun()

    with tab3:
        st.subheader("Edit or Delete Class")

        if not classes:
            st.info("No classes to edit.")
        else:
            selected_class = st.selectbox("Select Class", options=class_names, key="edit_class_select")

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
                            show_message(f"Class '{selected_class}' updated!", "success")
                            st.rerun()

                        if delete_btn:
                            ont.delete_class(selected_class)
                            show_message(f"Class '{selected_class}' deleted!", "success")
                            st.rerun()


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

            for prop in filtered_obj_props:
                with st.expander(f"🔗 **{prop['name']}** ({prop['domain'] or '?'} → {prop['range'] or '?'})"):
                    col_info, col_actions = st.columns([4, 1])

                    with col_info:
                        st.write(f"**URI:** {prop['uri']}")
                        if prop["label"]:
                            st.write(f"**Label:** {prop['label']}")
                        if prop["comment"]:
                            st.write(f"**Comment:** {prop['comment']}")
                        st.write(f"**Domain:** {prop['domain'] or 'Not specified'}")
                        st.write(f"**Range:** {prop['range'] or 'Not specified'}")
                        if prop["characteristics"]:
                            st.write(f"**Characteristics:** {', '.join(prop['characteristics'])}")
                        if prop.get("inverse_of"):
                            st.write(f"**Inverse of:** {prop['inverse_of']}")

                    with col_actions:
                        if f"edit_objprop_{prop['name']}" not in st.session_state:
                            st.session_state[f"edit_objprop_{prop['name']}"] = False

                        if st.button("✏️ Edit", key=f"btn_edit_objprop_{prop['name']}"):
                            st.session_state[f"edit_objprop_{prop['name']}"] = not st.session_state[f"edit_objprop_{prop['name']}"]

                        if st.button("🗑️ Delete", key=f"btn_del_objprop_{prop['name']}"):
                            ont.delete_property(prop["name"])
                            show_message(f"Property '{prop['name']}' deleted!", "success")
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

            datatypes = list(OntologyManager.XSD_DATATYPES.keys())

            for prop in filtered_data_props:
                with st.expander(f"📝 **{prop['name']}** ({prop['domain'] or '?'} → {prop['range']})"):
                    col_info, col_actions = st.columns([4, 1])

                    with col_info:
                        st.write(f"**URI:** {prop['uri']}")
                        if prop["label"]:
                            st.write(f"**Label:** {prop['label']}")
                        if prop["comment"]:
                            st.write(f"**Comment:** {prop['comment']}")
                        st.write(f"**Domain:** {prop['domain'] or 'Not specified'}")
                        st.write(f"**Range (Datatype):** {prop['range']}")
                        st.write(f"**Functional:** {'Yes' if prop['functional'] else 'No'}")

                    with col_actions:
                        if f"edit_dataprop_{prop['name']}" not in st.session_state:
                            st.session_state[f"edit_dataprop_{prop['name']}"] = False

                        if st.button("✏️ Edit", key=f"btn_edit_dataprop_{prop['name']}"):
                            st.session_state[f"edit_dataprop_{prop['name']}"] = not st.session_state[f"edit_dataprop_{prop['name']}"]

                        if st.button("🗑️ Delete", key=f"btn_del_dataprop_{prop['name']}"):
                            ont.delete_property(prop["name"])
                            show_message(f"Property '{prop['name']}' deleted!", "success")
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
                datatypes = list(OntologyManager.XSD_DATATYPES.keys())
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
            for ind in individuals:
                classes_str = ", ".join(ind["classes"]) if ind["classes"] else "No class"
                with st.expander(f"👤 **{ind['name']}** ({classes_str})"):
                    col_info, col_actions = st.columns([4, 1])

                    with col_info:
                        st.write(f"**URI:** {ind['uri']}")
                        if ind["label"]:
                            st.write(f"**Label:** {ind['label']}")
                        if ind["comment"]:
                            st.write(f"**Comment:** {ind['comment']}")
                        st.write(f"**Classes:** {', '.join(ind['classes']) or 'None'}")

                        if ind["properties"]:
                            st.write("**Property Values:**")
                            for prop in ind["properties"]:
                                st.write(f"  - {prop['property']}: {prop['value']}")

                    with col_actions:
                        if f"edit_ind_{ind['name']}" not in st.session_state:
                            st.session_state[f"edit_ind_{ind['name']}"] = False

                        if st.button("✏️ Edit", key=f"btn_edit_ind_{ind['name']}"):
                            st.session_state[f"edit_ind_{ind['name']}"] = not st.session_state[f"edit_ind_{ind['name']}"]

                        if st.button("🗑️ Delete", key=f"btn_del_ind_{ind['name']}"):
                            ont.delete_individual(ind["name"])
                            show_message(f"Individual '{ind['name']}' deleted!", "success")
                            st.rerun()

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

    # Combine all resources
    all_resources = []
    for c in classes:
        all_resources.append({"name": c["name"], "type": "Class"})
    for p in object_props:
        all_resources.append({"name": p["name"], "type": "Object Property"})
    for p in data_props:
        all_resources.append({"name": p["name"], "type": "Data Property"})
    for i in individuals:
        all_resources.append({"name": i["name"], "type": "Individual"})

    tab1, tab2 = st.tabs(["View Annotations", "Add Annotation"])

    with tab1:
        if not all_resources:
            st.info("No resources to annotate. Create classes, properties, or individuals first.")
        else:
            selected = st.selectbox(
                "Select Resource",
                options=[f"{r['name']} ({r['type']})" for r in all_resources],
                key="view_annotations_select"
            )

            if selected:
                resource_name = selected.split(" (")[0]
                annotations = ont.get_annotations(resource_name)

                if not annotations:
                    st.info(f"No annotations found for '{resource_name}'")
                else:
                    st.subheader(f"Annotations for {resource_name}")
                    for ann in annotations:
                        col1, col2, col3 = st.columns([2, 4, 1])
                        with col1:
                            st.write(f"**{ann['predicate']}**")
                        with col2:
                            lang_str = f" @{ann['language']}" if ann.get('language') else ""
                            st.write(f"{ann['value']}{lang_str}")
                        with col3:
                            if st.button("🗑️", key=f"del_ann_{ann['predicate']}_{ann['value'][:10]}"):
                                ont.delete_annotation(resource_name, ann['predicate'], ann['value'])
                                show_message("Annotation deleted!", "success")
                                st.rerun()

    with tab2:
        st.subheader("Add Annotation")

        if not all_resources:
            st.warning("Please create at least one resource first.")
        else:
            with st.form("add_annotation_form"):
                selected = st.selectbox(
                    "Select Resource",
                    options=[f"{r['name']} ({r['type']})" for r in all_resources]
                )

                annotation_types = [
                    "label", "comment", "seeAlso", "isDefinedBy",
                    "prefLabel", "altLabel", "definition", "example", "note",
                    "title", "description", "creator", "contributor", "date",
                    "deprecated"
                ]
                predicate = st.selectbox("Annotation Type", options=annotation_types)

                value = st.text_area("Value")

                language = st.text_input("Language Tag (optional)", placeholder="en, de, fr...")

                submitted = st.form_submit_button("Add Annotation")
                if submitted:
                    if not value:
                        show_message("Value is required!", "error")
                    else:
                        resource_name = selected.split(" (")[0]
                        ont.add_annotation(resource_name, predicate, value,
                                         lang=language if language else None)
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

        import_method = st.radio("Import Method", ["Upload File", "Paste Content"])

        if import_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Choose an ontology file",
                type=["ttl", "owl", "rdf", "xml", "n3", "nt"],
                help="Supported formats: Turtle (.ttl), RDF/XML (.owl, .rdf, .xml), N3 (.n3), N-Triples (.nt)"
            )

            if uploaded_file:
                format_map = {
                    "ttl": "turtle",
                    "owl": "xml",
                    "rdf": "xml",
                    "xml": "xml",
                    "n3": "n3",
                    "nt": "nt"
                }
                ext = uploaded_file.name.split(".")[-1].lower()
                format_ = format_map.get(ext, "turtle")

                if st.button("Import"):
                    try:
                        content = uploaded_file.read().decode("utf-8")
                        ont.load_from_string(content, format=format_)
                        st.session_state.ontology = ont
                        set_flash_message(f"Ontology imported successfully! ({len(ont.graph)} triples)", "success")
                        st.rerun()
                    except Exception as e:
                        show_message(f"Error importing ontology: {str(e)}", "error")

        else:
            content = st.text_area("Paste Ontology Content (Turtle format)", height=300)
            format_ = st.selectbox("Format", ["turtle", "xml", "n3", "nt"])

            if st.button("Import from Content"):
                if not content:
                    show_message("Please paste ontology content!", "error")
                else:
                    try:
                        ont.load_from_string(content, format=format_)
                        st.session_state.ontology = ont
                        set_flash_message(f"Ontology imported successfully! ({len(ont.graph)} triples)", "success")
                        st.rerun()
                    except Exception as e:
                        show_message(f"Error importing ontology: {str(e)}", "error")

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
            title = st.text_input("Title")
            description = st.text_area("Description")
            version = st.text_input("Version", value="1.0.0")
            creator = st.text_input("Creator")

            submitted = st.form_submit_button("Create New Ontology")
            if submitted:
                if not base_uri:
                    show_message("Base URI is required!", "error")
                else:
                    st.session_state.ontology = OntologyManager(base_uri=base_uri)
                    st.session_state.ontology.set_ontology_metadata(
                        title=title, description=description,
                        version=version, creator=creator
                    )
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
                        show_message(f"Expression added to {target_class}", "success")
                        st.rerun()
                    elif selected_classes:
                        ont.add_class_expression(target_class, expr_type,
                            classes=selected_classes)
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
    individuals = ont.get_individuals()

    stats = ont.get_statistics()

    if stats["content_triples"] == 0:
        st.info("No content to visualize. Add classes, properties, or individuals first.")
        return

    tab1, tab2, tab3 = st.tabs(["Interactive Graph", "Class Hierarchy", "Statistics"])

    with tab1:
        st.subheader("Interactive Ontology Graph")

        # Graph options
        col1, col2, col3 = st.columns(3)
        with col1:
            show_classes = st.checkbox("Show Classes", value=True)
        with col2:
            show_properties = st.checkbox("Show Properties", value=True)
        with col3:
            show_individuals = st.checkbox("Show Individuals", value=True)

        col1, col2 = st.columns(2)
        with col1:
            height = st.slider("Graph Height", 400, 800, 600)
        with col2:
            physics = st.checkbox("Enable Physics", value=True)

        # Build the graph
        from pyvis.network import Network
        import tempfile
        import os

        net = Network(height=f"{height}px", width="100%", bgcolor="#ffffff",
                     font_color="#333333", directed=True)

        # Configure physics
        if physics:
            net.barnes_hut(gravity=-3000, central_gravity=0.3,
                         spring_length=100, spring_strength=0.05)
        else:
            net.toggle_physics(False)

        # Add classes as nodes
        if show_classes and classes:
            for cls in classes:
                label = cls["label"] if cls["label"] else cls["name"]
                title = f"Class: {cls['name']}"
                if cls["label"]:
                    title += f"\nLabel: {cls['label']}"
                if cls["comment"]:
                    title += f"\nComment: {cls['comment'][:100]}"

                net.add_node(cls["name"], label=label, title=title,
                           color="#4CAF50", shape="box", size=25,
                           font={"color": "white"})

            # Add class hierarchy edges
            for cls in classes:
                for parent in cls["parents"]:
                    net.add_edge(cls["name"], parent, label="subClassOf",
                               color="#81C784", arrows="to")

        # Add object properties and their connections
        if show_properties and object_props:
            for prop in object_props:
                # Add property as a small node
                label = prop["label"] if prop["label"] else prop["name"]
                title = f"Object Property: {prop['name']}"
                if prop["domain"]:
                    title += f"\nDomain: {prop['domain']}"
                if prop["range"]:
                    title += f"\nRange: {prop['range']}"

                net.add_node(f"prop_{prop['name']}", label=label, title=title,
                           color="#2196F3", shape="ellipse", size=15,
                           font={"color": "white"})

                # Connect to domain and range if they exist
                if prop["domain"] and show_classes:
                    net.add_edge(prop["domain"], f"prop_{prop['name']}",
                               color="#90CAF9", arrows="to", dashes=True)
                if prop["range"] and show_classes:
                    net.add_edge(f"prop_{prop['name']}", prop["range"],
                               color="#90CAF9", arrows="to", dashes=True)

        # Add individuals
        if show_individuals and individuals:
            for ind in individuals:
                label = ind["label"] if ind["label"] else ind["name"]
                title = f"Individual: {ind['name']}"
                if ind["classes"]:
                    title += f"\nType: {', '.join(ind['classes'])}"

                net.add_node(f"ind_{ind['name']}", label=label, title=title,
                           color="#FF9800", shape="dot", size=20,
                           font={"color": "white"})

                # Connect to classes
                if show_classes:
                    for cls_name in ind["classes"]:
                        if any(c["name"] == cls_name for c in classes):
                            net.add_edge(f"ind_{ind['name']}", cls_name,
                                       label="type", color="#FFB74D", arrows="to")

        # Add class relations
        class_relations = ont.get_class_relations()
        if show_classes:
            for rel in class_relations:
                if rel["relation"] == "equivalentClass":
                    net.add_edge(rel["subject"], rel["object"],
                               label="≡", color="#9C27B0", arrows="to")
                elif rel["relation"] == "disjointWith":
                    net.add_edge(rel["subject"], rel["object"],
                               label="⊥", color="#F44336", arrows="to")

        # Generate and display the graph
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, "r", encoding="utf-8") as f:
                    html_content = f.read()
                os.unlink(tmp.name)

            # Display in Streamlit
            st.components.v1.html(html_content, height=height + 50, scrolling=True)

        except Exception as e:
            st.error(f"Error rendering graph: {str(e)}")

        st.caption("Drag nodes to rearrange • Scroll to zoom • Hover for details")

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
    st.sidebar.title("🌐 OrionBelt")
    st.sidebar.caption("Ontology Builder")

    st.sidebar.divider()

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

    selection = st.sidebar.radio("Navigation", list(pages.keys()))

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
