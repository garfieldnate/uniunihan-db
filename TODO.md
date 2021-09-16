# TODO

Next: find_regularities


Goal design:

* Pipeline starting from data sources and progressing through processing, indexing, and enrichment steps.
    - char data (gather_char_data.py)
    - pronunciations (from vocab or standards like Joyo) -> char2prons (get_char_prons)
    - char2prons + components -> purity groups (find_regularities)
    - add vocab, final sorting -> final language output (add_vocab? finalize)
    - assign IDs (index)
    - combine langs (cross_ref)
    - incorporate custom notes (finalize)
    - write output (format)


Topic: final output

* Number the chapters/purity groups for easier navigation
* continuous (but not intrusive) headers for language and purity group
* output language-specific names of components (BS gives pinyin but not Japanese, etc.)
* Get English keywords for components whose info is taken from ytenx
* Use character normalization to retrieve more BS data for components: 从->從, etc., 瓶
* Re-do structure: vocab surface, pron, meaning need to be in single divs together so that height changes in sync and make selection easier
* Pastel color-coding for languages on edge of pages; kanji for language printed on side (by printing black strips on each page that combine into a character?)
* show weird characters like ㍻ somewhere because it's interesting.

Topic: groupings


Topic: Mandarin support

* nǎi nai listed twice because it represents two different pronunciations
* messed up pron formatting: 好心倒做了驢肝肺 hǎo xīn dào zuò le lu:2 gān fēi
* parse out classifiers for vocab, remove pronunciation or put in ruby text: ear/CL:隻|只[zhi1],個|个[ge4],對|对[dui4]/handle (on a cup)
* parse out "see": see 羊拐[yang2 guai3]
* Get rough frequencies from baidu
* Differentiate baidu and wendu
* Get 三体 word list
    - simp to trad conversion
    - how to present? show chapter 1 vocab with rest of book as backup?
* Possibly provide middle Chinese pronunciations
    - mostly in Ytenx
* Possibly provide old Chinese pronunciations
    - download Baxter/Sagart data

Topic: Japanese Support

* 文字もんじ is a serious problem! Need to list もじ pronunciation
* Char notes: kokuji section, 動 is also kokuji but has a phonetic component
* track down unfound Baxter/Sagart data for 125 components
* Would be nice to have Japanese names for components
* More example compounds would actually be quite nice, particularly for the more common characters
* Would be nice to be able to sort キョウダイ before ケイテイ (need frequency of readings to do this)
* move POS into separate field in vocab (is currently part of definition).
* What is "/(P)" in definition field?
* non-joyo field should always be list, never `False`
* possibly output kun'yomi definitions
* possibly get Japanese glyph alternatives for components

Topic: Korean Support

* kyoyuk hanja doesn't have yo for 樂 or 현 for 見
* Source keywords
* Load libhangul data, align to get readings
* Download ezkorean dictionary
* Short section on gukja, like ones that include hangeul, etc.

Topic: Vietnamese Support

* Get word frequency list
* Get han tu spellings for words
    - hanviet: http://web.archive.org/web/20060218090101/http://perso.wanadoo.fr/dang.tk/langues/hanviet.htm
    - try extracting from Wiktionary?
        - Doing now! Save script somewhere...
    - Winvnkey has some great data! Particularly TuPhuc-HanViet.txt, which I haven't found anywhere else.
    - DDB
* Possibly an appendix on nom characters
* vnedict: http://www.denisowski.org/Vietnamese/vnedict.txt
* zetamu: https://web.archive.org/web/20101022085207/http://zung.zetamu.com/Hantu/hantu_index.html
* nomfoundation.org
    - use is explicitly listed as free!
    - will require lots of work to make it usable
* How to find modern words, though?
* short intro to chu nom (common words like I, is, you, etc.)

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
* python json: ignore '//' key everywhere
* comment on Wikipedia about missing syllables and umlauts in pronunciations for CKIP frequency data
* Unihan: kKoreanName messed up hangeul browser display (인명용 한자)
* Unihan: kGradeLevel only goes through grade 6, but characters are also learned in middle school, so the data is incomplete (missing like 2700 characters)
* Unihan: Wikipedia says 常用字字形表 should have 4762 characters, kHKGlyph only has 4759 (data is 20 years old)

## Dev Tools
* integrate darglint and/or pydocstyle to help keep documentation together
* mypy doesn't check that types are used in signatures, nor that methods are used correctly 😡 Maybe try pyre, pyright, or pytype
* Try rope for refactoring
* verify vscode integration
* Standalone build script
* Dockerfile
* Faster-to-load format than JSON? Is pickle better?

## Technical Questions
* Should we use importlib or something intead of Path(__file__).parents[1]?

## Inspirations

* hanzidb.org/about
* hanzicraft.com/about
* https://github.com/jsksxs360/Hanzi
* https://github.com/proycon/hanzigrid
