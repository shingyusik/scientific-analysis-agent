from typing import Dict, Type
from filters.filter_base import FilterBase
from filters.slice_filter import SliceFilter
from filters.clip_filter import ClipFilter

_filter_registry: Dict[str, Type[FilterBase]] = {}


def register_filter(filter_type: str, filter_class: Type[FilterBase]) -> None:
    """Register a filter class."""
    _filter_registry[filter_type] = filter_class


def get_filter(filter_type: str) -> Type[FilterBase] | None:
    """Get a filter class by type."""
    return _filter_registry.get(filter_type)


def get_all_filter_types() -> list[str]:
    """Get all registered filter types."""
    return list(_filter_registry.keys())


register_filter("slice_filter", SliceFilter)
register_filter("clip_filter", ClipFilter)

