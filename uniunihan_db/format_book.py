import json
from pathlib import Path

import jaconv
import jinja2
from jinja2 import Environment, FileSystemLoader

from uniunihan_db.util import configure_logging, read_baxter_sagart

from .component_group import PurityType

BAXTER_SAGART_DATA = read_baxter_sagart()

log = configure_logging(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


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


def component_header(component):
    infos = BAXTER_SAGART_DATA[component]
    requires_numbers = len(infos) > 1
    output = ['<div class="component-header">']
    output.append(f"<h2>{component}</h2>")
    for i, info in enumerate(infos):
        output.append('<div class="component-etymology-section">')
        num_text = f"{i+1}: " if requires_numbers else ""
        output.append(
            f"""
            <p class="component-keyword">{num_text}{info['keyword']}</p>
            <p class="component-pronunciation"><em>Middle Chinese:</em> {info['middle_chinese']}</p>
            <p class="component-pronunciation"><em>Old Chinese:</em> {info['old_chinese']}</p>
        </div>
        """
        )
    output.append("</div>")
    return "\n".join(output), len(infos) == 0


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


def main():
    jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    jinja_env.trim_blocks = True
    jinja_env.lstrip_blocks = True
    jinja_env.keep_trailing_newline = False
    jinja_env.filters["kata2hira"] = kata2hira
    jinja_env.filters["break_slashes"] = break_slashes
    jinja_env.globals["purity_group_header"] = purity_group_header

    components_missing_data = []
    total_components = 0

    def logged_component_header(component):
        header, no_info = component_header(component)
        nonlocal total_components
        total_components += 1
        if no_info:
            components_missing_data.append(component)
        return header

    jinja_env.globals["component_header"] = logged_component_header

    jp_template = jinja_env.get_template("jp_template.html.jinja")
    jp_data = json.load(JP_DATA_FILE.open("r"))
    index(jp_data)
    # TODO: generate cross-references
    result = jp_template.render(id=20, purity_groups=jp_data)

    print(result)

    if components_missing_data:
        log.warn(
            f"{len(components_missing_data)}/{total_components} components missing Baxter/Sagart info: {components_missing_data}"
        )


if __name__ == "__main__":
    main()
