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
## Questions

* Radical database for

## Dev Tools
* poetry: script aliases like for node; test-all = `poetry run pre-commit run --all-files`, etc.
* verify vscode integration
* Standalone build script
* Dockerfile

## Inspirations

* hanzidb.org/about
* hanzicraft.com/about
* https://github.com/jsksxs360/Hanzi
