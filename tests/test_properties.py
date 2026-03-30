"""Tests for property CRUD operations."""


def test_add_object_property(om):
    om.add_class("A")
    om.add_class("B")
    om.add_object_property("relatesTo", domain="A", range_="B")
    props = om.get_object_properties()
    names = [p["name"] for p in props]
    assert "relatesTo" in names


def test_add_data_property(om):
    om.add_class("A")
    om.add_data_property("hasAge", domain="A", range_="integer")
    props = om.get_data_properties()
    names = [p["name"] for p in props]
    assert "hasAge" in names


def test_delete_property(populated_om):
    populated_om.delete_property("worksFor")
    obj_props = populated_om.get_object_properties()
    names = [p["name"] for p in obj_props]
    assert "worksFor" not in names


def test_rename_property(populated_om):
    result = populated_om.rename_property("worksFor", "employedBy")
    assert result is True
    names = [p["name"] for p in populated_om.get_object_properties()]
    assert "employedBy" in names
    assert "worksFor" not in names
