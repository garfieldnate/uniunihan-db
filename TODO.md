# TODO

Topic: Mandarin support

* Use CJKlib (https://pythonhosted.org/cjklib/cjklib.reading.converter.PinyinWadeGilesConverter-class.html) to convert pinyin to Wade-Giles so words from CKIP and and chars from Unihan have same pronunciation strings.

Topic: final dictionary output

* Output final data (json) per char in desired order
* Provide highest frequency word for all characters and their pronunciations
* for singleton chars:
    - order chars by commonness of that word

Topic: Japanese Support

* Use new char glyphs to find words
    - More complex char and/or word representations, or just another index?
* Find larger frequency list
* provide historical spellings for Japanese characters
* when outputting group components, get Japanese glyphs where appropriate

Topic: Korean Support

* Get name of each character from somewhere
* Get Hanja word dictionary

Topic: Vietnamese Support

* Get word frequency list
* Get han tu spellings for words

## Tasks

Prediction experiments:
- components -> Japanese (sanity check with Heisig)
- components -> Mandarin
- Japanese -> Mandarin
- Japanese -> Cantonese
- Cantonese -> Mandarin

* Convert Jun Da frequency list to traditional characters so we have traditional frequency list (roughly)
* generate decision trees with accuracy stats for pronunciations:
    - components -> Japanese (check against Heisig)
    - components -> Mandarin
    - Japanese -> Mandarin
    - Japanese -> Cantonese
    - Cantonese -> Mandarin
* lib for parsing Syllables:
    - Cantonese
    - Vietnamese
* Character lists (grade level, newspaper standard, etc.)
    - https://en.wikisource.org/wiki/Translation:List_of_Frequently_Used_Characters_in_Modern_Chinese#Inferior_frequently_used_characters
    - https://web.archive.org/web/20160404231631/http://resources.publicense.moe.edu.tw/dict_reviseddict_download.html
    - Kanken
* Investigate https://github.com/cburgmer/cjklib
    - website is long gone, project no longer maintained, but it looks pretty comprehensive!
    - Can we revive/modernize it? May be a better data source!
* Incorporate http://ocbaxtersagart.lsait.lsa.umich.edu/ (historical reconstructions)
    - or try making a datapackage
* Investigate http://www.lrec-conf.org/proceedings/lrec2012/pdf/306_Paper.pdf
    - lists some good resources
    - they don't share their results :(
* Investigate https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/
    - seems they have a very permissive license (used in Wiktionary), but the content is not downloadable as a single file. This resource is truly amazing; if only it were more easily accessible!
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
* Investigate OpenCC
    - https://github.com/BYVoid/OpenCC/blob/master/data/dictionary


## Questions/Needs

* Legal character classifications (grade levels, Jouyou, etc.)
* DB for on readings by period (go-on, kan-on, tou-on, etc.)
* DB for historical kun'yomi
    - (very) partial dataset: https://www.bunka.go.jp/kokugo_nihongo/sisaku/joho/joho/kijun/naikaku/gendaikana/huhyo_i.html
* historical spellings, with wi, we, ye, etc. for Japanese

## Ideas

* Generate shiritori sequence for all characters in a group

## Issues to Open

* Make the on'yomi parser slightly less accommodating and then report misspellings to Unihan
* poetry: script aliases like for npm; test-all = `poetry run pre-commit run --all-files`, etc.
* Unihan does not link 麺 and 麵 as variants (Wikipedia correctly shows trad/simp/sinjitai)
* Unihan does not indicate where okurigana in a kun'yomi begin
* Would be great if unihan-etl (or better yet, Unihan itself!) structurized the (traditional variant of X), (non-classical variant of X), (same as X), etc. in the `kDefinition` field.
    - 㑶 is listed as the traditional variant of 㐹, but the Mandarin pronunciations are different! The kDefinition field notes that it's treated as a variant of 仡, which does have the same pronunciation.
* Unihan entries 彙彚𢑥 do not mention each other as variants
* Really wish unihan had kyuujitai/sinjitai links; 綠 links to 緑 only in the jinmeiyo kanji field.
* Unihan: relationship between 駄 and 馱 not given; between 瓶 and 甁, too (sinjitai/kyuujitai)
* Unihan: relationship between 栃𣜜櫔 not given
* Unihan: missing relationship between 顏顔, 匂匈, 倶俱 (from ytenx JihThex),


## Dev Tools
* integrate darglint and/or pydocstyle to help keep documentation together
* mypy doesn't check that types are used in signatures, nor that methods are used correctly 😡 Maybe try pyre, pyright, or pytype
* Try rope for refactoring
* verify vscode integration
* Standalone build script
* Dockerfile

## Technical Questions
* Should we use importlib or something intead of Path(__file__).parents[1]?

## Inspirations

* hanzidb.org/about
* hanzicraft.com/about
* https://github.com/jsksxs360/Hanzi
* https://github.com/proycon/hanzigrid
