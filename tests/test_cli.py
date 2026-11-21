from pathlib import Path

import yaml

from lego_creator.cli import main

FIXTURE_LIB = Path(__file__).parent / "fixtures" / "ldraw"


def setup_root(tmp_path: Path) -> Path:
    inv = tmp_path / "inventory"
    inv.mkdir()
    (inv / "45678-1.csv").write_text("part_num,color_id,quantity,name\n3001,4,1,Brick\n54675,322,1,Motor\n")
    (inv / "id-map.csv").write_text("ldraw_id,kit_part,qty,color,note\n54675c01,54675,1,,\n")
    return tmp_path


def run(root: Path, *args: str) -> int:
    return main(["--root", str(root), "--ldraw", str(FIXTURE_LIB), *args])


def test_new_scaffolds_model_directory(tmp_path):
    root = setup_root(tmp_path)
    assert run(root, "new", "line-follower") == 0
    d = root / "models" / "line-follower"
    meta = yaml.safe_load((d / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 1}
    assert meta["status"] == "draft"
    assert (d / "model.mpd").read_text().startswith("0 FILE main.ldr\n")
    assert (d / "spec.md").exists()
    assert (d / "program" / "main.py").exists()


def test_new_refuses_existing_slug(tmp_path):
    root = setup_root(tmp_path)
    assert run(root, "new", "x") == 0
    assert run(root, "new", "x") != 0


def test_validate_scaffold_passes(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    assert run(root, "validate", "x") == 0


def test_validate_fails_on_inventory_shortage(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    mpd = root / "models" / "x" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n" * 2)
    assert run(root, "validate", "x") == 1
    assert "inventory-shortage" in capsys.readouterr().out


def test_bom_lists_parts_with_titles(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    mpd = root / "models" / "x" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")
    capsys.readouterr()
    assert run(root, "bom", "x") == 0
    out = capsys.readouterr().out
    assert "3001" in out and "Brick  2 x  4" in out


def test_new_defaults_kits_to_owned_collection(tmp_path):
    root = setup_root(tmp_path)
    (root / ".local").mkdir()
    (root / ".local" / "owned.yaml").write_text("kits:\n  45678-1: 2\n  45681-1: 1\n")
    run(root, "new", "x")
    meta = yaml.safe_load((root / "models" / "x" / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 2, "45681-1": 1}


def test_new_repeated_kit_flag_counts_sets(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x", "--kit", "45678-1", "--kit", "45678-1")
    meta = yaml.safe_load((root / "models" / "x" / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 2}


def test_validate_multiplies_inventory_by_set_quantity(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x", "--kit", "45678-1", "--kit", "45678-1")
    mpd = root / "models" / "x" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n" * 2)
    assert run(root, "validate", "x") == 0


def test_validate_treats_blank_kit_quantity_as_unknown(tmp_path, capsys):
    root = setup_root(tmp_path)
    (root / "inventory" / "tank.csv").write_text("part_num,color_id,quantity,name\n3020,0,,Plate\n")
    run(root, "new", "x", "--kit", "45678-1", "--kit", "tank")
    mpd = root / "models" / "x" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 0 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n")
    assert run(root, "validate", "x") == 0
    assert "quantity-unknown" in capsys.readouterr().out
