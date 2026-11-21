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
    d = root / "models" / "line-follower-1"
    meta = yaml.safe_load((d / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 1}
    assert meta["status"] == "draft"
    assert (d / "model.mpd").read_text().startswith("0 FILE main.ldr\n")
    assert (d / "spec.md").exists()
    assert (d / "missions.yaml").exists() and not (d / "program").exists()


def test_new_writes_a_korean_name_readably(tmp_path):
    root = setup_root(tmp_path)
    assert run(root, "new", "tank", "--name", "탱크") == 0
    assert "name: 탱크 1호" in (root / "models" / "tank-1" / "model.yaml").read_text(encoding="utf-8")


def test_new_numbers_models_within_a_series(tmp_path):
    root = setup_root(tmp_path)
    assert run(root, "new", "x") == 0
    assert run(root, "new", "x") == 0
    assert run(root, "new", "bad name") != 0
    assert sorted(p.name for p in (root / "models").iterdir()) == ["x-1", "x-2"]
    meta = yaml.safe_load((root / "models" / "x-2" / "model.yaml").read_text())
    assert (meta["series"], meta["number"], meta["version"]) == ("x", 2, 1)


def test_new_from_copies_the_base_model_and_records_it(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "tank", "--name", "탱크")
    base = root / "models" / "tank-1"
    (base / "model.mpd").write_text("0 FILE main.ldr\n0 탱크\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")
    (base / "missions.yaml").write_text("# base missions\n[]\n")
    assert run(root, "new", "tank", "--from", "tank-1") == 0
    d = root / "models" / "tank-2"
    meta = yaml.safe_load((d / "model.yaml").read_text(encoding="utf-8"))
    assert meta["name"] == "탱크 2호" and meta["based_on"] == "tank-1"
    assert "3001.dat" in (d / "model.mpd").read_text() and (d / "missions.yaml").read_text() == "# base missions\n[]\n"
    assert run(root, "new", "tank", "--from", "nope-1") != 0


def test_revise_records_a_new_revision(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    assert run(root, "revise", "x-1", "-m", "Brace the frame") == 0
    meta = yaml.safe_load((root / "models" / "x-1" / "model.yaml").read_text())
    assert meta["version"] == 2 and meta["revisions"][-1]["note"] == "Brace the frame"


def test_list_shows_models_and_filters(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "tank", "--name", "탱크")
    run(root, "new", "tank", "--from", "tank-1")
    run(root, "new", "arm")
    capsys.readouterr()
    assert run(root, "list") == 0
    out = capsys.readouterr().out
    assert "tank-1" in out and "tank-2" in out and "arm-1" in out and "탱크 2호" in out and "draft" in out
    assert run(root, "list", "--series", "tank") == 0
    out = capsys.readouterr().out
    assert "tank-2" in out and "tank-1" in out and "arm-1" not in out
    assert run(root, "list", "--status", "ready") == 0
    assert "tank-1" not in capsys.readouterr().out


def test_validate_checks_missions_against_declared_ports(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    d = root / "models" / "x-1"
    (d / "model.mpd").write_text("0 FILE main.ldr\n0 !LC PORT A 54675c01 drive\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 54675c01.dat\n")
    (d / "missions.yaml").write_text("- title: t\n  goal: g\n  blocks:\n  - [run_motor_for, B, clockwise, 1, rotations]\n")
    capsys.readouterr()
    assert run(root, "validate", "x-1") == 1
    assert "mission-port-undeclared" in capsys.readouterr().out
    (d / "missions.yaml").write_text("- title: t\n  goal: g\n  blocks:\n  - [run_motor_for, A, clockwise, 1, rotations]\n")
    assert run(root, "validate", "x-1") == 0


def test_validate_scaffold_passes(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    assert run(root, "validate", "x-1") == 0


def test_validate_fails_on_inventory_shortage(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    mpd = root / "models" / "x-1" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n" * 2)
    assert run(root, "validate", "x-1") == 1
    assert "inventory-shortage" in capsys.readouterr().out


def test_bom_lists_parts_with_titles(tmp_path, capsys):
    root = setup_root(tmp_path)
    run(root, "new", "x")
    mpd = root / "models" / "x-1" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")
    capsys.readouterr()
    assert run(root, "bom", "x-1") == 0
    out = capsys.readouterr().out
    assert "3001" in out and "Brick  2 x  4" in out


def test_new_defaults_kits_to_owned_collection(tmp_path):
    root = setup_root(tmp_path)
    (root / ".local").mkdir()
    (root / ".local" / "owned.yaml").write_text("kits:\n  45678-1: 2\n  45681-1: 1\n")
    run(root, "new", "x")
    meta = yaml.safe_load((root / "models" / "x-1" / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 2, "45681-1": 1}


def test_new_repeated_kit_flag_counts_sets(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x", "--kit", "45678-1", "--kit", "45678-1")
    meta = yaml.safe_load((root / "models" / "x-1" / "model.yaml").read_text())
    assert meta["kits"] == {"45678-1": 2}


def test_validate_multiplies_inventory_by_set_quantity(tmp_path):
    root = setup_root(tmp_path)
    run(root, "new", "x", "--kit", "45678-1", "--kit", "45678-1")
    mpd = root / "models" / "x-1" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n" * 2)
    assert run(root, "validate", "x-1") == 0


def test_validate_treats_blank_kit_quantity_as_unknown(tmp_path, capsys):
    root = setup_root(tmp_path)
    (root / "inventory" / "tank.csv").write_text("part_num,color_id,quantity,name\n3020,0,,Plate\n")
    run(root, "new", "x", "--kit", "45678-1", "--kit", "tank")
    mpd = root / "models" / "x-1" / "model.mpd"
    mpd.write_text(mpd.read_text() + "1 0 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n")
    assert run(root, "validate", "x-1") == 0
    assert "quantity-unknown" in capsys.readouterr().out


def test_download_sends_a_tool_user_agent(tmp_path, monkeypatch):
    # library.ldraw.org answers 403 to urllib's default "Python-urllib/x.y" agent.
    import io
    import urllib.request

    from lego_creator import cli

    seen = {}

    def fake_urlopen(req, *a, **k):
        seen["ua"] = req.get_header("User-agent")
        return io.BytesIO(b"payload")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    out = cli._download("https://example.invalid/x.zip", tmp_path / "x.zip")
    assert out.read_bytes() == b"payload"
    assert seen["ua"] and seen["ua"].startswith("brick-steps/") and "Python-urllib" not in seen["ua"]


def test_release_check_prints_notes_or_fails(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.2"\n')
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n## [0.0.2] - 2026-12-01\n\n### Fixed\n- A bug\n")
    assert main(["--root", str(tmp_path), "release-check", "v0.0.2"]) == 0
    assert capsys.readouterr().out.strip() == "### Fixed\n- A bug"
    assert main(["--root", str(tmp_path), "release-check", "v0.0.3"]) == 1
