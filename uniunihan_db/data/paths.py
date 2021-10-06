from pathlib import Path

PROJECT_DIR = Path(__file__).parents[2]

DATA_DIR = PROJECT_DIR / "data"

GENERATED_DATA_DIR = DATA_DIR / "generated"
GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)

PIPELINE_OUTPUT_DIR = GENERATED_DATA_DIR / "pipeline"

INCLUDED_DATA_DIR = DATA_DIR / "included"

TEST_CORPUS_DIR = PROJECT_DIR / "tests" / "corpus"

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_ZIP = GENERATED_DATA_DIR / "cedict_1_0_ts_utf-8_mdbg.zip"
CEDICT_DIR = CEDICT_ZIP.with_suffix("")
CEDICT_FILE = CEDICT_DIR / "cedict_ts.u8"

CHUNOM_CHAR_FILE = INCLUDED_DATA_DIR / "chunom_org" / "char_data.csv"
CHUNOM_VOCAB_FILE = INCLUDED_DATA_DIR / "chunom_org" / "standard-list.csv"

COMPONENT_OVERRIDE_FILE = INCLUDED_DATA_DIR / "manual_components.json"

EDICT_FREQ_URL = "http://ftp.monash.edu.au/pub/nihongo/edict-freq-20081002.tar.gz"
EDICT_FREQ_TARBALL = GENERATED_DATA_DIR / "edict-freq-20081002.tar.gz"
EDICT_FREQ_DIR = EDICT_FREQ_TARBALL.with_suffix("").with_suffix("")
EDICT_FREQ_FILE = EDICT_FREQ_DIR / "edict-freq-20081002"

JUN_DA_CHAR_FREQ_URL = (
    "https://lingua.mtsu.edu/chinese-computing/statistics/char/list.php"
)
JUN_DA_CHAR_FREQ_FILE = GENERATED_DATA_DIR / "jun_da_char.tsv"

KENGDIC_DATA_PACKAGE_URL = (
    "https://raw.githubusercontent.com/garfieldnate/kengdic/master/datapackage.json"
)

KO_ED_CHARS_FILE = INCLUDED_DATA_DIR / "kyoyuk_hanja.csv"

JP_VOCAB_OVERRIDE = INCLUDED_DATA_DIR / "jp_vocab_override.json"

LIB_HANGUL_URL = "https://github.com/libhangul/libhangul/archive/master.zip"
LIB_HANGUL_ZIP_FILE = GENERATED_DATA_DIR / "libhangul-master.zip"
LIB_HANGUL_DIR = LIB_HANGUL_ZIP_FILE.with_suffix("")

PHONETIC_COMPONENTS_FILE = GENERATED_DATA_DIR / "components_to_chars.tsv"

UNIHAN_FILE = GENERATED_DATA_DIR / "unihan.json"
