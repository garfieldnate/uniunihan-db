import dataclasses
from collections import defaultdict

# allows commenting lines with # or //
import commentjson as json
from unihan_etl.process import export_json

from uniunihan_db.data.datasets import get_unihan, get_variants, get_ytenx_rhymes
from uniunihan_db.data_paths import (
    INCLUDED_DATA_DIR,
    PHONETIC_COMPONENTS_FILE,
    UNIHAN_AUGMENTATION_FILE,
)

from .lingua import japanese, mandarin
from .util import configure_logging

log = configure_logging(__name__)


def write_phonetic_components():
    """Extract and augment the phonetic component data in ytenx"""

    if (
        PHONETIC_COMPONENTS_FILE.exists()
        and PHONETIC_COMPONENTS_FILE.stat().st_size > 0
    ):
        log.info(f"{PHONETIC_COMPONENTS_FILE.name} already exists; skipping creation")
        return

    log.info("Determining phonetic components...")

    ytenx_rhyme_data = get_ytenx_rhymes()
    char_to_component = {char: info[0]["聲符"] for char, info in ytenx_rhyme_data.items()}

    with open(INCLUDED_DATA_DIR / "manual_components.json") as f:
        extra_char_to_components = json.load(f)
        char_to_component.update(extra_char_to_components)

    variants = get_variants()
    log.info("  Addding phonetic components for variants...")
    variant_to_component = {}
    for char in char_to_component:
        for c in variants.get(char, []):
            if c not in char_to_component:
                variant_to_component[c] = char_to_component[char]
    char_to_component.update(variant_to_component)

    # group by component to make it easier to use
    component_to_chars = defaultdict(list)
    for char, component in sorted(char_to_component.items()):
        component_to_chars[component].append(char)

    log.info(f"  Writing phonetic components to {PHONETIC_COMPONENTS_FILE}")
    with open(PHONETIC_COMPONENTS_FILE, "w") as f:
        f.write("component\tcharacters\n")
        for component, chars in component_to_chars.items():
            chars = "".join(chars)
            f.write(f"{component}\t{chars}\n")
    log.info(f"  Wrote {len(char_to_component)} character/component pairs")

    return char_to_component


def expand_unihan():
    """Expand Unihan DB with the following data:
    * Kana and IME spellings for Japanese on'yomi
    * On'yomi and Mandarin syllable analyses (for testing purposes)
    * Reverse compatibility variant references"""

    unihan = get_unihan()

    log.info("Expanding Unihan data...")
    new_data = {}
    reverse_compatibilities = defaultdict(list)
    for key, entry in unihan.items():
        new_data[key] = {}
        if on_list := entry.get("kJapaneseOn"):
            kana_list = []
            ime_list = []
            parsed_list = []
            for on in on_list:
                kana = japanese.alpha_to_kana(on)
                ime = japanese.kana_to_alpha(kana)
                try:
                    han_syl = japanese.parse_han_syllable(ime)
                    han_syl = dataclasses.asdict(han_syl)
                    parsed_list.append(han_syl)
                except TypeError:
                    log.warn(
                        f"  {entry['char']}/{on}/romanization={ime}: Failed to parse Han syllable!"
                    )
                    parsed_list.append(None)
                kana_list.append(kana)
                ime_list.append(ime)
            new_data[key] |= {
                "kJapaneseOn_kana": kana_list,
                "kJapaneseOn_ime": ime_list,
                "kJapaneseOn_parsed": parsed_list,
            }
        if pinyin_dict := entry.get("kMandarin"):
            parsed_dict = {}
            for k, v in pinyin_dict.items():
                try:
                    syl = mandarin.parse_syllable(v)
                    syl = dataclasses.asdict(syl)
                    parsed_dict[k] = syl
                except TypeError:
                    log.warn(
                        f"{entry['char']}/{k}={v}: Failed to parse pinyin syllable!"
                    )
                    parsed_dict[k] = None
            new_data[key] |= {"kMandarin_parsed": parsed_dict}
        for field_name in ["kCompatibilityVariant", "kJinmeiyoKanji", "kJoyoKanji"]:
            if comp_variant := entry.get(field_name):
                if type(comp_variant) != list:
                    comp_variant = [comp_variant]
                for v in comp_variant:
                    reverse_compatibilities[v].extend(key)

    for key, variants in reverse_compatibilities.items():
        new_data[key]["kReverseCompatibilityVariants"] = variants

    log.info(f"  Writing Unihan augmentations to {UNIHAN_AUGMENTATION_FILE.name}...")
    export_json(new_data, UNIHAN_AUGMENTATION_FILE)


def main():
    write_phonetic_components()
    # expand_unihan()


if __name__ == "__main__":
    main()
