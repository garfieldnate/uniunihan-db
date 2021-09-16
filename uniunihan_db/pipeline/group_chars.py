# Step 3: Group characters based on their phonetic components,
# and assign the resulting groups to larger groups based
# on their pronunciation regularity.
from collections import defaultdict

from uniunihan_db.component.group import ComponentGroup
from uniunihan_db.component.index import find_component_groups
from uniunihan_db.data.datasets import get_phonetic_components
from uniunihan_db.util import configure_logging

log = configure_logging(__name__)


KOKUJI = {"峠", "畑", "込", "匂", "枠"}


def group_chars_jp(char_data, out_dir):
    comp_to_char = get_phonetic_components()

    char_to_prons = {c: c_data["prons"] for c, c_data in char_data.items()}
    index = find_component_groups(char_to_prons, comp_to_char)
    # 国字 do not have phonetic characters, but can be usefully learned together
    index.groups.append(ComponentGroup("国字", {c: [] for c in KOKUJI}))
    index.no_comp_chars.difference_update(KOKUJI)
    index.log_diagnostics(log, out_dir)

    return __restructure_char_data(char_data, index)


def group_chars(char_data, out_dir):
    comp_to_char = get_phonetic_components()

    char_to_prons = {c: c_data.get("prons", {}) for c, c_data in char_data.items()}
    index = find_component_groups(char_to_prons, comp_to_char)
    index.log_diagnostics(log, out_dir)

    return __restructure_char_data(char_data, index)


def __restructure_char_data(char_data, index):
    output = defaultdict(dict)
    for g in index.groups:
        purity_groups = output[g.purity_type]
        purity_groups[g.component] = component_group = {"char_data": {}}
        for c in g.chars:
            component_group["char_data"][c] = char_data[c]
            component_group["num_exceptions"] = len(g.exceptions)

    return output


GROUP_CHARS = {"jp": group_chars_jp, "ko": group_chars, "zh-HK": group_chars}
