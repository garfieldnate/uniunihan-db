import json
from pathlib import Path

import jaconv
import jinja2
from component_group import PurityType
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
JINJA_ENV.trim_blocks = True
JINJA_ENV.lstrip_blocks = True
JINJA_ENV.keep_trailing_newline = False


# filters and functions for our jinja template
def kata2hira(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return jaconv.kata2hira(s)


def break_slashes(s, default_value=""):
    if isinstance(s, jinja2.runtime.Undefined):
        return default_value
    return s.replace("/", "/<wbr>")


def purity_group_header(s):
    purity = PurityType(int(s))
    return f"""<h1>{purity.display.title()} Groups</h1>
    <p class="purity-group-explainer">{purity.__doc__}</p>"""


JINJA_ENV.filters["kata2hira"] = kata2hira
JINJA_ENV.filters["break_slashes"] = break_slashes
JINJA_ENV.globals["purity_group_header"] = purity_group_header

GENERATED_DIR = Path(__file__).parent.parent / "data" / "generated"
JP_DATA_FILE = GENERATED_DIR / "regularities" / "jp" / "final_output.json"
# OUTPUT_FILE = GENERATED_DIR / "book.html"


def index(data):
    # assign indices to each character within a single language
    counter = 1
    for groups in data.values():
        for g in groups:
            for cluster in g["clusters"]:
                for char, char_info in cluster.items():
                    char_info["id"] = counter
                    counter += 1


if __name__ == "__main__":
    jp_template = JINJA_ENV.get_template("jp_template.html.jinja")
    jp_data = json.load(JP_DATA_FILE.open("r"))
    index(jp_data)
    # TODO: generate indices
    result = jp_template.render(id=20, purity_groups=jp_data)

    print(result)
