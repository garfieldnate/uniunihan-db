import argparse

from uniunihan_db.data_paths import PIPELINE_OUTPUT_DIR
from uniunihan_db.pipeline.add_char_prons import ADD_PRONUNCIATIONS
from uniunihan_db.pipeline.gather_char_data import LOAD_CHAR_DATA
from uniunihan_db.pipeline.group_chars import GROUP_CHARS
from uniunihan_db.pipeline.select_vocab import SELECT_VOCAB
from uniunihan_db.util import configure_logging, format_json

log = configure_logging(__name__)

OUTPUT_DIR = PIPELINE_OUTPUT_DIR
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

    char_data = LOAD_CHAR_DATA[args.language]()
    log.info(f"Loaded data for {len(char_data)} characters")
    char_data = ADD_PRONUNCIATIONS[args.language](char_data)
    purity_groups = GROUP_CHARS[args.language](char_data, OUTPUT_DIR)
    all_data = SELECT_VOCAB[args.language](purity_groups, OUTPUT_DIR)

    out_file = OUTPUT_DIR / f"{args.language}.json"
    with open(out_file, "w") as f:
        f.write(format_json(all_data))
    log.info(f"Wrote output to {out_file}")
