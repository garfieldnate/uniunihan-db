# UniUnihan Database

I've always wanted the ultimate Chinese character database.

## Goals

-   Aid in learning sinoxenic languages through knowledge transfer based on other sinoxenic languages
-   Collect every last shred of (legally usable) info on the Kanji/Hanja/Hanzi/Hán tự
-   Support building a website to satisfy sino-xenic language and linguistics nerds
-   Re-learn best practices Python project management. A lot has changed lately!

### Desired Data

-   char database
-   possible cognate database (words, not just characters!)
-   decision trees for guessing pronunciations in one language from another

## Installing

The simplest thing that will work for most developers:

    cd uniunihan-db
    pip3 install .

## Developing

The project is managed using [Poetry](https://python-poetry.org/docs/):

    pip3 install --user poetry

Install dependencies:

    poetry install --no-root

Install the pre-commit hooks:

    poetry run pre-commit install

If you _have_ to commit or push right now and don't have time to fix a failing test, use one of the following:

    git commit --no-verify
    git push --no-verify

For now, all of the tests, formatting, etc. can be run only from the pre-commit hook:

    poetry run pre-commit run --hook-stage commit --all-files

I know it's dumb... I'm looking into it.

A VSCode settings file is included which contains configurations for all of the linting and formatting tools installed.

Pre-compilation of data sources:

    poetry run build-db

Analysis of characters for one language (in flux; will probably be a learner's dictionary output of some kind):

    poetry run find-regularities
