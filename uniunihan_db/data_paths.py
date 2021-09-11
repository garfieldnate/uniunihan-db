from pathlib import Path

PROJECT_DIR = Path(__file__).parents[1]

DATA_DIR = PROJECT_DIR / "data"

GENERATED_DATA_DIR = DATA_DIR / "generated"
GENERATED_DATA_DIR.mkdir(exist_ok=True)

INCLUDED_DATA_DIR = DATA_DIR / "included"

TEST_CORPUS_DIR = PROJECT_DIR / "tests" / "corpus"

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_ZIP = GENERATED_DATA_DIR / "cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_DIR = CEDICT_ZIP.with_suffix("")
CEDICT_FILE = CEDICT_DIR / "cedict_ts.u8"

EDICT_FREQ_URL = "http://ftp.monash.edu.au/pub/nihongo/edict-freq-20081002.tar.gz"
EDICT_FREQ_TARBALL = GENERATED_DATA_DIR / "edict-freq-20081002.tar.gz"
EDICT_FREQ_DIR = EDICT_FREQ_TARBALL.with_suffix("").with_suffix("")
EDICT_FREQ_FILE = EDICT_FREQ_DIR / "edict-freq-20081002"

JUN_DA_CHAR_FREQ_URL = (
    "https://lingua.mtsu.edu/chinese-computing/statistics/char/list.php"
)
JUN_DA_CHAR_FREQ_FILE = GENERATED_DATA_DIR / "jun_da_char.tsv"

HK_ED_CHARS_FILE = GENERATED_DATA_DIR / "hk_ed_chars.json"
KO_ED_CHARS_FILE = GENERATED_DATA_DIR / "ko_ed_chars.json"

JP_VOCAB_OVERRIDE = INCLUDED_DATA_DIR / "jp_vocab_override.json"

LIB_HANGUL_URL = "https://github.com/libhangul/libhangul/archive/master.zip"
LIB_HANGUL_ZIP_FILE = GENERATED_DATA_DIR / "libhangul-master.zip"
LIB_HANGUL_DIR = LIB_HANGUL_ZIP_FILE.with_suffix("")

PHONETIC_COMPONENTS_FILE = GENERATED_DATA_DIR / "components_to_chars.tsv"

UNIHAN_FILE = GENERATED_DATA_DIR / "unihan.json"
UNIHAN_AUGMENTATION_FILE = GENERATED_DATA_DIR / "unihan_augmentation.json"