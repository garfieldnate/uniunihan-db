from uniunihan_db.data.raw_datasets import get_ytenx_rhymes, get_ytenx_variants


def test_get_ytenx_rhymes():
    data = get_ytenx_rhymes()
    assert data["搋"] == [
        {
            "廣韻聲": "徹",
            "廣韻韻": "皆",
            "聲調": "平",
            "等": "2",
            "開合": "開",
            "上字": "丑",
            "下字": "皆",
            "聲符": "虒",
            "韻部": "支",
            "擬音": ["hr'eː"],
            "註釋": "見通俗文",
        },
        {
            "廣韻聲": "徹",
            "廣韻韻": "佳",
            "聲調": "平",
            "等": "2",
            "開合": "開",
            "上字": "丑",
            "下字": "佳",
            "聲符": "虒",
            "韻部": "支",
            "擬音": ["hr'eː", "shreːl"],
            "註釋": "扠字注或體",
        },
    ]


def test_get_ytenx_variants():
    data = get_ytenx_variants()
    assert data["鮮"] == {"鱻", "尠", "尟", "鲜"}
