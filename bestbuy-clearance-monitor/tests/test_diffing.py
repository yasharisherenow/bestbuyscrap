from src.diffing import compare_states, has_meaningful_changes


def test_compare_states_detects_added_removed_changed() -> None:
    previous = {
        "123": {
            "sku": "123",
            "price": "999",
            "online_availability": "available_online",
            "pickup_availability": "available_for_pickup",
            "delivery_raw": "Available to ship",
            "pickup_raw": "Available for pickup",
            "cpu": "i5",
            "ram": "16GB",
            "storage": "1TB",
            "gpu": "RTX",
        },
        "999": {"sku": "999", "price": "100"},
    }
    current = {
        "123": {
            "sku": "123",
            "price": "899",
            "online_availability": "sold_out_online",
            "pickup_availability": "available_for_pickup",
            "delivery_raw": "Sold out online",
            "pickup_raw": "Available for pickup",
            "cpu": "i5",
            "ram": "16GB",
            "storage": "1TB",
            "gpu": "RTX",
        },
        "456": {"sku": "456", "price": "1234"},
    }

    diff = compare_states(previous, current)

    assert len(diff["added"]) == 1
    assert len(diff["removed"]) == 1
    assert len(diff["changed"]) == 1
    assert has_meaningful_changes(diff)
