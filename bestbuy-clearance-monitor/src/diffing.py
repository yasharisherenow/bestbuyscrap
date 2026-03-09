"""State comparison logic for meaningful product changes."""

from __future__ import annotations

from typing import Tuple

Product = dict[str, str]
State = dict[str, Product]

# Keep raw availability text out of change triggers to reduce noisy alerts.
# Normalized availability values are the meaningful signal.
MEANINGFUL_FIELDS = (
    "price",
    "online_availability",
    "pickup_availability",
    "cpu",
    "ram",
    "storage",
    "gpu",
)


def compare_states(previous: State, current: State) -> dict[str, list[dict[str, object]]]:
    """Return added, removed and changed products with field-level diff."""
    added: list[dict[str, object]] = []
    removed: list[dict[str, object]] = []
    changed: list[dict[str, object]] = []

    for key, product in current.items():
        if key not in previous:
            added.append({"key": key, "current": product})
            continue

        old = previous[key]
        field_changes: dict[str, Tuple[str, str]] = {}
        for field in MEANINGFUL_FIELDS:
            old_val = str(old.get(field, ""))
            new_val = str(product.get(field, ""))
            if old_val != new_val:
                field_changes[field] = (old_val, new_val)

        if field_changes:
            changed.append(
                {
                    "key": key,
                    "previous": old,
                    "current": product,
                    "changes": field_changes,
                }
            )

    for key, product in previous.items():
        if key not in current:
            removed.append({"key": key, "previous": product})

    return {"added": added, "removed": removed, "changed": changed}


def has_meaningful_changes(diff: dict[str, list[dict[str, object]]]) -> bool:
    """Return True if any meaningful events exist."""
    return bool(diff["added"] or diff["removed"] or diff["changed"])
