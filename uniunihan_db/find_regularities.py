import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

from .component_group import ComponentGroup, PurityType
from .util import GENERATED_DATA_DIR, INCLUDED_DATA_DIR, Aligner, configure_logging

log = configure_logging(__name__)

OUTPUT_DIR = GENERATED_DATA_DIR / "regularities"

# These three characters were collapsed in the sinjitai, and we don't have old spellings
# for vocab, so these have to be specified directly
JP_VOCAB_OVERRIDE = {
    "辯": {
        "ベン": [
            {
                "surface": "関西弁",
                "pron": "カンサイベン",
                "freq": 42413,
                "en": "(n) Kansai dialect",
            }
        ]
    },
    "辨": {
        "ベン": [
            {
                "surface": "弁当",
                "pron": "ベントウ",
                "freq": 524433,
                "en": "(n) bento (Japanese box lunch)",
            }
        ]
    },
    "瓣": {
        "ベン": [
            {
                "surface": "安全弁",
                "pron": "アンゼンベン",
                "freq": 566,
                "en": "(n) safety valve",
            }
        ]
    },
    "辦": {
        "ベン": [
            {
                "surface": "合弁会社",
                "pron": "ゴウベンガイシャ",
                "freq": 1374,
                "en": "(n) joint venture or concern",
            }
        ]
    },
    "辮": {
        "ベン": [
            {
                "surface": "弁髪",
                "pron": "ベンパツ",
                "freq": 414,
                "en": "(n) pigtail/queue",
            }
        ]
    },
}


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, ComponentGroup):
            return vars(obj)

        return json.JSONEncoder.default(self, obj)


