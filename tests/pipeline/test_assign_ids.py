from typing import Any, Mapping

from uniunihan_db.pipeline.assign_ids import assign_ids


def test_assign_ids():
    test_data: Mapping[str, Any] = {
        "2": {
            "groups": {
                "奇": {
                    "clusters": [
                        {"埼": {}, "奇": {}, "寄": {}, "崎": {}, "騎": {}},
                        {"椅": {}},
                    ]
                },
                "僉": {
                    "clusters": [{"儉": {}, "劍": {}, "檢": {}, "險": {}, "驗": {}}],
                },
            }
        },
        "3": {
            "groups": {
                "我": {
                    "clusters": [
                        {"儀": {}, "犧": {}, "義": {}, "議": {}},
                        {"我": {}, "餓": {}},
                    ]
                },
                "次": {
                    "clusters": [
                        {"姿": {}, "恣": {}, "次": {}, "茨": {}, "諮": {}, "資": {}}
                    ],
                },
            }
        },
    }

    assign_ids("foo", test_data)

    assert test_data == {
        "2": {
            "groups": {
                "奇": {
                    "clusters": [
                        {
                            "埼": {"ID": "c-foo-2-1"},
                            "奇": {"ID": "c-foo-2-2"},
                            "寄": {"ID": "c-foo-2-3"},
                            "崎": {"ID": "c-foo-2-4"},
                            "騎": {"ID": "c-foo-2-5"},
                        },
                        {"椅": {"ID": "c-foo-2-6"}},
                    ],
                    "ID": "g-foo-2-1",
                },
                "僉": {
                    "clusters": [
                        {
                            "儉": {"ID": "c-foo-2-7"},
                            "劍": {"ID": "c-foo-2-8"},
                            "檢": {"ID": "c-foo-2-9"},
                            "險": {"ID": "c-foo-2-10"},
                            "驗": {"ID": "c-foo-2-11"},
                        }
                    ],
                    "ID": "g-foo-2-2",
                },
            }
        },
        "3": {
            "groups": {
                "我": {
                    "clusters": [
                        {
                            "儀": {"ID": "c-foo-3-12"},
                            "犧": {"ID": "c-foo-3-13"},
                            "義": {"ID": "c-foo-3-14"},
                            "議": {"ID": "c-foo-3-15"},
                        },
                        {"我": {"ID": "c-foo-3-16"}, "餓": {"ID": "c-foo-3-17"}},
                    ],
                    "ID": "g-foo-3-3",
                },
                "次": {
                    "clusters": [
                        {
                            "姿": {"ID": "c-foo-3-18"},
                            "恣": {"ID": "c-foo-3-19"},
                            "次": {"ID": "c-foo-3-20"},
                            "茨": {"ID": "c-foo-3-21"},
                            "諮": {"ID": "c-foo-3-22"},
                            "資": {"ID": "c-foo-3-23"},
                        }
                    ],
                    "ID": "g-foo-3-4",
                },
            }
        },
    }
