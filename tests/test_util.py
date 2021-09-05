import string

from uniunihan_db.util import filter_keys


def test_filter_keys() -> None:
    d = {c: ord(c) for c in string.ascii_lowercase}
    letters = "abc"
    assert filter_keys(d, letters) == {"a": ord("a"), "b": ord("b"), "c": ord("c")}
