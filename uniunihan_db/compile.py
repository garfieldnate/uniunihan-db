from collections import OrderedDict, defaultdict
from typing import Any, MutableMapping

from uniunihan_db.component.group import PurityType
from uniunihan_db.component.index import ComponentGroupIndex
from uniunihan_db.data.types import Char2Pron2Words
from uniunihan_db.util import configure_logging

log = configure_logging(__name__)


# sort characters by frequency of most frequent vocab (if available), then by character
def cluster_sort_key(cluster_kv):
    k1 = 0
    if prons := cluster_kv[1]["prons"]:
        k1 = -prons[0]["vocab"].frequency
    # fallback to sorting by character
    # TODO: use size of cluster?
    k2 = cluster_kv[0]

    return (k1, k2)


def compile_final_output(
    index: ComponentGroupIndex,
    char_to_pron_to_vocab: Char2Pron2Words,
    pron_entry_sort_key,
    augment,
):
    log.info("Constructing final output...")
    purity_2_groups: MutableMapping[PurityType, Any] = defaultdict(list)
    for g in index.groups:
        # keep track of highest frequency vocab used in the group
        highest_freq = -1
        cluster_entries = []
        for cluster in g.get_ordered_clusters():
            cluster_entry = {}
            for c in cluster:
                pron_entries = []
                for pron, vocab_list in char_to_pron_to_vocab[c].items():
                    if vocab_list:
                        # find a multi-char word if possible
                        try:
                            vocab = next(
                                filter(lambda v: len(v.surface) > 1, vocab_list)
                            )
                        except StopIteration:
                            vocab = vocab_list[0]
                        highest_freq = max(highest_freq, vocab.frequency)
                    else:
                        pass  # TODO
                    pron_entry = {
                        "pron": pron,
                        "vocab": vocab,
                    }
                    pron_entries.append(pron_entry)
                c_entry = {"prons": pron_entries}
                augment(c, c_entry)
                pron_entries.sort(key=pron_entry_sort_key)
                cluster_entry[c] = c_entry

            cluster_entry = OrderedDict(
                sorted(cluster_entry.items(), key=cluster_sort_key)
            )
            cluster_entries.append(cluster_entry)

        group_entry = {
            "component": g.component,
            "clusters": cluster_entries,
            "purity": g.purity_type,
            "chars": g.chars,
            "highest_vocab_freq": highest_freq,
        }
        purity_2_groups[g.purity_type].append(group_entry)

    for groups in purity_2_groups.values():
        # Sort the entries by purity type, then number of characters descending, then frequency
        # of most frequent word descending, and final orthographically by component
        groups.sort(
            key=lambda g: (
                -len(g["chars"]),
                -g["highest_vocab_freq"],
                g["component"],
            )
        )

    # sort keys by purity integer value
    final = OrderedDict(sorted(purity_2_groups.items(), key=lambda kv: kv[0]))
    return final
