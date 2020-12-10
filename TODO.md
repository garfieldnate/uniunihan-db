# TODO

Next:

* Char to component -> pron features
    - get traditional variant
        - error if multiples, then figure out how to handle them (pick one?)
    - get components, including self, from cjkv-ids
    - choose one pronunciation (most common? most regular?)
    - break pron into sylable pieces (and keep whole sylable, too)
    -
* Convert to Jun Da frequency list to traditional characters so we have traditional frequency list (roughly)
* simp to trad converter
    - so does Unihan!

## Tasks

* generate decision trees with accuracy stats for pronunciations:
    - components -> Japanese (check against Heisig)
    - components -> Mandarin
    - Japanese -> Mandarin
    - Japanese -> Cantonese
    - Cantonese -> Mandarin
* lib for parsing Syllables:
    - Cantonese
* convert between simplified and traditional characters
* Character lists (grade level, newspaper standard, etc.)
    - generate pronunciation decision trees for subsets
    - https://en.wikisource.org/wiki/Translation:List_of_Frequently_Used_Characters_in_Modern_Chinese#Inferior_frequently_used_characters
    - https://web.archive.org/web/20160404231631/http://resources.publicense.moe.edu.tw/dict_reviseddict_download.html
    - HSK (simplified): http://www.chinesetest.cn/userfiles/file/HSK/HSK-2012.xls
    - Seems that frequency lists and class lists are for simplified only. Here's a traditional-simplified converter: https://github.com/berniey/hanziconv/blob/master/hanziconv/charmap.py (Apache 2.0)
* Investigate https://github.com/nieldlr/hanzi
    - how does determinePhoneticRegularity work? It's essential the Heisig chapter grouping. Can we use this to build a better decision tree?
* Investigate https://github.com/cburgmer/cjklib
    - website is long gone, project no longer maintained abandoned, but it looks pretty comprehensive!
    - Can we revive/modernize it? May be a better data source!
* Investigate http://ocbaxtersagart.lsait.lsa.umich.edu/ (historical reconstructions)
    - try to predict Mandarin/Cantonese from Middle Chinese or reconstructions?
    - an old version has been uploaded to wiktionary and needs to be updated
    - sent an email asking for the license
* Investigate http://www.lrec-conf.org/proceedings/lrec2012/pdf/306_Paper.pdf
    - lists some good resources
    - they don't share their results :(
* Investigate https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/
    - seems they have a very permissive license (used in Wiktionary), but the content is not downloadable as a single file. This resource is truly amazing; if only it were more easily accessible!
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

## Ideas

* Generate shiritori sequence for all characters in a group

## Issues to Open

* Make the on'yomi parser slightly less accommodating and then report misspellings to Unihan
* poetry: script aliases like for npm; test-all = `poetry run pre-commit run --all-files`, etc.
* Unihan does not link 麺 and 麵 as variants (Wikipedia correctly shows trad/simp/sinjitai)

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
* https://github.com/proycon/hanzigrid
