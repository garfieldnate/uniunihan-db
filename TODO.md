# TODO

## Tasks

* lib for parsing Syllables:
    - Japanese
    - Mandarin
    - Cantonese
* generate decision tree for pronunciations:
    - Japanese -> Mandarin
    - Japanese -> Cantonese
    - Cantonese -> Mandarin
* Investigate https://github.com/nieldlr/hanzi
    - how does determinePhoneticRegularity work? It's essential the Heisig chapter grouping. Can we use this to build a better decision tree?
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
## Questions

* DB for on readings by period (go-on, kan-on, tou-on, etc.)

## Dev Tools
* poetry: script aliases like for node; test-all = `poetry run pre-commit run --all-files`, etc.
* verify vscode integration
* Standalone build script
* Dockerfile

## Inspirations

* hanzidb.org/about
* hanzicraft.com/about
* https://github.com/jsksxs360/Hanzi
