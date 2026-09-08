# Vietnamese (Hán-Việt / Sino-Vietnamese) source data

Data backing the **Hán-Việt** part of the book: standard Chinese characters read
with their Sino-Vietnamese pronunciation, ordered and illustrated by frequency.
(The Chữ Nôm data for the planned appendix lives separately in
`data/included/chunom_org/`.)

Loading + generation logic: `uniunihan_db/data/vietnamese.py`.

## Files

| Path | What | Committed? |
|---|---|---|
| `raw/han-viet-thanh-son-le-3.04.txt` | WinVNKey char→Hán-Việt readings (Thanh Sơn Lê), UTF-8 (converted from UTF-16) | yes (provenance) |
| `raw/han-viet-hoc-d-ngo.txt` | WinVNKey char→Hán-Việt readings (Học D. Ngô), UTF-8 | yes |
| `raw/han-viet-trad-supplement-2.02.txt` | WinVNKey supplement, UTF-8 | yes |
| `han_viet_readings.tsv` | **merged** char→reading table (Unihan `kVietnamese` ∪ WinVNKey); `char⇥codepoint⇥pron1\|pron2…` | yes (generated) |

Frequency data is **downloaded and cached** in `data/generated/` (not committed):
the Leipzig `vie_news_2022_1M` corpus (its `words.txt` for syllable frequency and
its `sentences.txt` for true per-word frequency) and HermitDave OpenSubtitles
`vi_50k`. Example words for each character are ranked by **per-word** frequency —
how often the word occurs as a contiguous syllable n-gram in the Leipzig
sentences — since per-syllable lists can't tell which multi-syllable word is
common. The blended syllable frequency is only a tie-breaker for words too rare
to appear in the corpus.

Regenerate the merged table + coverage report:

```bash
poetry run python -m uniunihan_db.data.vietnamese
```

## Source ledger (licensing)

| Source | Provides | License | Ship in public book? |
|---|---|---|---|
| **Unihan `kVietnamese`** | char→Hán-Việt reading (~8.3k chars) | Unicode Data Files license (attribution) | ✅ yes |
| **vnedict** (denisowski) | VN↔EN glosses (no Han) | CC BY 3.0 | ✅ yes (attribute) |
| **Leipzig Corpora** (`vie_news`) | syllable frequency (formal) | CC BY | ✅ yes (attribute) |
| **HermitDave / OpenSubtitles** | syllable frequency (colloquial) | CC BY-**SA** 4.0 | ⚠️ share-alike — using it obligates the book under SA |
| **WinVNKey** Hán-Việt DBs | char→Hán-Việt reading (~19.5k chars) | unclear (WinVNKey is free sw; data terms unstated) | ⚠️ **off by default** (`USE_WINVNKEY_READINGS=False`); opt-in for personal use only |
| **chunom.org** (`standard-list`, `char_data`) | Han-spelled vocab + QN + gloss + freq; Nôm chars | terms unstated | ⚠️ local use; clear before shipping |
| **nomfoundation.org** | Han-Nôm lookup, glosses | "All rights reserved"; free use only *reported* | ⚠️ get explicit permission |
| **zetamu Hantu** | char→reading + glosses | © TitTop, no license | ⚠️ local use only |
| **hvdic.thivien.net** / KanjiDictVN | rich Hán-Việt/Nôm | proprietary | ❌ do not redistribute |

**Bottom line for a shippable public book:** by default the Hán-Việt part uses
only cleanly-licensed data — Unihan `kVietnamese` readings, CEDICT Han spellings +
glosses, vnedict meaning-confirmation, and Leipzig frequency (~3.7k words / ~1.3k
chars). WinVNKey readings (which would add ~40% more) are **off by default**
because their provenance is unclear; enable `USE_WINVNKEY_READINGS` in
`uniunihan_db/data/vietnamese.py` only for personal use. Character keywords come
from Unihan `kDefinition`; word glosses from CEDICT — no definition text is taken
from WinVNKey or other murky sources. (Note CEDICT is CC BY-SA, i.e. share-alike.)
The Chữ Nôm appendix still draws on chunom.org, whose terms are unstated.

## Notes & remaining caveats

- **Reading reconstruction + meaning check** (`get_han_viet_data`): each
  character is assigned the Hán-Việt reading whose Quốc-Ngữ word is attested in
  vnedict *and* whose vnedict gloss **agrees** with the source CEDICT gloss
  (exact or shared-prefix token match, `_gloss_agreement`). A word is **kept only
  if its meaning is confirmed** — deliberately strict, since we are not bound to
  a fixed character list and would rather drop a word than mislead. This fixes
  meaning mismatches (市長 "mayor" → `thị trưởng`, not the market word `thị
  trường`) and rejects false friends (求取 "to seek" spelling `cầu thủ` athlete;
  扇子 "fan" mis-read as `thiên tử`). Trade-off: some correct words whose CEDICT
  and vnedict glosses are worded differently are also dropped.
- **Ranking is per-word corpus frequency**, which fixed the earlier
  syllable-frequency skew (words containing a polysemous syllable like `không`
  are no longer over-ranked). Only the tie-breaker for corpus-absent words is
  per-syllable.
- **Tone-mark placement duplicates** (e.g. `thủy` vs `thuỷ`) exist in the merged
  `han_viet_readings.tsv` but do **not** reach the pipeline: inventory readings
  come from vnedict's consistent spelling, so no collapsing is needed in practice.
- **Nôm vs Sinitic:** `han_viet_readings.tsv` includes Nôm-only characters. The
  Hán-Việt part restricts to characters that appear in the reconstructed
  Sino-Vietnamese vocabulary; the chunom.org data feeds the separate Nôm appendix.
- Consider applying the Unihan L2/23251 corrections (166 erroneous Hán-Nôm
  reading values) to `kVietnamese` if reading noise becomes an issue.
