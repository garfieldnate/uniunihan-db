from uniunihan_db.component_group import ComponentGroup, PurityType


def test_chars():
    group = ComponentGroup("x", {"a": ["x", "y", "z"], "b": ["x", "w", "u"]})
    assert group.chars == set(["x", "y", "z", "w", "u"])


def test_pron_to_chars_are_sorted():
    group = ComponentGroup("x", {"a": ["y", "x", "z"], "b": ["x", "w", "u"]})
    pron_to_chars = group.pron_to_chars
    assert pron_to_chars == {"a": ["x", "y", "z"], "b": ["u", "w", "x"]}


def test_exceptions():
    group = ComponentGroup(
        "x",
        {
            "a": ["x", "y", "z"],
            "b": ["x", "w", "u"],
            "c": ["v"],
            "d": ["t"],
        },
    )
    assert group.exceptions == {"c": "v", "d": "t"}


def test_purity_type():
    pron_to_chars = {"a": ["x"]}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.SINGLETON

    pron_to_chars["a"].extend(["y", "z"])
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.PURE

    pron_to_chars["b"] = ["c"]
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.SEMI_PURE

    pron_to_chars["b"].extend(["d", "e"])
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_A

    pron_to_chars["c"] = ["w"]
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_B

    pron_to_chars = {"a": ["x", "a"], "b": ["x", "c"], "c": ["e", "f"], "d": ["g", "h"]}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_C

    pron_to_chars = {"a": ["x", "y"], "b": ["z"], "c": ["x"]}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_D

    pron_to_chars = {"a": ["x"], "b": ["z"], "c": ["x"]}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.NO_PATTERN


def test_get_char_presentation():
    pron_to_chars = {
        "b": ["x", "w", "u"],
        "a": ["x", "y", "z"],
        "c": ["u", "t"],
        "d": ["v", "z"],
    }
    group = ComponentGroup("x", pron_to_chars)
    char_clusters = group.get_char_presentation()
    assert char_clusters == [["x", "y", "z"], ["u", "w"], ["t"], ["v"]]
