"""Tree router — picks the right node table from Category."""
from __future__ import annotations

from mangrove_copilot.engine.dependency_tree import DEPENDENCY_NODES
from mangrove_copilot.engine.redundancy_tree import REDUNDANCY_NODES
from mangrove_copilot.engine.state_machine import Node
from mangrove_copilot.models import Category


class UnsupportedCategoryError(ValueError):
    pass


def get_tree(category: Category) -> dict[int, Node]:
    if category == "Redundancy":
        return REDUNDANCY_NODES
    if category == "Dependency":
        return DEPENDENCY_NODES
    raise UnsupportedCategoryError(
        f"Deterministic routing locked: no tree registered for category {category!r}."
    )
