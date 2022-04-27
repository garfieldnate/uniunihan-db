# Chinese character dictionary for Sino-xenic languages

![verification workflow](https://github.com/garfieldnate/uniunihan-db/actions/workflows/verify.yml/badge.svg)
![dictionary building workflow](https://github.com/garfieldnate/uniunihan-db/actions/workflows/build_book.yml/badge.svg)

See the current book form online [here](https://garfieldnate.github.io/uniunihan-db/).

Classical Chinese was the written lingua franca of East Asia until the early 1900's, and as a result these languages still share a large part of their vocabulary (with pronunciation differences). For example, if you know the word for "telephone" in Japanese is 電話 (den'wa), you might notice the similar pronunciations in Mandarin (diǎn huà), Korean (jeonhwa) and Vietnamese (điện thoại). This book was created to help you make those connections and leverage your knowledge of one Sino-xenic language to quickly recognize vocabulary in another.

The book is divided into 4 parts, one for each language, and the characters are organized by regularity of pronunciation, following the structure of James W. Heisig's [Remembering the Kanji II](https://www.goodreads.com/book/show/495157.Remembering_the_Kanji_II). The idea behind the character ordering is to allow the learner to cover a lot of ground quickly by first learning groups of characters which have a clear pronunciation given some phonetic component, and proceeding to less regular and more difficult ones later. Each character is presented with its pronunciations, example words using the pronunciation, cross-references with usage in other languages, and some additional information depending on the language.

## Goals

-   Aid in learning sino-xenic languages through knowledge transfer based on other sinoxenic languages
-   Collect every last shred of (legally usable) info on the Kanji/Hanja/Hanzi/Hán tự
-   Support building a website to satisfy sino-xenic language and linguistics nerds
-   Explore the Python ecosystem and have fun :)

## Desired Data

-   char database
-   possible cognate database (words, not just characters!)

## Developing

The project is managed using [Poetry](https://python-poetry.org/docs/):

    pip3 install --user poetry

To install dependencies:

    poetry install --no-root

To build the book (output to data/generated/book):

    poetry run build-book

To install the pre-commit hooks:

    poetry run pre-commit install

If you _have_ to commit or push right now and don't have time to fix a failing test, use one of the following:

    git commit --no-verify
    git push --no-verify

All of the lints and tests can be run using the poe task `verify`:

    poetry run poe verify

A VSCode settings file is included which contains configurations for all of the linting and formatting tools installed.

