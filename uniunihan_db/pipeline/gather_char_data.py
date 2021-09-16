# Step 1: gather data for characters to be learned
# Final structure: {char -> {char data}}

from uniunihan_db.data.datasets import get_historical_on_yomi, get_joyo, get_unihan
from uniunihan_db.data_paths import KO_ED_CHARS_FILE
from uniunihan_db.util import configure_logging, read_csv

log = configure_logging(__name__)


def load_char_data_jp():
    char_data = get_joyo()

    # enrich with historical kana spellings
    char_to_new_to_old_pron = get_historical_on_yomi()
    for c, new_to_old_pron in char_to_new_to_old_pron.items():
        if c_data := char_data.get(c):
            c_data["historical_pron"] = new_to_old_pron

    return char_data


def load_char_data_zh_hk():
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


LOAD_CHAR_DATA = {
    "jp": load_char_data_jp,
    "zh-HK": load_char_data_zh_hk,
    "ko": load_char_data_ko,
}
