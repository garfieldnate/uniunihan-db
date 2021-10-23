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
                            "埼": {"ID": "c-foo-1"},
                            "奇": {"ID": "c-foo-2"},
                            "寄": {"ID": "c-foo-3"},
                            "崎": {"ID": "c-foo-4"},
                            "騎": {"ID": "c-foo-5"},
                        },
                        {"椅": {"ID": "c-foo-6"}},
                    ],
                    "ID": "g-foo-1",
                },
                "僉": {
                    "clusters": [
                        {
                            "儉": {"ID": "c-foo-7"},
                            "劍": {"ID": "c-foo-8"},
                            "檢": {"ID": "c-foo-9"},
                            "險": {"ID": "c-foo-10"},
                            "驗": {"ID": "c-foo-11"},
                        }
                    ],
                    "ID": "g-foo-2",
                },
            }
        },
        "3": {
            "groups": {
                "我": {
                    "clusters": [
                        {
                            "儀": {"ID": "c-foo-12"},
                            "犧": {"ID": "c-foo-13"},
                            "義": {"ID": "c-foo-14"},
                            "議": {"ID": "c-foo-15"},
                        },
                        {"我": {"ID": "c-foo-16"}, "餓": {"ID": "c-foo-17"}},
                    ],
                    "ID": "g-foo-3",
                },
                "次": {
                    "clusters": [
                        {
                            "姿": {"ID": "c-foo-18"},
                            "恣": {"ID": "c-foo-19"},
                            "次": {"ID": "c-foo-20"},
                            "茨": {"ID": "c-foo-21"},
                            "諮": {"ID": "c-foo-22"},
                            "資": {"ID": "c-foo-23"},
                        }
                    ],
                    "ID": "g-foo-4",
                },
            }
        },
    }
