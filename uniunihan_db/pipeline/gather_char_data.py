# Step 1: gather data for characters to be learned

import argparse

from uniunihan_db.data.datasets import get_historical_on_yomi, get_joyo, get_unihan
from uniunihan_db.data_paths import KO_ED_CHARS_FILE, PIPELINE_OUTPUT_DIR
from uniunihan_db.util import configure_logging, format_json, read_csv

log = configure_logging(__name__)

OUTPUT_DIR = PIPELINE_OUTPUT_DIR / "chars"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--language",
        default="jp",
        choices=["jp", "ko", "zh-HK"],
        help="",
    )

    args = parser.parse_args()

    if args.language == "jp":
        char_data = load_char_data_jp()
    elif args.language == "zh-HK":
        char_data = load_char_data_zh_hk()
    elif args.language == "ko":
        char_data = load_char_data_ko()
    else:
        log.error(f"Cannot handle language {args.language} (yet)")
        exit()

    out_file = OUTPUT_DIR / f"{args.language}.json"
    log.info(f"Writing data for {len(char_data)} characters to {out_file}")
    with open(out_file, "w") as f:
        f.write(format_json(char_data))


def load_char_data_jp():
    joyo = get_joyo()

    # enrich with historical kana spellings
    char_to_new_to_old_pron = get_historical_on_yomi()
    for c, new_to_old_pron in char_to_new_to_old_pron.items():
        if c_data := joyo.char_to_supplementary_info.get(c):
            c_data["historical_pron"] = new_to_old_pron

    return joyo.char_to_supplementary_info


def load_char_data_zh_hk():
    # TODO: returns 4825 characters; expected 4759
    unihan = get_unihan()
    char_data = {}
    for char, info in unihan.items():
        if "kHKGlyph" in info:
            char_data[char] = {"trad": char}
            if c_def := info.get("kDefinition"):
                char_data[char]["english"] = c_def
            if simplified := unihan[char].get("kSimplifiedVariant", []):
                char_data[char]["simp"] = simplified

    return char_data


def load_char_data_ko():
    char_data = {}

    reader = read_csv(KO_ED_CHARS_FILE)
    for row in reader:
        char = row["char"]
        del row["char"]
        char_data[char] = row

    return char_data


if __name__ == "__main__":
    main()
