from lego_creator.rebrickable import extract_set_inventory

INVENTORIES = [
    {"id": "10", "version": "1", "set_num": "45678-1"},
    {"id": "20", "version": "2", "set_num": "45678-1"},
    {"id": "30", "version": "1", "set_num": "9999-1"},
]

INVENTORY_PARTS = [
    {"inventory_id": "10", "part_num": "2780", "color_id": "0", "quantity": "92", "is_spare": "False"},
    {"inventory_id": "20", "part_num": "61332", "color_id": "0", "quantity": "92", "is_spare": "False"},
    {"inventory_id": "20", "part_num": "61332", "color_id": "0", "quantity": "3", "is_spare": "True"},
    {"inventory_id": "20", "part_num": "3713", "color_id": "71", "quantity": "10", "is_spare": "False"},
    {"inventory_id": "30", "part_num": "3001", "color_id": "4", "quantity": "1", "is_spare": "False"},
]


def test_extract_uses_latest_version_and_drops_spares():
    rows = extract_set_inventory(
        INVENTORIES, INVENTORY_PARTS, {"61332": "Technic Pin", "3713": "Technic Bush"}, "45678-1"
    )
    assert rows == [
        {"part_num": "3713", "color_id": "71", "quantity": "10", "name": "Technic Bush"},
        {"part_num": "61332", "color_id": "0", "quantity": "92", "name": "Technic Pin"},
    ]


def test_extract_unknown_set_returns_empty():
    assert extract_set_inventory(INVENTORIES, INVENTORY_PARTS, {}, "1-1") == []
