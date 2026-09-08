# Vietnamese (Hán-Việt / Sino-Vietnamese) source data

Data backing the **Hán-Việt** part of the book: standard Chinese characters read
with their Sino-Vietnamese pronunciation, ordered and illustrated by frequency.
(The Chữ Nôm data for the planned appendix lives separately in
`data/included/chunom_org/`.)

Loading + generation logic: `uniunihan_db/data/vietnamese.py`.

## Files

This directory holds this README, the Unicode `kvietnamese_corrections.tsv`, and the
WinVNKey reading files under `raw/` (used with attribution — see below). Frequency
and vocab data (Unihan, CEDICT, vnedict, Leipzig) are downloaded to `data/generated/`.
A merged reading table + coverage report can be regenerated (to `data/generated/`,
not committed) with:

```bash
poetry run python -m uniunihan_db.data.vietnamese
```

Frequency data is **downloaded and cached** in `data/generated/` (not committed):
the Leipzig `vie_news_2022_1M` corpus (its `words.txt` for syllable frequency and
its `sentences.txt` for true per-word frequency) and HermitDave OpenSubtitles
`vi_50k`. Example words for each character are ranked by **per-word** frequency —
how often the word occurs as a contiguous syllable n-gram in the Leipzig
sentences — since per-syllable lists can't tell which multi-syllable word is
common. The blended syllable frequency is only a tie-breaker for words too rare
to appear in the corpus.

## WinVNKey provenance (shipped, with attribution)

The WinVNKey Hán-Việt reading databases (`raw/han-viet-*.txt`) add ~40% more
words/characters and are **used by default** (`USE_WINVNKEY_READINGS=True`). Their
header states the readings were transcribed from several dictionaries, two still in
copyright — *Hán Việt tân tự điển* (Nguyễn Quốc Hùng, 1975) and *Tự điển Hán Việt*
(Trần Văn Chánh, 2000) — alongside Thiều Chửu (1943, likely public domain). We use
them because individual char→reading pairs are **uncopyrightable facts**; the book's
acknowledgements credit the WinVNKey compilers (Thanh Sơn Lê, Học D. Ngô) and name
those source dictionaries as the original sources. (This is a considered,
non-commercial, attribution-based use, not a legal guarantee.) Set
`USE_WINVNKEY_READINGS=False` to fall back to Unihan-only readings.

**Unicode L2/23-251 corrections are applied.** `kvietnamese_corrections.tsv`
(committed; extracted from the Unicode working-group document
`23251-kvietnameseCorr.pdf`) fixes 166 erroneous/incomplete `kVietnamese` values
by removing wrong readings and adding missing ones; `_unihan_han_viet_readings`
applies it. This is permissively-licensed Unicode data.

To further recover the ~40% coverage WinVNKey would add, a clean channel exists
but is the user's call: **vi.wiktionary Hán-Việt readings** (CC BY-SA 3.0 / GFDL,
attributable) — though note individual char→reading pairs are uncopyrightable
facts, so the licensing question is really about how they are sourced/attributed
in bulk, not about any single reading.

## Source ledger (licensing)

| Source | Provides | License | Ship in public book? |
|---|---|---|---|
| **Unihan `kVietnamese`** | char→Hán-Việt reading (~8.3k chars) | Unicode Data Files license (attribution) | ✅ yes |
| **vnedict** (denisowski) | VN↔EN glosses (no Han) | CC BY 3.0 | ✅ yes (attribute) |
| **Leipzig Corpora** (`vie_news`) | syllable frequency (formal) | CC BY | ✅ yes (attribute) |
| **HermitDave / OpenSubtitles** | syllable frequency (colloquial) | CC BY-**SA** 4.0 | ⚠️ share-alike — using it obligates the book under SA |
| **WinVNKey** Hán-Việt DBs | char→Hán-Việt reading (~19.5k chars) | transcribes dictionaries (see above); readings used as facts, with attribution | ⚠️ shipped + on by default (`USE_WINVNKEY_READINGS=True`); credited in the book acknowledgements |
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
