"""Tests for snapshot infrastructure and undo/redo."""

from ontology_manager import OntologyManager, UndoManager


def test_snapshot_roundtrip(populated_om):
    """Snapshot capture and restore preserves graph content."""
    original_classes = sorted(c["name"] for c in populated_om.get_classes())
    snapshot = populated_om.take_snapshot()

    populated_om.add_class("NewClass")
    assert "NewClass" in [c["name"] for c in populated_om.get_classes()]

    populated_om.restore_snapshot(snapshot)
    restored_classes = sorted(c["name"] for c in populated_om.get_classes())
    assert restored_classes == original_classes


def test_snapshot_preserves_namespace(populated_om):
    snapshot = populated_om.take_snapshot()
    old_base = populated_om.base_uri
    populated_om.restore_snapshot(snapshot)
    assert populated_om.base_uri == old_base


def test_undo_basic(populated_om):
    um = UndoManager(populated_om)
    populated_om.add_class("Temp")
    um.checkpoint("Added Temp")

    assert "Temp" in [c["name"] for c in populated_om.get_classes()]
    um.undo()
    assert "Temp" not in [c["name"] for c in populated_om.get_classes()]


def test_redo_basic(populated_om):
    um = UndoManager(populated_om)
    populated_om.add_class("Temp")
    um.checkpoint("Added Temp")

    um.undo()
    assert "Temp" not in [c["name"] for c in populated_om.get_classes()]
    um.redo()
    assert "Temp" in [c["name"] for c in populated_om.get_classes()]


def test_undo_returns_none_at_bottom(populated_om):
    um = UndoManager(populated_om)
    assert um.undo() is None


def test_redo_returns_none_when_empty(populated_om):
    um = UndoManager(populated_om)
    assert um.redo() is None


def test_checkpoint_clears_redo_stack(populated_om):
    um = UndoManager(populated_om)
    populated_om.add_class("A")
    um.checkpoint("A")
    um.undo()
    assert um.can_redo()

    populated_om.add_class("B")
    um.checkpoint("B")
    assert not um.can_redo()


def test_multiple_undo_redo(populated_om):
    um = UndoManager(populated_om)

    populated_om.add_class("Step1")
    um.checkpoint("Step1")
    populated_om.add_class("Step2")
    um.checkpoint("Step2")
    populated_om.add_class("Step3")
    um.checkpoint("Step3")

    def names():
        return [c["name"] for c in populated_om.get_classes()]

    assert "Step3" in names()
    um.undo()
    assert "Step3" not in names()
    assert "Step2" in names()
    um.undo()
    assert "Step2" not in names()
    assert "Step1" in names()
    um.redo()
    assert "Step2" in names()


def test_max_history_enforced():
    om = OntologyManager()
    um = UndoManager(om, max_history=5)
    for i in range(10):
        om.add_class(f"C{i}")
        um.checkpoint(f"C{i}")
    assert len(um._undo_stack) <= 5


def test_undo_labels(populated_om):
    um = UndoManager(populated_om)
    populated_om.add_class("A")
    um.checkpoint("Added A")
    populated_om.add_class("B")
    um.checkpoint("Added B")

    assert um.undo_labels == ["Added A", "Added B"]
    um.undo()
    assert um.redo_labels == ["Added B"]
