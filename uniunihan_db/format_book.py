from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
JINJA_ENV.trim_blocks = True
JINJA_ENV.lstrip_blocks = True
JINJA_ENV.keep_trailing_newline = False

CHAR_DATA = {
    "prons": [
        {
            "pron": "ケイ",
            "vocab": {
                "surface": "兄弟",
                "pron": "ケイテイ",
                "freq": 354349,
                "en": "(n) siblings/brothers and sisters",
            },
            "non-joyo": False,
        },
        {
            "pron": "キョウ",
            "vocab": {
                "surface": "兄弟",
                "pron": "キョウダイ",
                "freq": 354349,
                "en": "(n) siblings/brothers and sisters/(P)",
            },
            "non-joyo": True,
            "historical": "きゃう",
        },
    ],
    "keyword": "older brother",
    "kun-yomi": "あに",
    "grade": "2",
    "strokes": "5",
    "new": "兄",
    "old": None,
    "non-joyo": ["キョウ"],
    "readings": ["キョウ", "ケイ"],
    "cross_ref": {"Mandarin": 478, "Korean": 12, "Vietnamese": 924},
}

if __name__ == "__main__":
    jp_template = JINJA_ENV.get_template("jp_template.html.jinja")
    result = jp_template.render(id=20, char=CHAR_DATA)
    # "<br />".join([v["surface"] for v in char.vocab])
    print(result)
