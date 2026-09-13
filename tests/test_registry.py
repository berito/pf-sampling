import pytest

from pfexp import registry
from pfexp.techniques.base import Move


def test_discovers_technique_files():
    assert "none" in registry.names("move")


def test_create_from_name_and_from_dict():
    assert registry.create("move", "none").name == "none"
    assert registry.create("move", {"name": "none"}).name == "none"


def test_unknown_name_lists_what_is_available():
    with pytest.raises(KeyError, match="available: .*none"):
        registry.get("move", "does_not_exist")


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        registry.register("not_a_kind", "x")


def test_duplicate_name_is_rejected():
    with pytest.raises(ValueError, match="already registered"):
        @registry.register("move", "none")
        class Other(Move):
            pass


def test_unexpected_parameters_are_rejected():
    with pytest.raises(TypeError):
        registry.create("move", {"name": "none", "typo": 1})
