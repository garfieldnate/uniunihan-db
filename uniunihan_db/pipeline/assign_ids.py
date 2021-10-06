def assign_ids(lang, data):
    """Add ID values for groups and characters"""
    group_id = 1
    char_id = 1
    for purity_group in data.values():
        for group in purity_group["groups"].values():
            group["ID"] = f"g-{lang}-{group_id}"
            group_id += 1
            for cluster in group["clusters"]:
                for char_data in cluster.values():
                    char_data["ID"] = f"c-{lang}-{char_id}"
                    char_id += 1
    return data


ASSIGN_IDS = {
    "jp": lambda data: assign_ids("jp", data),
    "zh": lambda data: assign_ids("zh", data),
    "ko": lambda data: assign_ids("ko", data),
    "vi": lambda data: assign_ids("vi", data),
}
