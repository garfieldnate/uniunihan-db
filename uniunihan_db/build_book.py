import json
from datetime import datetime
from pathlib import Path
from shutil import copy2

import jaconv
import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from uniunihan_db.collate import collate
from uniunihan_db.component.group import PurityType
from uniunihan_db.data_paths import GENERATED_DATA_DIR
from uniunihan_db.lingua.mandarin import pinyin_numbers_to_tone_marks
from uniunihan_db.util import configure_logging

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
INPUT_FILE = GENERATED_DATA_DIR / "collated" / "final.json"
OUTPUT_FILE = GENERATED_DATA_DIR / "book" / "book.html"
OUTPUT_FILE.parent.mkdir(exist_ok=True, parents=True)
log = configure_logging(__name__)


# filters and functions for our jinja template
def __kata2hira(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return jaconv.kata2hira(s)


def __break_slashes(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return s.replace("/", "/<wbr>")


def __purity_group_header(s):
    purity = PurityType(int(s))
    return f"""<h1>{purity.display.title()} Groups</h1>
    <p class="purity-group-explainer">{purity.__doc__}</p>"""


def __format_id(s):
    return s.split("-")[-1]


LANG_TO_HAN = {"jp": "日", "zh": "中", "ko": "韓", "vi": "越"}


def __lang_to_han(s):
    return LANG_TO_HAN[s]


def get_jinja_env():
    jinja_env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR), undefined=StrictUndefined
    )
    jinja_env.trim_blocks = True
    jinja_env.lstrip_blocks = True
    jinja_env.keep_trailing_newline = False
    jinja_env.filters["kata2hira"] = __kata2hira
    jinja_env.filters["break_slashes"] = __break_slashes
    jinja_env.globals["purity_group_header"] = __purity_group_header
    jinja_env.filters["num2diacritic"] = pinyin_numbers_to_tone_marks
    jinja_env.filters["format_id"] = __format_id
    jinja_env.filters["lang_to_han"] = __lang_to_han
    return jinja_env


def build_book():
    if INPUT_FILE.exists():
        log.info(f"Loading collated data from {INPUT_FILE}...")
        all_data = json.load(INPUT_FILE.open())
    else:
        log.info("Re-generating collated data...")
        all_data = collate()

    jinja_env = get_jinja_env()
    template = jinja_env.get_template("base.html.jinja")
    result = template.render(
        all_data=all_data,
        intros={
            "jp": "<h1>Japanese (joyo)</h1>",
            "zh": "<h1>Mandarin (HSK)</h1>",
            "ko": "<h1>Korean (kyoyuk)</h1>",
        },
    )

    # write resulting HTML file
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"<!-- Generated from build_book.py, {datetime.now()} -->")
        f.write(result)

    # copy CSS files
    out_dir = OUTPUT_FILE.parent
    for css_file in list(TEMPLATES_DIR.glob("*.css")):
        copy2(css_file, out_dir)
    for css_file in list((Path(__file__).parent.parent / "vendor").glob("*.css")):
        copy2(css_file, out_dir)
