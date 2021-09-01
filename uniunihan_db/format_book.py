import json
from pathlib import Path

import jaconv
import jinja2
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
JINJA_ENV.trim_blocks = True
JINJA_ENV.lstrip_blocks = True
JINJA_ENV.keep_trailing_newline = False


def kata2hira(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return jaconv.kata2hira(s)


def break_slashes(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return s.replace("/", "/<wbr>")


JINJA_ENV.filters["kata2hira"] = kata2hira
JINJA_ENV.filters["break_slashes"] = break_slashes

GENERATED_DIR = Path(__file__).parent.parent / "data" / "generated"
JP_DATA_FILE = GENERATED_DIR / "regularities" / "jp" / "final_output.json"
# OUTPUT_FILE = GENERATED_DIR / "book.html"

if __name__ == "__main__":
    jp_template = JINJA_ENV.get_template("jp_template.html.jinja")
    jp_data = json.load(JP_DATA_FILE.open("r"))
    # TODO: generate indices
    result = jp_template.render(id=20, components=jp_data)

    print(result)
