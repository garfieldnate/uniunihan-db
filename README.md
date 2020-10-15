# UniUnihan Database

I've always wanted the ultimate unihan database.

## Goals

* Aid in learning sinoxenic languages through knowledge transfer based on other sinoxenic languages
* Collect every last shred of (legally usable) info on the Kanji/Hanja/Hanzi/Hán tự
* Support building a website to satisfy sino-xenic language and linguistics nerds
* Re-learn best practices Python project management. A lot has changed lately!

### Desired Data

* char database
* possible cognate database (words, not just characters!)
* decision trees for guessing pronunciations in one language from another

## Developing

Install the pre-commit hook:

    poetry run pre-commit install

If you *have* to commit or push right now and don't have time to fix a failing test, use one of the following:

    git commit --no-verify
    git push --no-verify

For now, all of the tests, formatting, etc. can be run only from the pre-commit hook:

    .git/hooks/pre-commit

I know it's dumb... I'm looking into it.
