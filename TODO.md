# TODO

## Tasks

* lib for parsing Syllables:
    - Cantonese
* generate decision trees with accuracy stats for pronunciations:
    - Japanese -> Mandarin
    - Japanese -> Cantonese
    - Cantonese -> Mandarin
* Character lists (grade level, newspaper standard, etc.)
    - generate pronunciation decision trees for subsets
* Investigate https://github.com/nieldlr/hanzi
    - how does determinePhoneticRegularity work? It's essential the Heisig chapter grouping. Can we use this to build a better decision tree?
* Investigate https://code.google.com/archive/p/cjklib
    - website is long gone, project long abandoned, but it looks pretty comprehensive!
    - https://web.archive.org/web/20100902210649/http://cjklib.org/0.3/
    - Can we revive/modernize it? May be a better data source!
* build_db should download radicals data
* generate decision tree for pronunciations:
    - radicals -> joyo Japanese
    - radicals -> hsk Mandarin
    - radicals -> hsk Cantonese
* Investigate Wiktionary
    - has become much more extensive in recent years!
    - sino-xenic compound cognates are already there (see https://en.wiktionary.org/wiki/%E4%BA%94%E7%A9%80)
    - lua error on some pages?
        - example: https://en.wiktionary.org/wiki/%E4%BA%BA
        - tracker: https://phabricator.wikimedia.org/T165935
    - can/should I contribute directly to wiktionary?
        - seems like data is very hit and miss; 人 article for Korean contains many compounds. Check page for 人力車 and it doesn't have a sino-xenic descendants section 🤔
    - would it still be valuable to create my own database?
        - probably, if nothing else we can find what wiktionary is missing

## Questions/Needs

* Legal character classifications (grade levels, Jouyou, etc.)
* DB for on readings by period (go-on, kan-on, tou-on, etc.)
* unihan kun'yomi don't indicate okurigana!
* historical spellings, with wi, we, ye, etc. for Japanese

## Issues to Open

* Make the on'yomi parser slightly less accommodating and then report misspellings to Unihan
* poetry: script aliases like for npm; test-all = `poetry run pre-commit run --all-files`, etc.

## Dev Tools
* integrate darglint and/or pydocstyle to help keep documentation together
* mypy doesn't check that types are used in signatures, nor that methods are used correctly 😡 Maybe try pyre, pyright, or pytype
* verify vscode integration
* Standalone build script
* Dockerfile

## Inspirations

* hanzidb.org/about
* hanzicraft.com/about
* https://github.com/jsksxs360/Hanzi