def _read_joyo():
    log.info("Loading joyo data...")
    new_char_to_prons = {}
    old_char_to_prons = {}
    char_to_supplementary_info = {}
    with open(INCLUDED_DATA_DIR / "joyo.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            # number,new,old,radical,strokes,grade,year_added,English_meaning,on-yomi,kun-yomi
            supplementary_info = {
                "keyword": r["English_meaning"],
                "kun-yomi": r["kun-yomi"],
                "grade": r["grade"],
                "strokes": r["strokes"],
                "new": r["new"],
            }
            if r["old"]:
                supplementary_info["old"] = r["old"]
            readings = r["on-yomi"].split("|")
            # remove empty readings;
            # forget about parenthesized readings; focus on the main reading for pattern finding
            readings = [yomi for yomi in readings if yomi and "（" not in yomi]
            for c in r["new"]:
                new_char_to_prons[c] = readings
                char_to_supplementary_info[c] = supplementary_info
            # old glyph same as new glyph when missing
            for c in r["old"] or r["new"]:
                old_char_to_prons[c] = readings
                char_to_supplementary_info[c] = supplementary_info

    return old_char_to_prons, new_char_to_prons, char_to_supplementary_info


def _read_edict_freq(aligner):
    log.info("Loading EDICT frequency list...")
    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(GENERATED_DATA_DIR / "edict-freq.tsv") as f:
        num_words = 0
        for line in f.readlines():
            line = line.strip()
            surface, surface_normalized, pronunciation, english, frequency = line.split(
                "\t"
            )
            alignment = aligner.align(surface_normalized, pronunciation)
            if alignment:
                word = {
                    "surface": surface,
                    "pron": pronunciation,
                    "freq": int(frequency),
                    "en": english,
                }
                for c, pron in alignment.items():
                    char_to_pron_to_words[c][pron].append(word)
                num_words += 1
    return char_to_pron_to_words


def _read_historical_on_yomi():
    log.info("Loading historical on-yomi data...")
    char_to_new_to_old_pron = defaultdict(dict)
    with open(INCLUDED_DATA_DIR / "historical_kanji_on-yomi.csv") as f:
        # filter comments
        rows = csv.DictReader(filter(lambda row: row[0] != "#", f))
        for r in rows:
            modern = r["現代仮名遣い"]
            historical = r["字音仮名遣い"]
            chars = r["字"]
            for c in chars:
                char_to_new_to_old_pron[c][modern] = historical

    return char_to_new_to_old_pron


def _read_unihan():
    log.info("Loading unihan data...")
    # TODO: read path from constants file
    with open(GENERATED_DATA_DIR / "unihan.json") as f:
        unihan = json.load(f)

    return unihan


def _get_hk_ed_chars(unihan):
    def get_pron(info):
        # check all of the available fields in order of usefulness/accuracy
        if pron := info.get("kHanyuPinlu"):
            #             print('returning pinlu')
            return [p["phonetic"] for p in pron]
        elif pron := info.get("kXHC1983"):
            #             print('returning 1983')
            return [p["reading"] for p in pron]
        elif pron := info.get("kHanyuPinyin"):
            #             print('returning pinyin!')
            return [r for p in pron for r in p["readings"]]
        elif pron := info.get("kMandarin"):
            print("returning mandarin!")
            return pron["zh-Hans"]
        return []

    chars = {}
    for char, info in unihan.items():
        if "kGradeLevel" in info:
            prons = get_pron(info)
            chars[char] = prons
    return chars


def _read_phonetic_components():
    log.info("Loading phonetic components...")
    comp_to_char = {}
    with open(GENERATED_DATA_DIR / "components_to_chars.tsv") as f:
        rows = csv.DictReader(f, delimiter="\t")
        for r in rows:
            component = r["component"]
            chars = r["characters"]
            comp_to_char[component] = set(chars)

    return comp_to_char


def _read_jp_netflix(aligner, max_words=1_000_000):
    log.info("Loading Netflix frequency list...")
    char_to_pron_to_words = defaultdict(lambda: defaultdict(list))
    with open(INCLUDED_DATA_DIR / "jp_Netflix10K.txt") as f:
        num_words = 0
        for line in f.readlines():
            if not line.startswith("#"):
                line = line.strip()
                surface, pronunciation = line.split("\t")
                alignment = aligner.align(surface, pronunciation)
                if alignment:
                    for c, pron in alignment.items():
                        char_to_pron_to_words[c][pron].append(surface)
                    num_words += 1
                    if num_words == max_words:
                        break
    return char_to_pron_to_words


@dataclass
class Index:
    groups: List[ComponentGroup]
    # char -> pronuncitions
    char_to_prons: Dict[str, List[str]]
    # unique pronunciations and their corresponding character
    unique_pron_to_char: Dict[str, str]
    # characters without any pronunciations
    no_pron_chars: List[str]
    # characters with no pronunciation components
    no_comp_chars: Set[str]


def _index(char_to_prons, comp_to_char):
    # Group and classify characters by component
    chars_assigned_to_a_group = set()
    groups = []
    for component, chars in comp_to_char.items():
        # comp_to_char likely contains way more characters than we need
        chars = {c for c in chars if c in char_to_prons}
        if not chars:
            continue
        c2p = {c: prons for c, prons in char_to_prons.items() if c in chars}
        group = ComponentGroup(
            component,
            c2p,
        )
        groups.append(group)
        chars_assigned_to_a_group.update(chars)

    # Organize and sort the groups for easier inspection
    groups.sort(key=lambda g: (g.purity_type, -len(g.chars)))

    # find characters with no assigned group
    all_chars = set(char_to_prons.keys())
    chars_with_no_group = all_chars - chars_assigned_to_a_group

    # Find characters with no listed pronunciations
    no_pron_chars = set()
    for char, prons in char_to_prons.items():
        if not prons:
            no_pron_chars.add(char)
    no_pron_chars -= chars_with_no_group

    # get unique character readings
    pron_to_chars = defaultdict(set)
    for char, char_prons in char_to_prons.items():
        for char_pron in char_prons:
            pron_to_chars[char_pron].add(char)
    unique_readings = {
        pron: next(iter(chars))
        for pron, chars in pron_to_chars.items()
        if len(chars) == 1
    }

    return Index(
        groups,
        char_to_prons,
        unique_readings,
        no_pron_chars,
        chars_with_no_group,
    )


def _get_vocab_per_char_pron(char_to_prons, char_to_pron_to_words):
    """char_to_prons: dict character -> iterable of pronunciations
    char_to_pron_to_words: dict character -> pronunciation -> list
    of vocab sorted by frequency of use"""

    char_to_words = defaultdict(lambda: defaultdict(list))
    missing_words = []
    prons_to_move = defaultdict(list)
    for char, prons in char_to_prons.items():
        for p in prons:
            if word := char_to_pron_to_words.get(char, {}).get(p):
                char_to_words[char][p].extend(word)
                prons_to_move[char].append(p)
            else:
                missing_words.append(f"{char}/{p}")

    return char_to_words, missing_words


def _format_json(data):
    return json.dumps(
        data,
        cls=CustomJsonEncoder,
        ensure_ascii=False,
        indent=2,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--language",
        # sanity check against Heisig Volume II
        default="jp",
        choices=["jp", "zh-ZH", "zh-HK"],
        help="",
    )

    args = parser.parse_args()

    comp_to_char = _read_phonetic_components()

    if args.language == "jp":
        # old glyphs give a better matching with non-Japanese datasets,
        # and only new glyphs are matchable against modern word lists
        char_to_prons, new_char_to_prons, char_supplement = _read_joyo()
        aligner = Aligner(new_char_to_prons)
        # char_to_pron_to_vocab = _read_jp_netflix(aligner, 10000)
        char_to_pron_to_vocab = _read_edict_freq(aligner)
        char_to_words, missing_words = _get_vocab_per_char_pron(
            new_char_to_prons, char_to_pron_to_vocab
        )
        # convert to old glyphs to match char_to_prons
        old_char_to_words = {}
        for new_char, words in char_to_words.items():
            for c in char_supplement[new_char].get("old", []):
                old_char_to_words[c] = words
        char_to_words.update(old_char_to_words)

        char_to_words.update(JP_VOCAB_OVERRIDE)
        for c in JP_VOCAB_OVERRIDE:
            char_supplement[c]["old"] = c

        char_to_new_to_old_pron = _read_historical_on_yomi()
    elif args.language == "zh-HK":
        unihan = _read_unihan()
        char_to_prons = _get_hk_ed_chars(unihan)
        # print(char_to_prons)
        # get chars to prons from unihan where
    # elif args.language == 'zh-Zh':
    else:
        log.error(f"Cannot handle language {args.language} yet")
        exit()

    index = _index(char_to_prons, comp_to_char)

    purity_to_chars = defaultdict(set)
    purity_to_groups = defaultdict(int)
    exceptional_chars = set()
    for g in index.groups:
        purity_to_chars[g.purity_type].update(g.chars)
        purity_to_groups[g.purity_type] += 1
        exceptional_chars.update(g.exceptions.values())
    log.info(
        f"{len(index.no_comp_chars)} characters with no phonetic component data: {index.no_comp_chars}"
    )
    log.info(f"{len(index.no_pron_chars)} characters with no pronunciations")
    log.info(f"{len(index.unique_pron_to_char)} characters with unique readings")

    log.info(f"{len(index.groups)} total groups:")
    for purity_type in PurityType:
        log.info(
            f"    {purity_to_groups[purity_type]} {purity_type.name} groups ({len(purity_to_chars[purity_type])} characters)"
        )

    log.info(f"Missing words for {len(missing_words)} char/pron pairs")

    out_dir = OUTPUT_DIR / args.language
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "groups.json", "w") as f:
        f.write(_format_json(index.groups))
    with open(out_dir / "unique_readings.json", "w") as f:
        f.write(_format_json(index.unique_pron_to_char))
    with open(out_dir / "no_readings.json", "w") as f:
        f.write(_format_json(index.no_pron_chars))

    # FINAL OUTPUT
    log.info("Constructing final output...")
    final = []
    for g in index.groups:
        cluster_entries = []
        for cluster in g.get_char_presentation():
            cluster_entry = {}
            for c in cluster:
                pron_entries = []
                pron_to_vocab = sorted(char_to_words[c].items())
                if not pron_to_vocab:
                    raise ValueError(f"Missing pron_to_vocab for {c}")
                for pron, vocab_list in pron_to_vocab:
                    # find a multi-char word if possible
                    try:
                        vocab = next(
                            filter(lambda v: len(v["surface"]) > 1, vocab_list)
                        )
                    except StopIteration:
                        vocab = vocab_list[0]
                    pron_entry = {"pron": pron, "vocab": vocab}
                    if old_pron := char_to_new_to_old_pron.get(c, {}).get(pron):
                        pron_entry["historical"] = old_pron
                    pron_entries.append(pron_entry)

                c_entry = {"prons": pron_entries}
                c_entry.update(char_supplement[c])
                cluster_entry[c] = c_entry
            cluster_entries.append(cluster_entry)
        group_entry = {
            "component": g.component,
            "clusters": cluster_entries,
            "purity": g.purity_type.name,
        }
        final.append(group_entry)

    with open(out_dir / "final_output.json", "w") as f:
        f.write(_format_json(final))


if __name__ == "__main__":
    main()
