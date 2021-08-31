from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
JINJA_ENV.trim_blocks = True
JINJA_ENV.lstrip_blocks = True
JINJA_ENV.keep_trailing_newline = False

CLUSTER_DATA = {
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
}

if __name__ == "__main__":
    jp_template = JINJA_ENV.get_template("jp_template.html.jinja")
    # TODO: replace `/` with `/<wbr>` in English definitions
    # TODO: ensure that ordering in maps is preserved
    result = jp_template.render(id=20, cluster=CLUSTER_DATA)

    print(result)
