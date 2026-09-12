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
LANG_TO_HAN = {"jp": "日", "zh": "中", "ko": "韓", "vi": "越", "vi_nom": "喃"}
LANG_ENGLISH = {
    "jp": "Japanese",
    "zh": "Mandarin",
    "ko": "Korean",
    "vi": "Vietnamese",
    "vi_nom": "Chữ Nôm",
}


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


def count_chars(data):
    """Number of distinct characters covered in one language's data (across all
    purity types, groups, and clusters)."""
    chars = set()
    for pg in data.values():
        for group in pg["groups"].values():
            for cluster in group["clusters"]:
                chars.update(cluster.keys())
    return len(chars)


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


def render_part_intro(jinja_env, lang, part_num, char_count, prev, next):
    part_intro_template = jinja_env.get_template("part_intro.html.jinja")
    intro = intros[lang].replace("{count}", f"{char_count:,}")
    result = part_intro_template.render(
        lang=lang, part_num=part_num, intro=intro, prev=prev, next=next
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
    "jp": (
        "<h1>Japanese (Jōyō kanji)</h1>"
        "<p>This part covers the <b>Jōyō kanji</b> (常用漢字) &mdash; the Japanese "
        "Ministry of Education's list of regular-use characters taught in schools "
        "({count} characters here). Each is grouped by phonetic component and "
        "ordered by the regularity of its <i>on-yomi</i> readings, shown with "
        "example vocabulary and cross-references to the same character in the "
        "other languages.</p>"
    ),
    "zh": (
        "<h1>Mandarin (Hong Kong commonly-used characters)</h1>"
        "<p>This part covers the characters of the Hong Kong <b>List of Graphemes "
        "of Commonly-Used Chinese Characters</b> (常用字字形表), selected via the "
        "Unihan <code>kHKGlyph</code> property ({count} characters here). "
        "Traditional glyphs are shown, with simplified variants where they differ, "
        "grouped by phonetic component and ordered by the regularity of their "
        "Mandarin readings, with example vocabulary from CC-CEDICT.</p>"
    ),
    "ko": (
        "<h1>Korean (Educational Hanja)</h1>"
        "<p>This part covers the <b>Basic Hanja for Educational Use</b> "
        "(교육용 기초 한자) &mdash; the South Korean Ministry of Education's list of "
        "{count} hanja taught in secondary school. Each is grouped by phonetic "
        "component and ordered by the regularity of its <i>hanja eum</i> reading, "
        "shown with example Sino-Korean vocabulary.</p>"
    ),
    "vi": (
        "<h1>Vietnamese (Hán-Việt)</h1>"
        "<p>A large share of the Vietnamese vocabulary was borrowed from Chinese "
        "and is known as <i>Hán-Việt</i> (Sino-Vietnamese). Although modern "
        "Vietnamese is written in the Latin-based <i>Quốc Ngữ</i> alphabet, each "
        "Sino-Vietnamese morpheme corresponds to a Chinese character "
        "(<i>chữ Hán</i> / <i>Hán tự</i>) with a regular reading &mdash; just as "
        "Japanese <i>on-yomi</i> and Korean <i>hanja</i> readings do. This part "
        "groups those characters by phonetic component and orders them by the "
        "frequency of their readings, so that recognizing one character helps you "
        "guess the reading of its relatives. There is no standard published "
        "Hán-Việt character list, so the inventory here is <b>{count} characters</b> "
        "reconstructed as exactly those used by the confirmed Sino-Vietnamese "
        "vocabulary (see below). Each character is shown with its "
        "Hán-Việt reading(s), an English keyword, and example Sino-Vietnamese "
        "words written in <i>Hán tự</i> with their Quốc Ngữ spelling.</p>"
        "<h2>Sources &amp; acknowledgements</h2>"
        "<p>Hán-Việt readings are from the Unicode <i>Unihan</i> database "
        "(<code>kVietnamese</code>) with the Unicode L2/23-251 corrections, "
        "supplemented by the WinVNKey Hán-Việt reading databases compiled by "
        "Thanh Sơn Lê and Học D. Ngô, which draw on the dictionaries of Thiều Chửu "
        "(<i>Hán Việt tự điển</i>, 1943), Nguyễn Quốc Hùng (<i>Hán Việt tân tự "
        "điển</i>, 1975), and Trần Văn Chánh (<i>Tự điển Hán Việt</i>, 2000). "
        "Word definitions are from <i>vnedict</i> by Paul Denisowski (CC BY 3.0). "
        "Character keywords are from Unihan; Han-character word forms are from "
        "CC-CEDICT (CC BY-SA). Word-frequency ordering uses the Leipzig Corpora "
        "Collection (Vietnamese) and the OpenSubtitles frequency list.</p>"
    ),
    "vi_nom": (
        "<h1>Chữ Nôm Appendix</h1>"
        "<p><i>Chữ Nôm</i> is the historical logographic script once used to write "
        "vernacular Vietnamese, alongside borrowed Chinese characters and many "
        "characters invented in Vietnam. Unlike the Hán-Việt part, which covers "
        "borrowed Sino-Vietnamese vocabulary, this appendix presents commonly "
        "attested Nôm characters &mdash; including native words such as pronouns "
        "and everyday verbs &mdash; grouped by phonetic component, with their Nôm "
        "readings and example usage ({count} characters here). The data is drawn "
        "from chunom.org.</p>"
    ),
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
            count_chars(data),
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
