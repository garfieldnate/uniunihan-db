# Chinese character dictionary for Sino-xenic languages

![verification workflow](https://github.com/garfieldnate/uniunihan-db/actions/workflows/verify.yml/badge.svg)
![dictionary building workflow](https://github.com/garfieldnate/uniunihan-db/actions/workflows/build_book.yml/badge.svg)

See the current book form online [here](https://garfieldnate.github.io/uniunihan-db/). The book is still very incomplete, but input is welcome!

Classical Chinese was the written lingua franca of East Asia until the early 1900's, and as a result several languages from this area still share a large part of their vocabulary (with differences in pronunciation). For example, if you know that the word for "telephone" in Japanese is 電話 (den'wa), you might notice the similar pronunciations in Mandarin (diǎn huà), Korean (jeonhwa) and Vietnamese (điện thoại). This book was created to help you make those connections and leverage your knowledge of one Sino-xenic language to quickly recognize vocabulary in another.

The book is divided into 4 parts, one for each language, and the characters are organized by regularity of pronunciation, following the structure of James W. Heisig's [Remembering the Kanji II](https://www.goodreads.com/book/show/495157.Remembering_the_Kanji_II). The idea behind the character ordering is to allow the learner to cover a lot of ground quickly by first learning groups of characters which have a clear pronunciation given some phonetic component, and proceeding to less regular and more difficult ones later. Each character is presented with its pronunciations, example words using the pronunciation, cross-references with usage in other languages, and some additional information depending on the language.

## Goals

-   Aid in learning sino-xenic languages through knowledge transfer based on other sinoxenic languages
-   Collect every last shred of (legally usable) info on the Kanji/Hanja/Hanzi/Hán tự
-   Support building a website to satisfy sino-xenic language and linguistics nerds
-   Explore the Python ecosystem and have fun :) This repository will serve as my source of a good Python project setup.

## Desired Data

-   char database
-   possible cognate database (words, not just characters!)

## Developing

The project is managed using [Poetry](https://python-poetry.org/docs/):

    pip3 install --user poetry

To install dependencies:

    poetry install --no-root

To build the book (output to `data/generated/book`):

    poetry run poe build_book

This one command reproduces the whole book from scratch: it runs the data
pipeline for every language, cross-references the results, and renders the HTML.
See [Data and reproducibility](#data-and-reproducibility) below for what it
downloads and how the stages fit together.

To install the pre-commit hooks:

    poetry run pre-commit install

If you _have_ to commit or push right now and don't have time to fix a failing test, use one of the following:

    git commit --no-verify
    git push --no-verify

All of the lints and tests can be run using the poe task `verify`:

    poetry run poe verify

A VSCode settings file is included which contains configurations for all of the linting and formatting tools installed.

## Data and reproducibility

The entire book is reproducible from the scripts in this repo. From a fresh
checkout, `poetry install --no-root` followed by `poetry run poe build_book`
downloads every external dataset, processes it, and writes the HTML book — no
manual data preparation is required.

### The build pipeline

Three poe tasks make up the pipeline (`build_book` runs all of them as needed):

    poetry run poe pipeline -l <zh|jp|ko|vi|vi_nom>   # one language's data
    poetry run poe collate                            # all languages + cross-refs
    poetry run poe build_book                         # render HTML (re-collates if needed)

Each language runs the same ordered stages (see `uniunihan_db/pipeline/`): gather
characters → add pronunciations → group by phonetic component → integrate
Old/Middle Chinese → select example vocab → organize by regularity → assign IDs.
Every stage is a dict keyed by language code, so each language plugs into the
shared machinery.

For a clean rebuild that re-runs everything, delete the generated data first:

    rm -rf data/generated && poetry run poe build_book

### Where the data comes from

- **Downloaded automatically** into `data/generated/` (cached; safe to delete) by
  `uniunihan_db/data/datasets.py` and `uniunihan_db/data/vietnamese.py`: Unihan,
  CC-CEDICT, frequency-annotated EDICT, ytenx (phonetic components / Old & Middle
  Chinese), libhangul, Kengdic, Jun Da's character frequencies, vnedict, the
  Leipzig Vietnamese corpus, and the OpenSubtitles Vietnamese frequency list.
  First run is slow and needs the network; later runs reuse the cache.
- **Committed as source** under `data/included/`: curated/manual lists (Jōyō,
  educational hanja, HSK, CKIP, chunom.org, Baxter–Sagart, manual phonetic
  components, etc.) and, for Vietnamese, the WinVNKey Hán-Việt reading databases
  under `data/included/vi/`. See `data/included/vi/README.md` for the Vietnamese
  source/license ledger.

The WinVNKey files in `data/included/vi/raw/` were distributed as UTF-16 and are
committed here converted to UTF-8 (`iconv -f UTF-16 -t UTF-8 <in> | tr -d '\r'`);
because they are committed, no re-conversion is needed to build. The merged
`data/included/vi/han_viet_readings.tsv` is a generated reference table; regenerate
it (and a coverage report) with `poetry run python -m uniunihan_db.data.vietnamese`.

## Known Issues

### Can't discover/run tests in VSCode

Set up the project as described above, and ensure VSCode is using the local virtual environment.

Following discussions [here](https://github.com/microsoft/vscode-python/issues/21757), open the testing tab. It will say that it did not find any tests. Check the output console to get TEST_PORT and TEST_UUID. Then run the following commands in a new terminal:

    export TEST_PORT=...
    export TEST_UUID=...
    PYTHONPATH=~/.vscode/extensions/ms-python.python-2024.0.1/pythonFiles .venv/bin/python -m pytest -p vscode_pytest --collect-only tests

This discovers all of the tests successfully. Then run:

    .venv/bin/python ~/.vscode/extensions/ms-python.python-2024.0.1/pythonFiles/vscode_pytest/run_pytest_script.py --rootdir .

This correctly runs the tests. However, if you try to run the tests in the UI they will hang forever.

The extension paths above may be different with different versions of the Python extension for VSCode. Tested as of 2/25/2024.
