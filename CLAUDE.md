# CLAUDE.md

Guidance for AI agents working in this repository. Read this first.

## What this project is

`uniunihan-db` builds a **dictionary/book of Chinese characters for learners of
Sino-xenic languages** (Japanese, Korean, Mandarin, Vietnamese). The premise:
these languages share a large borrowed Chinese vocabulary, so a learner of one
can bootstrap another by recognizing shared characters and their (regularly
corresponding) pronunciations.

Characters are grouped by **phonetic component** and ordered by **pronunciation
regularity** (the "purity" of a group), following the pedagogy of Heisig's
*Remembering the Kanji II*. Each character is shown with its pronunciations,
example vocabulary, cross-references to the same character in the other
languages, and language-specific extras.

The output is a static HTML "book" (see `data/generated/book/`), published at
https://garfieldnate.github.io/uniunihan-db/. It is intentionally incomplete and
research-flavored — this repo doubles as the author's reference Python project.

## Repo layout

- `uniunihan_db/` — the package
  - `pipeline/` — the per-language data pipeline (see below)
  - `data/` — data loading (`datasets.py`), path constants (`paths.py`), shared
    types (`types.py`)
  - `lingua/` — language-specific logic: `aligner.py` (align a word's surface
    characters to its pronunciation syllables), `japanese.py`, `mandarin.py`
  - `component/` — phonetic-component grouping: `group.py` (`ComponentGroup`,
    `PurityType`), `index.py` (`find_component_groups`)
  - `collate.py` — runs all language pipelines and cross-references characters
    shared across languages
  - `build_book.py` — renders collated JSON into HTML via Jinja templates
- `data/included/` — **source data committed to the repo** (curated/manual lists)
- `data/generated/` — **downloaded + pipeline output; not authoritative, safe to
  delete and regenerate.** Do not hand-edit; do not treat as source of truth.
- `templates/` — Jinja2 HTML templates (`*_char.html.jinja` per language)
- `css/` — copied into the book output
- `tests/` — pytest; `tests/corpus/` holds fixtures
- `TODO.md` — the author's extensive running notes, including a per-language
  wishlist. Read the relevant section before starting language work.

## Environment & commands

Managed with **Poetry** (Python `^3.9`; a `.venv/` is present).

```bash
poetry install --no-root          # install deps
poetry run poe pipeline -l vi     # run ONE language pipeline (jp|zh|ko|vi)
poetry run poe collate            # run all pipelines + cross-reference
poetry run poe build_book         # render HTML book (regenerates collate if needed)
poetry run poe verify             # all lints + tests (pre-commit run --all-files)
poetry run pytest tests           # tests only
```

Note: the README mentions `build-book`, but the poe task is `build_book`
(underscore). Poe tasks are defined in `pyproject.toml` under `[tool.poe.tasks.*]`.

Lint/format stack: black, isort (black profile), flake8, pyright (basic mode),
pre-commit. `pyright` ignores `data/generated`.

## The pipeline (the core abstraction)

`pipeline/runner.py` runs a fixed sequence of stages for one `language`
(`"zh" | "jp" | "ko" | "vi"`). **Every stage is a dict keyed by language code**,
so adding/altering a language means editing that language's entry in each stage:

1. `gather_char_data.py` — `LOAD_CHAR_DATA[lang]()` → `{char: {char data}}`
2. `add_char_prons.py` — `ADD_PRONUNCIATIONS[lang]` → adds `prons: {pron: {...}}`
3. `group_chars.py` — `GROUP_CHARS[lang]` → groups by phonetic component into a
   `ComponentGroupIndex` (`{"char_data", "group_index"}`)
4. `oc_mc.py` — `OC_MC[lang]` → attaches Old/Middle Chinese data to components
5. `select_vocab.py` — `SELECT_VOCAB[lang]` → attaches example `vocab` to each
   pronunciation (≤ `MAX_EXAMPLE_VOCAB`, preferring frequent, unused, multi-char
   words)
6. `organize.py` — `ORGANIZE_DATA[lang]` → nests by `PurityType` → component
   group → cluster → char, sorted so the most useful info comes first
7. `assign_ids.py` — `ASSIGN_IDS[lang]` → stamps `g-<lang>-<purity>-N` /
   `c-<lang>-<purity>-N` IDs

Then `collate.py` runs all four languages and links characters that appear in
more than one (`cross_ref`). `build_book.py` turns the collated JSON into HTML.

Data flows as plain nested dicts (plus `Word`/`ZhWord` dataclasses from
`data/types.py`). Output of each language lands in
`data/generated/pipeline/<lang>/all_data.json`; collated in
`data/generated/collated/final.json`.

## Data sources (`data/datasets.py`)

