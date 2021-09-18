import argparse

from uniunihan_db.data_paths import PIPELINE_OUTPUT_DIR
from uniunihan_db.util import configure_logging, format_json

from .add_char_prons import ADD_PRONUNCIATIONS
from .gather_char_data import LOAD_CHAR_DATA
from .group_chars import GROUP_CHARS
from .oc_mc import OC_MC
from .organize import ORGANIZE_DATA
from .select_vocab import SELECT_VOCAB

log = configure_logging(__name__)

OUTPUT_DIR = PIPELINE_OUTPUT_DIR


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
    out_dir = OUTPUT_DIR / args.language
    out_dir.mkdir(parents=True, exist_ok=True)

    char_data = LOAD_CHAR_DATA[args.language]()
    log.info(f"Loaded data for {len(char_data)} characters")
    char_data = ADD_PRONUNCIATIONS[args.language](char_data, out_dir)
    all_data = GROUP_CHARS[args.language](char_data, out_dir)
    all_data = OC_MC[args.language](all_data, out_dir)
    all_data = SELECT_VOCAB[args.language](all_data, out_dir)
    all_data = ORGANIZE_DATA[args.language](all_data)

    final_out_file = out_dir / "all_data.json"
    with open(final_out_file, "w") as f:
        f.write(format_json(all_data))
    log.info(f"Wrote output to {final_out_file}")
