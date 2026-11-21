from lego_creator.catalog import (
    check_catalog,
    model_slug,
    new_meta,
    next_number,
    revise,
    updated,
)


def meta(series="tank", number=1, **extra):
    return {**new_meta("탱크 1호", series, number, {"45678-1": 2}, "2026-11-22"), **extra}


def codes(issues):
    return [(i.level, i.code) for i in issues]


def test_slug_is_series_and_number():
    assert model_slug("tank", 2) == "tank-2"


def test_next_number_counts_within_the_series():
    metas = {"tank-1": meta(), "tank-3": meta(number=3), "arm-1": meta("arm")}
    assert next_number(metas, "tank") == 4
    assert next_number(metas, "arm") == 2
    assert next_number(metas, "crane") == 1


def test_new_meta_starts_a_draft_at_revision_one():
    m = new_meta("탱크 2호", "tank", 2, {"45678-1": 1}, "2026-11-22", based_on="tank-1")
    assert m["name"] == "탱크 2호" and m["series"] == "tank" and m["number"] == 2
    assert m["status"] == "draft" and m["version"] == 1 and m["created"] == "2026-11-22"
    assert m["revisions"] == [{"version": 1, "date": "2026-11-22", "note": "First draft"}]
    assert m["based_on"] == "tank-1"
    assert "based_on" not in new_meta("탱크 1호", "tank", 1, {}, "2026-11-22")


def test_revise_bumps_the_version_and_keeps_history():
    first = meta()
    second = revise(first, "Brace the side frames", "2026-12-01")
    assert second["version"] == 2 and second["created"] == "2026-11-22"
    assert second["revisions"][-1] == {"version": 2, "date": "2026-12-01", "note": "Brace the side frames"}
    assert len(second["revisions"]) == 2 and first["version"] == 1
    assert updated(second) == "2026-12-01" and updated(first) == "2026-11-22"


def test_catalog_accepts_a_consistent_model():
    assert check_catalog("tank-1", {"tank-1": meta()}) == []


def test_catalog_flags_slug_that_does_not_match_series_and_number():
    assert codes(check_catalog("tank", {"tank": meta()})) == [("error", "slug-mismatch")]


def test_catalog_flags_missing_and_cyclic_base():
    metas = {"tank-1": meta(based_on="tank-9")}
    assert codes(check_catalog("tank-1", metas)) == [("error", "based-on-missing")]
    metas = {"tank-1": meta(based_on="tank-2"), "tank-2": meta(number=2, based_on="tank-1")}
    assert codes(check_catalog("tank-1", metas)) == [("error", "based-on-cycle")]


def test_catalog_flags_version_that_disagrees_with_the_revision_list():
    assert codes(check_catalog("tank-1", {"tank-1": meta(version=3)})) == [("error", "revision-mismatch")]
