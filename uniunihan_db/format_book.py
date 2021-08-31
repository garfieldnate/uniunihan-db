from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
JINJA_ENV.trim_blocks = True
JINJA_ENV.lstrip_blocks = True
JINJA_ENV.keep_trailing_newline = False

COMPONENT_DATA = {
    "component": "予",
    "clusters": [
        {
            "豫": {
                "prons": [
                    {
                        "pron": "ヨ",
                        "vocab": {
                            "surface": "予定",
                            "pron": "ヨテイ",
                            "freq": 1719758,
                            "en": "(n,vs) plans/<wbr>arrangement/<wbr>schedule/<wbr>program/<wbr>programme/<wbr>expectation/<wbr>estimate/<wbr>(P)",
                        },
                        "non-joyo": False,
                    }
                ],
                "keyword": "in advance",
                "kun-yomi": "",
                "grade": "3",
                "strokes": "4",
                "new": "予",
                "old": "豫",
                "non-joyo": [],
                "readings": ["ヨ"],
                "cross_ref": {"中": 478, "韓": 12, "越": 924},
                "comment": "Cursive form became hiragana と; can't think of what else to say, so I'll just adding this long-winded sentence, or sentence fragment, rather, to fill in some space so that I can test multi-line comment display.",
                "id": 20,
            },
            "預": {
                "prons": [
                    {
                        "pron": "ヨ",
                        "vocab": {
                            "surface": "預金",
                            "pron": "ヨキン",
                            "freq": 28789,
                            "en": "(n,vs) deposit/<wbr>bank account/<wbr>(P)",
                        },
                        "non-joyo": False,
                    }
                ],
                "keyword": "deposit",
                "kun-yomi": "あず-ける|あず-かる",
                "grade": "5",
                "strokes": "13",
                "new": "預",
                "old": None,
                "non-joyo": [],
                "readings": ["ヨ"],
                "cross_ref": {"中": 478, "韓": 12, "越": 924},
                "comment": "Cursive form became hiragana と; can't think of what else to say, so I'll just adding this long-winded sentence, or sentence fragment, rather, to fill in some space so that I can test multi-line comment display.",
                "id": 20,
            },
        },
        {
            "序": {
                "prons": [
                    {
                        "pron": "ジョ",
                        "vocab": {
                            "surface": "序盤",
                            "pron": "ジョバン",
                            "freq": 65469,
                            "en": "(n) the opening(s) (e.g. in a game of go or chess)/<wbr>(P)",
                        },
                        "non-joyo": False,
                    }
                ],
                "keyword": "preface",
                "kun-yomi": "",
                "grade": "5",
                "strokes": "7",
                "new": "序",
                "old": None,
                "non-joyo": [],
                "readings": ["ジョ"],
                "cross_ref": {"中": 478, "韓": 12, "越": 924},
                "comment": "Cursive form became hiragana と; can't think of what else to say, so I'll just adding this long-winded sentence, or sentence fragment, rather, to fill in some space so that I can test multi-line comment display.",
                "id": 20,
            }
        },
        {
            "野": {
                "prons": [
                    {
                        "pron": "ヤ",
                        "vocab": {
                            "surface": "野球",
                            "pron": "ヤキュウ",
                            "freq": 852257,
                            "en": "(n) baseball/<wbr>(P)",
                        },
                        "non-joyo": False,
                    }
                ],
                "keyword": "field",
                "kun-yomi": "の",
                "grade": "2",
                "strokes": "11",
                "new": "野",
                "old": None,
                "non-joyo": [],
                "readings": ["ヤ"],
                "cross_ref": {"中": 478, "韓": 12, "越": 924},
                "comment": "Cursive form became hiragana と; can't think of what else to say, so I'll just adding this long-winded sentence, or sentence fragment, rather, to fill in some space so that I can test multi-line comment display.",
                "id": 20,
            }
        },
    ],
    "purity": 4,
    "chars": ["預", "野", "序", "豫"],
    "highest_vocab_freq": 1719758,
}

if __name__ == "__main__":
    jp_template = JINJA_ENV.get_template("jp_template.html.jinja")
    # TODO: replace `/` with `/<wbr>` in English definitions
    # TODO: ensure that ordering in maps is preserved
    result = jp_template.render(id=20, component=COMPONENT_DATA)

    print(result)
