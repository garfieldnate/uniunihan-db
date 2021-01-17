import pytest

from uniunihan_db.component_group import ComponentGroup, PurityType


def test_no_chars_raises_error():
    with pytest.raises(ValueError):
        ComponentGroup("x", {})


def test_chars():
    group = ComponentGroup(
        "x", {"x": ["b", "a"], "y": ["a"], "z": ["a"], "w": ["b"], "u": ["b"]}
    )
    assert group.chars == set(["x", "y", "z", "w", "u"])


def test_pron_to_chars():
    group = ComponentGroup(
        "x", {"x": ["b", "a"], "y": ["a"], "z": ["a"], "w": ["b"], "u": ["b"]}
    )
    pron_to_chars = group.pron_to_chars
    assert pron_to_chars == {"a": ["x", "y", "z"], "b": ["u", "w", "x"]}


def test_non_empty_prons():
    group = ComponentGroup("x", {"x": ["b", "a"], "y": []})
    assert not group.empty_prons


def test_exceptions():
    group = ComponentGroup(
        "x",
        {
            "x": ["b", "a"],
            "y": ["a", "b"],
            "z": ["a"],
            "w": ["b"],
            "u": ["b"],
            "v": ["c"],
            "t": ["d"],
        },
    )
    assert group.exceptions == {"c": "v", "d": "t"}


def test_purity_type():
    char_to_prons = {"x": ["a"]}
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.SINGLETON

    char_to_prons["y"] = ["a"]
    char_to_prons["z"] = ["a"]
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.PURE

    char_to_prons["c"] = ["b"]
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.SEMI_PURE

    char_to_prons["d"] = ["b"]
    char_to_prons["e"] = ["b"]
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.MIXED_A

    char_to_prons["w"] = ["c"]
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.MIXED_B

    char_to_prons = {
        "x": ["a", "b"],
        "c": ["b"],
        "e": ["c"],
        "f": ["c"],
        "g": ["d"],
        "h": ["d"],
    }
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.MIXED_C

    char_to_prons = {"x": ["a", "c"], "y": ["a"], "z": ["b"]}
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.MIXED_D

    char_to_prons = {"x": ["a", "c"], "z": ["b"]}
    group = ComponentGroup("x", char_to_prons)
    assert group.purity_type == PurityType.NO_PATTERN


def test_get_char_presentation():
    char_to_prons = {
        "x": ["a", "b"],
        "y": ["a"],
        "u": ["b", "c"],
        "w": ["b"],
        "t": ["c"],
        "v": ["d"],
        "z": ["d", "a"],
    }
    group = ComponentGroup("x", char_to_prons)
    char_clusters = group.get_char_presentation()
    assert char_clusters == [["x", "y", "z"], ["u", "w"], ["t"], ["v"]]


def test_group_with_no_pronunciations():
    group = ComponentGroup("x", {"a": [], "b": [], "c": []})
    assert group.empty_prons
    assert group.chars == {"a", "b", "c"}
    assert group.purity_type == PurityType.NO_PATTERN
    assert group.pron_to_chars == {"": ["a", "b", "c"]}
    assert group.get_char_presentation() == [["a", "b", "c"]]
