from uniunihan_db.component.index import find_component_groups


def test_group_assignment():
    char_to_prons = {
        "館": ["kan", "foo"],
        "官": ["kan"],
        "棺": ["kan"],
        "可": ["ka", "foo"],
        "何": ["ka"],
        "河": ["ka"],
    }
    comp_to_char = {"官": "館官菅棺倌管琯輨悹涫痯錧婠悺逭", "可": "何砢柯菏牁滒哥歌謌鴚哿河舸笴軻珂"}
    index = find_component_groups(char_to_prons, comp_to_char)

    assert len(index.groups) == 2
    group_1 = find(index.groups, lambda g: g.component == "官")
    assert group_1.pron_to_chars == {"kan": ["官", "棺", "館"], "foo": ["館"]}

    group_2 = find(index.groups, lambda g: g.component == "可")
    assert group_2.pron_to_chars == {"ka": ["何", "河"]}


def find(iterable, pred=None):
    return next(filter(pred, iterable))


def test_unique_readings():
    char_to_prons = {"館": ["kan"], "缶": ["kan"], "没": ["botu"]}
    index = find_component_groups(char_to_prons, {})
    assert index.unique_pron_to_char == {"botu": "没"}


def test_no_pron_chars():
    char_to_prons = {"峠": [], "畑": []}
    comp_to_chars = {"foo": "峠畑"}
    index = find_component_groups(char_to_prons, comp_to_chars)
    assert index.missing_pron_chars == set("峠畑")


def test_no_group_chars():
    char_to_prons = {"館": ["kan"], "缶": ["kan"]}
    index = find_component_groups(char_to_prons, {})
    assert index.no_comp_chars == set("館缶")
