from loguru import logger as log

from uniunihan_db.data.paths import GENERATED_DATA_DIR
from uniunihan_db.util import configure_logging, format_json

from .pipeline.runner import LANGUAGES, run_pipeline

OUTPUT_DIR = GENERATED_DATA_DIR / "collated"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# TODO: cross-ref components, too


def __iter_chars(data):
    for purity_group in data.values():
        for group in purity_group["groups"].values():
            for cluster in group["clusters"]:
                for c, char_data in cluster.items():
                    yield c, char_data


def __get_char_index(data, get_variants):
    """Returns a map from characters to char_info structures"""

    char_index = {}

    def add_to_char_index(char):
        if char in char_index:
            log.warning(
                f"{char} already in index! Conflicting IDs: {char_index[char]['ID']}, {char_info['ID']}"
            )
        else:
            char_index[char] = char_info

    for char, char_info in __iter_chars(data):
        add_to_char_index(char)
        for variant in get_variants(char, char_info):
            add_to_char_index(variant)
    return char_index


def __get_variants_jp(char, char_info):
    # Besides the 5 characters collapsed to 弁, there is a
    # 1-1 mapping between 新字体 and 旧字体, so these variants
    # are safe to use
    if char_info["new"] != char and char_info["new"] != "弁":
        return char_info["new"]
    return []


def __get_variants_ko(char, char_info):
    if variant := char_info["variant"]:
        return variant
    return []


def __get_variants_zh(char, char_info):
    # if simp := char_info.get("simp"):
    #     return simp
    return []


__get_variants = {
    "jp": __get_variants_jp,
    "ko": __get_variants_ko,
    "zh": __get_variants_zh,
}


def collate():
    all_data = {lang: run_pipeline(lang) for lang in LANGUAGES}
    all_char_indices = {
        lang: __get_char_index(all_data[lang], __get_variants[lang])
        for lang in LANGUAGES
    }
    __cross_reference(all_char_indices)
    with open(OUTPUT_DIR / "final.json", "w") as f:
        f.write(format_json(all_data))

    return all_data


def __cross_reference(all_indices):
    duplicates = 0
    for lang1 in all_indices.keys():
        for lang2, index2 in all_indices.items():
            if lang1 == lang2:
                continue
            for char1, char_info1 in all_indices[lang1].items():
                cross_ref1 = char_info1.setdefault("cross_ref", {})
                if char_info2 := index2.get(char1):
                    if lang2 in cross_ref1:
                        log.debug(
                            f"Character {char1} already linked from {lang1} to {lang2} (IDs: {char_info2['ID']}, {cross_ref1[lang2]})"
                        )
                        duplicates += 1
                    else:
                        cross_ref1[lang2] = char_info2["ID"]
    log.warning(
        f"{duplicates} character entries with multiple link possibilities in another language"
    )


def main():
    configure_logging()
    collate()


if __name__ == "__main__":
    main()
