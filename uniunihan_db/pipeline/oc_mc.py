# Integrate Old and Middle Chinese data

from loguru import logger

from uniunihan_db.data.datasets import get_baxter_sagart, get_ytenx_rhymes
from uniunihan_db.util import format_json


def integrate_historical_chinese(all_data):
    """For now, we just add the historical data to the components to
    illustrate the original pronunciations they signalled"""

    baxter_sagart_data = get_baxter_sagart()
    ytenx_rhymes = get_ytenx_rhymes()
    missing_data_components = []
    for g in all_data["group_index"].groups:
        g.sup_info["historical"] = historical_data = []

        component = g.component
        # Filter out groups that aren't based off of real components
        if component in ["国字", "國字"]:
            continue

        bs_infos = baxter_sagart_data[component]
        ytenx_infos = ytenx_rhymes[component]
        if bs_infos := baxter_sagart_data[component]:
            for bs in bs_infos:
                historical_data.append(
                    {
                        "source": "BS",  # Baxter/Sagart
                        "gloss": bs.gloss,
                        "OC": [bs.old_chinese],
                        "MC": bs.middle_chinese,
                        "LMC": None,
                    }
                )
        elif ytenx_infos := ytenx_rhymes[component]:
            for yt in ytenx_infos:
                historical_data.append(
                    {
                        "source": "ZZ",  # Zheng/Zhang # TODO: confirm it's Zheng/Zhang
                        "gloss": "TODO: gloss",  # get it from Unihan? (be sure to mark source in that case)
                        "OC": yt.old_chinese,
                        "MC": yt.middle_chinese,
                        "LMC": yt.late_middle_chinese,
                    }
                )
        else:
            missing_data_components.append(component)

    if missing_data_components:
        logger.warning(
            f"Missing historical data for {len(missing_data_components)} components"
        )
        logger.debug(format_json(missing_data_components))

    return all_data


OC_MC = {
    "jp": integrate_historical_chinese,
    "ko": integrate_historical_chinese,
    "zh": integrate_historical_chinese,
}
