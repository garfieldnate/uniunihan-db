# Vietnamese (Hán-Việt / Sino-Vietnamese) source data

Data backing the **Hán-Việt** part of the book: standard Chinese characters read
with their Sino-Vietnamese pronunciation, ordered and illustrated by frequency.
(The Chữ Nôm data for the planned appendix lives separately in
`data/included/chunom_org/`.)

Loading + generation logic: `uniunihan_db/data/vietnamese.py`.

## Files

This directory holds only this README. All Hán-Việt reading data used by the
default build comes from Unihan (downloaded), and the frequency/vocab data from
CEDICT, vnedict, and the Leipzig corpus (also downloaded). Nothing here needs to
be committed as source.

The optional WinVNKey files (`raw/han-viet-*.txt`) are **deliberately not shipped**
— see the provenance note below. If you enable `USE_WINVNKEY_READINGS` for personal
use, place the UTF-8-converted files in `raw/` yourself. A merged reading table +
coverage report can be regenerated (to `data/generated/`, not committed) with:

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

## WinVNKey provenance (why it's not shipped)

The WinVNKey Hán-Việt reading databases add ~40% more words/characters, but they
are **not shipped** and are **off by default**. Their own header states the
readings were transcribed from several dictionaries, including two that are still
in copyright — *Hán Việt tân tự điển* (Nguyễn Quốc Hùng, 1975) and *Tự điển Hán
Việt* (Trần Văn Chánh, 2000) — alongside Thiều Chửu (1943, likely public domain).
The files carry no data license. Individual char→reading mappings are
uncopyrightable facts, but redistributing the database as a block reproduces those
dictionaries' reading tables, so we do not ship it.

Clean ways to recover the extra readings, if wanted (both the user's call):
- **vi.wiktionary Hán-Việt readings** (CC BY-SA 3.0 / GFDL): the WinVNKey authors
  explicitly granted their data to Wiktionary in 2006, so pulling alternates
  through that licensed, attributable channel is clean (note: Wiktionary was
  otherwise avoided for this project).
- **Unicode L2/23-251** correction set: 166 fixed `kVietnamese` values (permissive
  Unicode data) — corrections, not expansions, but worth applying for accuracy.

## Source ledger (licensing)

| Source | Provides | License | Ship in public book? |
|---|---|---|---|
| **Unihan `kVietnamese`** | char→Hán-Việt reading (~8.3k chars) | Unicode Data Files license (attribution) | ✅ yes |
| **vnedict** (denisowski) | VN↔EN glosses (no Han) | CC BY 3.0 | ✅ yes (attribute) |
| **Leipzig Corpora** (`vie_news`) | syllable frequency (formal) | CC BY | ✅ yes (attribute) |
| **HermitDave / OpenSubtitles** | syllable frequency (colloquial) | CC BY-**SA** 4.0 | ⚠️ share-alike — using it obligates the book under SA |
| **WinVNKey** Hán-Việt DBs | char→Hán-Việt reading (~19.5k chars) | transcribes in-copyright dictionaries; no data license (see above) | ❌ **not shipped**, off by default (`USE_WINVNKEY_READINGS=False`); local personal use only |
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
