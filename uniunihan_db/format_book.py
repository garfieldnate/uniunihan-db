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
ZH_HK_DATA_FILE = GENERATED_DIR / "regularities" / "zh-HK" / "final_output.json"
# OUTPUT_FILE = GENERATED_DIR / "book.html"


def __iter_chars(data):
    for groups in data.values():
        for g in groups:
            for cluster in g["clusters"]:
                for char, char_info in cluster.items():
                    yield char, char_info


def __index_first_pass(data):
    """Assigns character IDs and returns map from characters to char_info structures"""
    char_counter = 1
    index = {}
    for char, char_info in __iter_chars(data):
        char_info["id"] = char_counter
        index[char] = char_info
        char_counter += 1

    return index


def index(jp_data, zh_data):
    # assign indices to each character within a single language
    jp_index = __index_first_pass(jp_data)
    zh_index = __index_first_pass(zh_data)

    jp_missing_zh_chars = []
    for char, char_info in jp_index.items():
        if char in zh_index:
            if "cross_ref" not in char_info:
                char_info["cross_ref"] = {}
            char_info["cross_ref"]["中"] = zh_index[char]["id"]
        else:
            jp_missing_zh_chars.append(char)

    if jp_missing_zh_chars:
        log.warn(
            f"{len(jp_missing_zh_chars)} JP chars missing ZH indices: {jp_missing_zh_chars}"
        )

    zh_missing_jp_chars = []
    for char, char_info in zh_index.items():
        if char in jp_index:
            if "cross_ref" not in char_info:
                char_info["cross_ref"] = {}
            char_info["cross_ref"]["日"] = jp_index[char]["id"]
        else:
            zh_missing_jp_chars.append(char)

    if zh_missing_jp_chars:
        log.warn(
            f"{len(zh_missing_jp_chars)} zh-HK chars missing JP indices: {zh_missing_jp_chars}"
        )


def get_jinja_env():
    jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    jinja_env.trim_blocks = True
    jinja_env.lstrip_blocks = True
    jinja_env.keep_trailing_newline = False
    jinja_env.filters["kata2hira"] = kata2hira
    jinja_env.filters["break_slashes"] = break_slashes
    jinja_env.globals["purity_group_header"] = purity_group_header

    return jinja_env


def main():
    jinja_env = get_jinja_env()
    components_missing_data = set()
    total_components = 0

    def logged_component_header(component):
        header, no_info = component_header(component)
        nonlocal total_components
        total_components += 1
        if no_info:
            components_missing_data.add(component)
        return header

    jinja_env.globals["component_header"] = logged_component_header

    template = jinja_env.get_template("base.html.jinja")
    jp_data = json.load(JP_DATA_FILE.open("r"))
    zh_data = json.load(ZH_HK_DATA_FILE.open("r"))
    index(jp_data, zh_data)
    result = template.render(
        id=20,
        jp_data=jp_data,
        jp_intro="<h1>Japanese (joyo)</h1>",
        zh_hk_data=zh_data,
        zh_hk_intro="<h1>Mandarin (HSK)</h1>",
    )

    print(result)

    if components_missing_data:
        log.warn(
            f"{len(components_missing_data)}/{total_components} components missing Baxter/Sagart info: {components_missing_data}"
        )


if __name__ == "__main__":
    main()
