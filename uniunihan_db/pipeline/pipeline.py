import argparse

from uniunihan_db.data_paths import PIPELINE_OUTPUT_DIR
from uniunihan_db.pipeline.add_char_prons import ADD_PRONUNCIATIONS
from uniunihan_db.pipeline.gather_char_data import LOAD_CHAR_DATA
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
    char_data = ADD_PRONUNCIATIONS[args.language](char_data)

    out_file = OUTPUT_DIR / f"{args.language}.json"
    log.info(f"Writing data for {len(char_data)} characters to {out_file}")
    with open(out_file, "w") as f:
        f.write(format_json(char_data))
