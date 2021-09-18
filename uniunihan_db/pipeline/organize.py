# Create the final book structure (for one language) by organizing the characters
# by purity level, component gruop, and cluster, and by sorting everything so that
# the most useful, general information comes first.


from uniunihan_db.component.group import PurityType
from uniunihan_db.component.index import ComponentGroupIndex


def purity_group_comparator(purity):
    return int(purity)


def organize_data(data):
    index: ComponentGroupIndex = data["group_index"]
    char_data = data["char_data"]

    # purity groups are numbered ascending by their impurity; put simpler (purer) ones first
    final_output = {
        p: {"groups": __organize_groups(char_data, index, p)} for p in PurityType
    }

    # TODO: order purity groups, component groups, and chars
    # TODO: assign IDs to component groups, chars, and vocab
    # purity_groups = {p: purity_groups[p] for p in sorted(purity_groups.keys(), key=int)}
    # find the highest frequency word for each character and component

    return final_output


def __organize_groups(char_data, index: ComponentGroupIndex, p: PurityType):
    groups = [g for g in index.groups if g.purity_type == p]
    data = {g.component: __create_group_data(g, char_data) for g in groups}
    data = {key: value for key, value in sorted(data.items(), key=__group_sort_key)}

    return data


def __group_sort_key(item):
    component, group_data = item[0], item[1]
    return (
        # descending
        -group_data["num_chars"],
        # ascending
        group_data["exceptions"],
        # descending
        -group_data["max_frequency"],
        # alphabetical ascending
        component,
    )


def __create_group_data(g, char_data):
    data = {
        "exceptions": len(g.exceptions),
        "max_frequency": -1,
        "num_chars": len(g.chars),
        "clusters": [],
    }

    max_frequency = -1
    for chars in g.get_ordered_clusters():
        cluster = {}
        data["clusters"].append(cluster)
        for c in chars:
            cluster[c] = char_data[c]
            for pron_data in char_data[c]["prons"].values():
                for v in pron_data["vocab"]:
                    if v.frequency > max_frequency:
                        max_frequency = v.frequency
    data["max_frequency"] = max_frequency
    return data


ORGANIZE_DATA = {
    "jp": organize_data,
    "zh-HK": organize_data,
    "ko": organize_data,
}