Downloaders (prefixed `__download_*`) fetch and cache into `data/generated/`;
accessors (`get_*`, mostly `@cache`d) load them. **Many stages hit the network on
first run** (Unihan, CEDICT, EDICT, ytenx, libhangul, kengdic, Jun Da freq list).
Expect the first pipeline run to be slow and to require internet.

Per language, roughly:
- **jp**: Jōyō list (`augmented_joyo.csv`) + historical on-yomi; vocab from
  frequency-annotated EDICT; manual overrides in `jp_vocab_override.json`
- **zh**: Unihan (`kHKGlyph` set) + CEDICT vocab + CKIP frequency
- **ko**: educational hanja (`kyoyuk_hanja.csv`) + Kengdic vocab
- **vi**: currently built from **chunom.org** data (`data/included/chunom_org/`)
  — see the caveat below

Phonetic components come from **ytenx** rhyme data plus manual overrides
(`manual_components.json`); Old/Middle Chinese from Baxter–Sagart and ytenx.

## Vietnamese: important caveat

The other three languages model **Chinese characters read with the borrowed
Sino-xenic reading** (on-yomi / hanja eum / Mandarin) illustrated with
Sino-xenic vocabulary. The Vietnamese parallel to that is **Hán tự / Hán-Việt**
(Sino-Vietnamese), and that is what the `vi` part now builds.

Data + logic live in `uniunihan_db/data/vietnamese.py`
(see `data/included/vi/README.md` for the source/license ledger):

- **Readings** come from Unihan `kVietnamese` (+ Unicode L2/23-251 corrections),
  supplemented by the WinVNKey databases (`USE_WINVNKEY_READINGS`, on) which add
  ~40% more words/chars. WinVNKey transcribes dictionaries (see
  `data/included/vi/README.md`); the readings are used as facts, credited in the
  book acknowledgements. **Word definitions** are shown from vnedict (human,
  CC BY); CEDICT is used only internally (word candidates, Han spellings,
  meaning-confirmation).
- **Vocabulary + inventory** (`get_han_viet_data`) is reconstructed: take
  multi-character CEDICT (Chinese) words, read each character with its Unihan
  Hán-Việt reading, and keep the word only if that Quốc-Ngữ spelling is confirmed
  a real Vietnamese word by **vnedict**. This yields genuine Sino-Vietnamese
  vocabulary (~5.8k words / ~1.6k chars) with real Hán tự spellings, Hán-Việt
  readings, and English glosses — all from permissively-licensed sources. The
  character inventory is exactly the characters used by that vocabulary.
- **Frequency / ordering** is by true **per-word** frequency: each candidate word
  is counted as a contiguous syllable n-gram in the Leipzig `vie_news_2022_1M`
  sentence corpus (`_count_corpus_word_frequency`), since per-syllable lists can't
  say which multi-syllable word is common. The blended Leipzig+OpenSubtitles
  *syllable* frequency (`get_vi_syllable_frequency`, weights are constants at the
  top of `vietnamese.py`) is only a tie-breaker for corpus-absent words.
  Characters are ordered within their groups by the frequency of their most
  common word (via `pipeline/organize.py`, which falls back to alphabetical for
  the other languages).

See `data/included/vi/README.md` for remaining caveats (a residue of reading
mismatches when only a wrong reading is attested in vnedict; the merged readings
table has tone-placement duplicates that don't reach the pipeline).

The **chunom.org / Chữ Nôm** data (`data/included/chunom_org/`,
`get_chunom_org_vocab`) is no longer used by the main `vi` pipeline; it is
reserved for a planned **Chữ Nôm appendix** (not yet built).

## Conventions & gotchas

- **Don't commit regenerated `data/generated/`** as if it were source; it is
  derived output.
- Source data lives in `data/included/`; add new curated data there and wire a
  path constant in `data/paths.py`.
- Some included data files (e.g. WinVNKey `.txt`) are **UTF-16 with a BOM** —
  decode accordingly, not as UTF-8.
- `Word.frequency` is stored **negative** in several places so ascending sort =
  most-frequent-first; `-1` means "unknown". Check the sign convention in the
  loader you're using.
- Aligners in `lingua/aligner.py` silently drop words whose surface length
  doesn't match the syllable count (numbers, letters, multi-syllabic chars).
- `PurityType` values drive ordering; groups render in ascending complexity.
- The build has been in a partially broken state (see recent commits); run
  `poetry run poe verify` and the specific pipeline before assuming green.

## Where to look first for a task

- Adding/fixing a language → the seven `pipeline/*.py` dicts + that language's
  `templates/<lang>_char.html.jinja` + `data/datasets.py` loaders.
- Character grouping/ordering logic → `component/` + `pipeline/organize.py`.
- Output/appearance → `templates/` + `build_book.py` + `css/`.
- New data source → `data/datasets.py` (downloader + accessor) and
  `data/paths.py`.
