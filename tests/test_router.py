import pytest

from mangrove_copilot.engine.router import (
    DEPENDENCY_NODES,
    REDUNDANCY_NODES,
    UnsupportedCategoryError,
    get_tree,
)


def test_redundancy_routes_correctly():
    assert get_tree("Redundancy") is REDUNDANCY_NODES


def test_dependency_routes_correctly():
    assert get_tree("Dependency") is DEPENDENCY_NODES


def test_unknown_category_is_locked_down():
    with pytest.raises(UnsupportedCategoryError):
        get_tree("SomethingElse")  # type: ignore[arg-type]
