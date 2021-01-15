from uniunihan_db.component_group import ComponentGroup, PurityType


def test_chars():
    group = ComponentGroup("x", {"a": set(["x", "y", "z"]), "b": set(["x", "w", "u"])})
    assert group.chars == set(["x", "y", "z", "w", "u"])


def test_exceptions():
    group = ComponentGroup(
        "x",
        {
            "a": set(["x", "y", "z"]),
            "b": set(["x", "w", "u"]),
            "c": set(["v"]),
            "d": set(["t"]),
        },
    )
    assert group.exceptions == {"c": "v", "d": "t"}


def test_purity_type():
    pron_to_chars = {"a": set("x")}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.SINGLETON

    pron_to_chars["a"].update("yz")
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.PURE

    pron_to_chars["b"] = set("c")
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.SEMI_PURE

    pron_to_chars["b"].update("de")
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_A

    pron_to_chars["c"] = set("w")
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_B

    pron_to_chars = {"a": set("xa"), "b": set("xc"), "c": set("ef"), "d": set("gh")}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_C

    pron_to_chars = {"a": set("xy"), "b": set("z"), "c": set("x")}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.MIXED_D

    pron_to_chars = {"a": set("x"), "b": set("z"), "c": set("x")}
    group = ComponentGroup("x", pron_to_chars)
    assert group.purity_type == PurityType.NO_PATTERN
