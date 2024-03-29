# Write the book HTML files. The book is organized into front matter,
# then language ("part"), then purity group. One page is written to introduce
# each part, and one page is written for each purity group in each language.

import json
from datetime import datetime
from pathlib import Path
from shutil import copy2

import jaconv
import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from loguru import logger as log

from uniunihan_db.collate import collate
from uniunihan_db.component.group import PurityType
from uniunihan_db.data.paths import GENERATED_DATA_DIR
from uniunihan_db.lingua.mandarin import pinyin_numbers_to_tone_marks
from uniunihan_db.util import configure_logging

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
INPUT_FILE = GENERATED_DATA_DIR / "collated" / "final.json"
OUTPUT_DIR = GENERATED_DATA_DIR / "book"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
LANG_TO_HAN = {"jp": "日", "zh": "中", "ko": "韓", "vi": "越"}
LANG_ENGLISH = {"jp": "Japanese", "zh": "Mandarin", "ko": "Korean", "vi": "Vietnamese"}


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


def __format_char_cross_ref(char_id):
    _, lang, purity_type, c_num = char_id.split("-")
    return (
        f'<a href="{lang}-{purity_type}.html#{char_id}">{LANG_TO_HAN[lang]}：{c_num}</a>'
    )


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
    jinja_env.filters["format_char_cross_ref"] = __format_char_cross_ref
    return jinja_env


def lang_intro_page_name(lang):
    return f"{lang}-intro.html"


def purity_group_page_name(lang, purity_type: int):
    return f"{lang}-{purity_type}.html"


def generate_toc(all_data):
    """Returns (toc, toc_html), where toc is a list of {title, file_name}
    entries corresponding to every page on the site, and toc_html the same
    but formatted for display in the front matter"""

    toc = [{"title": "Introduction", "file_name": "index.html"}]
    toc_html = ['<a href="#intro">Introduction</a><br/>']
    toc_html.append("<ol>")
    for lang, data in all_data.items():
        title = f"{LANG_ENGLISH[lang]} &mdash; Introduction"
        file_name = lang_intro_page_name(lang)
        toc.append(
            {
                "title": title,
                "file_name": file_name,
            }
        )
        toc_html.append(f'<li><a href="{file_name}">{title}</a></li>')
        toc_html.append("<ol>")
        for purity_type, pg in data.items():
            if not pg["groups"]:
                continue

            purity = PurityType(int(purity_type))
            file_name = purity_group_page_name(lang, purity_type)
            toc.append(
                {
                    "title": f"{LANG_ENGLISH[lang]} &mdash; "
                    f"{purity.display.title()} Groups",
                    "file_name": file_name,
                }
            )
            toc_html.append(
                f'<li><a href="{file_name}">{purity.display.title()} Groups</a></li>'
            )
        toc_html.append("</ol>")
    toc_html.append("</ol>")

    return toc, "\n".join(toc_html)


def render_front_matter(jinja_env, toc, toc_html):
    front_matter_template = jinja_env.get_template("front_matter.html.jinja")
    result = front_matter_template.render(
        book_title="Dictionary of Chinese Characters for Sinoxenic Language Learners",
        intro="TODO: intro text",
        toc=toc_html,
        prev=None,
        next=toc[1],
    )
    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(f"<!-- Generated from build_book.py, {datetime.now()} -->")
        f.write(result)


def render_part_intro(jinja_env, lang, part_num, prev, next):
    part_intro_template = jinja_env.get_template("part_intro.html.jinja")
    result = part_intro_template.render(
        lang=lang, part_num=part_num, intro=intros[lang], prev=prev, next=next
    )
    with open(OUTPUT_DIR / lang_intro_page_name(lang), "w") as f:
        f.write(f"<!-- Generated from build_book.py, {datetime.now()} -->")
        f.write(result)


def render_purity_group(jinja_env, lang, purity_type, pg, prev, next):
    purity_group_template = jinja_env.get_template("purity_group.html.jinja")
    result = purity_group_template.render(
        purity_type=purity_type,
        pg=pg,
        lang=lang,
        intro=intros[lang],
        prev=prev,
        next=next,
    )
    with open(OUTPUT_DIR / f"{lang}-{purity_type}.html", "w") as f:
        f.write(f"<!-- Generated from build_book.py, {datetime.now()} -->")
        f.write(result)


intros = {
    "jp": "<h1>Japanese (joyo)</h1><p>TODO: write introduction</p>",
    "zh": "<h1>Mandarin (HSK)</h1><p>TODO: write introduction</p>",
    "ko": "<h1>Korean (kyoyuk)</h1><p>TODO: write introduction</p>",
    "vi": "<h1>Vietnamese (chunom.org)</h1><p>TODO: write introduction</p>",
}


def build_book():
    if INPUT_FILE.exists():
        log.info(f"Loading collated data from {INPUT_FILE}...")
        all_data = json.load(INPUT_FILE.open())
    else:
        log.info("Re-generating collated data...")
        all_data = collate()

    toc, toc_html = generate_toc(all_data)
    jinja_env = get_jinja_env()

    render_front_matter(jinja_env, toc, toc_html)

    toc_index = 0
    for part_num, (lang, data) in enumerate(all_data.items()):
        log.info(f"Rendering {lang} files...")
        toc_index += 1

        render_part_intro(
            jinja_env,
            lang,
            part_num + 1,
            prev=toc[toc_index - 1],
            next=toc[toc_index + 1],
        )

        for purity_type, pg in data.items():
            if not pg["groups"]:
                continue
            toc_index += 1
            render_purity_group(
                jinja_env,
                lang,
                purity_type,
                pg,
                prev=toc[toc_index - 1],
                next=toc[toc_index + 1] if toc_index < len(toc) - 1 else None,
            )

    # copy CSS files
    for css_file in list((Path(__file__).parent.parent / "css").glob("*.css")):
        copy2(css_file, OUTPUT_DIR)


def main():
    configure_logging(__name__)
    build_book()


if __name__ == "__main__":
    main()
