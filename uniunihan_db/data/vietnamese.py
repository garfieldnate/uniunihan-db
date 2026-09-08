"""Vietnamese (Hán-Việt / Sino-Vietnamese) data loading.

Two things live here:

* ``get_han_viet_readings`` -- a merged ``char -> {Hán-Việt reading}`` map built
  from Unihan's ``kVietnamese`` field plus the WinVNKey reading databases.
* ``get_han_viet_data`` -- the Sino-Vietnamese vocabulary and character
  inventory, with each word ranked by its true corpus frequency (see below).
* ``get_vi_syllable_frequency`` -- a blended Vietnamese syllable-frequency score,
  used only as a tie-breaker for words too rare to appear in the corpus.

Because Vietnamese is written one syllable per token, frequency *lists* only give
per-syllable counts. To choose the best example words for each character we need
per-*word* frequency, so we count each candidate word as a contiguous syllable
n-gram in the Leipzig sentence corpus (``_count_corpus_word_frequency``).

The syllable-frequency blend combines two openly-licensed corpora; adjust the
weights below to change how much each register counts.
"""

import itertools
import re
import tarfile
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from math import prod
from typing import Dict, List, Mapping, MutableMapping, Sequence, Set, Tuple

import requests
from loguru import logger

from uniunihan_db.data.datasets import get_cedict, get_unihan
from uniunihan_db.data.paths import (
    LEIPZIG_VI_DIR,
    LEIPZIG_VI_SENTENCES_FILE,
    LEIPZIG_VI_TARBALL,
    LEIPZIG_VI_URL,
    LEIPZIG_VI_WORDS_FILE,
    OPENSUBS_VI_FILE,
    OPENSUBS_VI_URL,
    VI_WINVNKEY_FILES,
    VNEDICT_FILE,
    VNEDICT_URL,
)
from uniunihan_db.data.types import Word

# --- Frequency blend weights (tweak these) --------------------------------
# How much each corpus contributes to the blended syllable-frequency score.
# Leipzig is formal/written register (news, wiki), which better matches the
# largely formal Sino-Vietnamese vocabulary; OpenSubtitles is colloquial and
# fills out the long tail. Weights are normalized, so only their ratio matters.
LEIPZIG_WEIGHT = 0.7
OPENSUBS_WEIGHT = 0.3

# A reconstructed word is only kept if its Vietnamese meaning is *confirmed* --
# its vnedict gloss agrees with the source Chinese gloss. This keeps totally
# incorrect entries (false friends, wrong readings) out of the book, at the cost
# of dropping genuine Sino-Vietnamese words whose meaning drifted from Chinese and
# whose vnedict/CEDICT glosses therefore no longer overlap (e.g. 方便 phương tiện
# "means/vehicle" vs Chinese "convenient"). Set False to also keep words that use
# only standard Unihan readings even without a gloss match -- broader coverage,
# but some false friends slip back in.
REQUIRE_MEANING_MATCH = True

# A word's ranking is its true corpus frequency (how many times it occurs as a
# contiguous syllable n-gram in the Leipzig sentences), with the blended syllable
# frequency used only as a tie-breaker for words too rare to appear in the corpus.
# The integer ``Word.frequency`` packs the two so corpus count always dominates:
#   frequency = corpus_count * _CORPUS_COUNT_WEIGHT + syllable_tiebreaker
_CORPUS_COUNT_WEIGHT = 1_000_000
# Frequency assigned to a syllable that is absent from the frequency corpora, so
# that a word containing one rare syllable is still ranked (just very low).
_MISSING_SYLLABLE_FREQ = 1e-12
# Scales the geometric-mean syllable frequency (~1e-2..1e-8) into the integer
# tie-breaker range [0, _CORPUS_COUNT_WEIGHT).
_SYLLABLE_TIEBREAK_SCALE = 1e8
# Guard against pathological reading-combination blowups when reconstructing a
# word's Hán-Việt reading (chars with many readings * long words).
_MAX_READING_COMBINATIONS = 2000
# --------------------------------------------------------------------------

# Common English words ignored when checking whether a reconstructed word's gloss
# agrees with its CEDICT gloss (so the overlap reflects content, not function
# words).
_GLOSS_STOPWORDS = frozenset(
    "a an the to of and or in on for with by at as be is are was word "
    "person thing sth sb one's oneself etc cl variant".split()
)


def _norm(s: str) -> str:
    """Normalize a Hán-Việt syllable for comparison (NFC + lowercase + strip)."""
    return unicodedata.normalize("NFC", s.strip().lower())


def _gloss_tokens(text: str) -> Set[str]:
    """Content-word tokens of an English gloss, for semantic cross-checking."""
    return {t for t in re.findall(r"[a-z]+", text.lower()) if t not in _GLOSS_STOPWORDS}


# Minimum token length at which a shared prefix counts as agreement, so that
# "develop"/"development" or "nation"/"national" match without conflating short
# words.
_GLOSS_PREFIX_MIN = 4


def _gloss_agreement(a: Set[str], b: Set[str]) -> int:
    """Number of tokens in ``a`` that agree with some token in ``b`` -- exact
    match, or a shared prefix of at least ``_GLOSS_PREFIX_MIN`` characters (to
    forgive inflections and CEDICT/vnedict wording differences like
    develop/development)."""
    agree = 0
    for x in a:
        for y in b:
            if x == y or (
                len(x) >= _GLOSS_PREFIX_MIN
                and len(y) >= _GLOSS_PREFIX_MIN
                and (x.startswith(y) or y.startswith(x))
            ):
                agree += 1
                break
    return agree


#################
# Readings ######
#################


def _char_from_codepoint(token: str) -> str:
    """Convert a ``U+XXXX`` token (or a literal character) to a character."""
    token = token.strip()
    if token.upper().startswith("U+"):
        return chr(int(token[2:], 16))
    return token


def _load_winvnkey_readings() -> MutableMapping[str, Set[str]]:
    """Read the WinVNKey Hán-Việt databases into ``char -> {readings}``.

    Each file is tab- or space-delimited with ``# ...`` comment lines. The first
    field is either a ``U+XXXX`` codepoint or a literal han character; the second
    field is one or more comma-separated Hán-Việt readings.
    """
    char_to_prons: MutableMapping[str, Set[str]] = defaultdict(set)
    for path in VI_WINVNKEY_FILES:
        if not path.exists():
            logger.warning(f"Missing WinVNKey reading file: {path}")
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # split off the first whitespace-delimited field (the char)
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                char = _char_from_codepoint(parts[0])
                for pron in parts[1].split(","):
                    pron = _norm(pron)
                    if pron:
                        char_to_prons[char].add(pron)
    return char_to_prons


@cache
def get_han_viet_readings() -> Mapping[str, Set[str]]:
    """Return ``char -> {Hán-Việt readings}`` merged from Unihan + WinVNKey.

    Sources are unioned. Unihan ``kVietnamese`` is permissively licensed and used
    as the baseline; the WinVNKey databases add substantial extra coverage.
    """
    char_to_prons: MutableMapping[str, Set[str]] = defaultdict(set)

    unihan = get_unihan()
    unihan_chars = 0
    for char, entry in unihan.items():
        if readings := entry.get("kVietnamese"):
            unihan_chars += 1
            for pron in readings:
                char_to_prons[char].add(_norm(pron))
    logger.info(f"  Loaded Hán-Việt readings for {unihan_chars} chars from Unihan")

    winvnkey = _load_winvnkey_readings()
    for char, prons in winvnkey.items():
        char_to_prons[char].update(prons)
    logger.info(
        f"  Merged WinVNKey readings ({len(winvnkey)} chars); "
        f"{len(char_to_prons)} chars total"
    )

    return dict(char_to_prons)


#################
# Frequency #####
#################


def _download_leipzig_vi() -> None:
    have_words = LEIPZIG_VI_WORDS_FILE.exists() and LEIPZIG_VI_WORDS_FILE.stat().st_size
    have_sents = (
        LEIPZIG_VI_SENTENCES_FILE.exists() and LEIPZIG_VI_SENTENCES_FILE.stat().st_size
    )
    if have_words and have_sents:
        logger.debug(f"{LEIPZIG_VI_DIR.name} already extracted; skipping download")
        return
    if not (LEIPZIG_VI_TARBALL.exists() and LEIPZIG_VI_TARBALL.stat().st_size > 0):
        logger.info(f"Downloading Leipzig Vietnamese corpus to {LEIPZIG_VI_TARBALL}")
        r = requests.get(LEIPZIG_VI_URL, stream=True)
        with open(LEIPZIG_VI_TARBALL, "wb") as fd:
            for chunk in r.iter_content(chunk_size=8192):
                fd.write(chunk)
    LEIPZIG_VI_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(LEIPZIG_VI_TARBALL, "r:gz") as tar:
        for member in tar.getmembers():
            # flatten: strip the leading archive directory
            name = member.name.split("/")[-1]
            if name.endswith("-words.txt") or name.endswith("-sentences.txt"):
                member.name = name
                tar.extract(member, LEIPZIG_VI_DIR)


def _download_opensubs_vi() -> None:
    if OPENSUBS_VI_FILE.exists() and OPENSUBS_VI_FILE.stat().st_size > 0:
        logger.debug(f"{OPENSUBS_VI_FILE.name} already exists; skipping download")
        return
    logger.info(f"Downloading OpenSubtitles Vietnamese frequency to {OPENSUBS_VI_FILE}")
    r = requests.get(OPENSUBS_VI_URL)
    OPENSUBS_VI_FILE.write_bytes(r.content)


def _normalized(counts: Dict[str, int]) -> Dict[str, float]:
    """Turn raw counts into a probability (share of corpus tokens)."""
    total = sum(counts.values())
    if not total:
        return {}
    return {tok: c / total for tok, c in counts.items()}


def _read_leipzig_counts() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    with LEIPZIG_VI_WORDS_FILE.open(encoding="utf-8") as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                continue
            _rank, word, freq = fields
            word = word.strip().lower()
            if word.isalpha():  # keep Vietnamese syllables, drop punctuation/digits
                counts[word] = counts.get(word, 0) + int(freq)
    return counts


def _read_opensubs_counts() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    with OPENSUBS_VI_FILE.open(encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            word, freq = parts
            word = word.strip().lower()
            if word.isalpha():
                counts[word] = counts.get(word, 0) + int(freq)
    return counts


@cache
def get_vi_syllable_frequency() -> Mapping[str, float]:
    """Return ``syllable -> blended frequency score`` (higher = more common).

    Each corpus is normalized to a share-of-tokens probability, then combined
    with ``LEIPZIG_WEIGHT`` / ``OPENSUBS_WEIGHT``. A syllable missing from one
    corpus simply contributes 0 from that side.
    """
    _download_leipzig_vi()
    _download_opensubs_vi()

    leipzig = _normalized(_read_leipzig_counts())
    opensubs = _normalized(_read_opensubs_counts())
    total_weight = LEIPZIG_WEIGHT + OPENSUBS_WEIGHT

    scores: Dict[str, float] = {}
    for syl in set(leipzig) | set(opensubs):
        blended = (
            LEIPZIG_WEIGHT * leipzig.get(syl, 0.0)
            + OPENSUBS_WEIGHT * opensubs.get(syl, 0.0)
        ) / total_weight
        scores[syl] = blended

    logger.info(
        f"  Blended VI syllable frequency for {len(scores)} syllables "
        f"(Leipzig={len(leipzig)}, OpenSubtitles={len(opensubs)})"
    )
    return scores


#################
# Vocabulary ####
#################


@cache
def _unihan_han_viet_readings() -> Mapping[str, Set[str]]:
    """char -> {Hán-Việt readings}, strictly from Unihan ``kVietnamese``.

    Unlike the merged ``get_han_viet_readings``, this excludes the WinVNKey
    databases, which mix in Nôm (phonetic-loan) readings. Using the strict Sino
    readings keeps the reconstructed Sino-Vietnamese vocabulary genuine.
    """
    unihan = get_unihan()
    return {
        c: {_norm(x) for x in e["kVietnamese"]}
        for c, e in unihan.items()
        if e.get("kVietnamese")
    }


@cache
def _vnedict_glosses() -> Mapping[str, Set[str]]:
    """Normalized Vietnamese headword -> set of English gloss tokens, from vnedict.

    Membership in this mapping means the headword is an attested Vietnamese word;
    the gloss tokens let us check that a reconstructed reading actually means what
    its source Chinese word means (see ``_reconstruct_han_viet_reading``).
    """
    _download_vnedict()
    glosses: MutableMapping[str, Set[str]] = defaultdict(set)
    with VNEDICT_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            headword, _, gloss = line.partition(":")
            glosses[_norm(headword)].update(_gloss_tokens(gloss))
    return glosses


def _download_vnedict() -> None:
    if VNEDICT_FILE.exists() and VNEDICT_FILE.stat().st_size > 0:
        logger.debug(f"{VNEDICT_FILE.name} already exists; skipping download")
        return
    logger.info(f"Downloading vnedict to {VNEDICT_FILE}")
    r = requests.get(VNEDICT_URL)
    VNEDICT_FILE.write_bytes(r.content)


def _reconstruct_han_viet_reading(
    chars: List[str],
    char_to_readings: Mapping[str, Set[str]],
    vnedict: Mapping[str, Set[str]],
    meaning_tokens: Set[str] = frozenset(),  # type: ignore[assignment]
    preferred_readings: Mapping[str, Set[str]] = None,  # type: ignore[assignment]
) -> Tuple[str, ...]:
    """Assign each character a Hán-Việt reading so the joined Quốc-Ngữ form is an
    attested Vietnamese word, and (given ``meaning_tokens`` from the source word's
    gloss) whose *meaning* matches. Returns the syllable tuple, or ``()`` if none.

    When several readings spell attested words (e.g. 市長 -> "thị trưởng" mayor vs
    the coincidental "thị trường" market), the one whose vnedict gloss shares the
    most content words with the source gloss wins, avoiding meaning mismatches.
    Ties are then broken toward ``preferred_readings`` (the standard Unihan Sino
    readings), so a rarer WinVNKey reading is only used when the meaning demands it.
    """
    reading_options = [sorted(char_to_readings[c]) for c in chars]
    if prod(len(o) for o in reading_options) > _MAX_READING_COMBINATIONS:
        return ()
    best: Tuple[str, ...] = ()
    best_key = (-1, -1)
    for combo in itertools.product(*reading_options):
        gloss_tokens = vnedict.get(" ".join(combo))
        if gloss_tokens is None:
            continue
        overlap = _gloss_agreement(meaning_tokens, gloss_tokens)
        n_preferred = (
            sum(s in preferred_readings.get(c, ()) for c, s in zip(chars, combo))
            if preferred_readings
            else 0
        )
        key = (overlap, n_preferred)
        if key > best_key:
            best_key = key
            best = combo
    return best


_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _count_corpus_word_frequency(
    prons: Sequence[Tuple[str, ...]]
) -> Mapping[Tuple[str, ...], int]:
    """Count how often each Quốc-Ngữ word (a tuple of syllables) occurs as a
    contiguous token n-gram in the Leipzig sentence corpus. This is a genuine
    per-*word* frequency, which per-syllable lists cannot provide."""
    _download_leipzig_vi()

    wanted: MutableMapping[int, Set[Tuple[str, ...]]] = defaultdict(set)
    for p in prons:
        wanted[len(p)].add(p)
    lengths = sorted(wanted)
    counts: Counter = Counter()

    logger.info(f"  Counting word frequencies in {LEIPZIG_VI_SENTENCES_FILE.name}...")
    with LEIPZIG_VI_SENTENCES_FILE.open(encoding="utf-8") as f:
        for line in f:
            _id, _, text = line.partition("\t")
            if not text:
                continue
            toks = [_norm(t) for t in _TOKEN_RE.findall(text.lower())]
            for i in range(len(toks)):
                for n in lengths:
                    if i + n > len(toks):
                        break
                    ngram = tuple(toks[i : i + n])
                    if ngram in wanted[n]:
                        counts[ngram] += 1
    return counts


@dataclass
class HanVietData:
    # example vocabulary (Chinese words confirmed to be Vietnamese words),
    # sorted by descending frequency
    words: List[Word]
    # char -> {Hán-Việt readings actually used by the vocabulary}
    char_to_readings: Mapping[str, Set[str]]
    # char -> ordering score (higher = more useful/common)
    char_to_score: Mapping[str, int]


@cache
def get_han_viet_data() -> HanVietData:
    """Build the Sino-Vietnamese vocabulary and character inventory.

    A word qualifies if it is a multi-character CEDICT (Chinese) word, every
    character has a Unihan Hán-Việt reading, and some assignment of those
    readings spells a word that vnedict confirms is actually Vietnamese (with a
    matching meaning). This yields genuine Sino-Vietnamese vocabulary with real
    Hán tự spellings, Hán-Việt readings, and English glosses -- all from
    permissively-licensed sources.

    Words are ranked by their true corpus frequency (occurrences as a contiguous
    syllable n-gram in the Leipzig sentences), so the most common, good-to-know
    words are chosen as examples for each character; the blended syllable
    frequency only breaks ties among words too rare to appear in the corpus.
    """
    # Use the merged readings (Unihan ∪ WinVNKey) as candidates so legitimate
    # alternate readings (e.g. 長 "trưởng") are available, but prefer the standard
    # Unihan Sino readings when meaning doesn't force otherwise.
    hv_readings = get_han_viet_readings()
    unihan_readings = _unihan_han_viet_readings()
    vnedict = _vnedict_glosses()
    syl_freq = get_vi_syllable_frequency()

    # Phase 1: reconstruct candidate Sino-Vietnamese words.
    candidates = []  # (surface, english, combo)
    char_to_readings: MutableMapping[str, Set[str]] = defaultdict(set)
    for zh_word in get_cedict():
        chars = list(zh_word.surface)
        if len(chars) < 2 or any(c not in hv_readings for c in chars):
            continue
        meaning = _gloss_tokens(zh_word.english)
        combo = _reconstruct_han_viet_reading(
            chars, hv_readings, vnedict, meaning, unihan_readings
        )
        if not combo:
            continue
        # Keep a word only if its meaning is confirmed -- its vnedict gloss agrees
        # with the source (Chinese) gloss -- rejecting false reading matches (扇子
        # "fan" mis-read as "thiên tử" son-of-heaven) and false friends where the
        # reading coincides with an unrelated common word (求取 "to seek" spelling
        # "cầu thủ" athlete). When REQUIRE_MEANING_MATCH is relaxed, also keep
        # words spelled with only standard Unihan readings (see the constant).
        meaning_confirmed = bool(_gloss_agreement(meaning, vnedict[" ".join(combo)]))
        if not meaning_confirmed:
            if REQUIRE_MEANING_MATCH:
                continue
            all_standard = all(
                s in unihan_readings.get(c, ()) for c, s in zip(chars, combo)
            )
            if not all_standard:
                continue
        candidates.append((zh_word.surface, zh_word.english, combo))
        for c, s in zip(chars, combo):
            char_to_readings[c].add(s)

    # Phase 2: count true per-word corpus frequency for the candidate readings.
    corpus_freq = _count_corpus_word_frequency([c[2] for c in candidates])

    # Phase 3: assemble Words, packing corpus count (primary) and syllable
    # frequency (tie-breaker for corpus-absent words) into one integer.
    words: List[Word] = []
    for i, (surface, english, combo) in enumerate(candidates, start=1):
        geo_mean = prod(syl_freq.get(s, _MISSING_SYLLABLE_FREQ) for s in combo) ** (
            1 / len(combo)
        )
        frequency = corpus_freq.get(combo, 0) * _CORPUS_COUNT_WEIGHT + min(
            _CORPUS_COUNT_WEIGHT - 1, round(geo_mean * _SYLLABLE_TIEBREAK_SCALE)
        )
        words.append(Word(surface, f"hv-{i}", " ".join(combo), english, frequency))

    words.sort(key=lambda w: (-w.frequency, w.surface))

    # A character's ordering score is the frequency of its most common word.
    char_to_score: MutableMapping[str, int] = defaultdict(int)
    for w in words:
        for c in w.surface:
            if w.frequency > char_to_score[c]:
                char_to_score[c] = w.frequency

    covered = sum(1 for w in words if w.frequency >= _CORPUS_COUNT_WEIGHT)
    logger.info(
        f"  Built {len(words)} Hán-Việt words over {len(char_to_readings)} "
        f"characters ({covered} words attested in the corpus)"
    )
    return HanVietData(words, dict(char_to_readings), dict(char_to_score))


def get_char_keyword(char: str) -> str:
    """A short English keyword/gloss for a character, from Unihan kDefinition."""
    definition = get_unihan().get(char, {}).get("kDefinition")
    if not definition:
        return ""
    # kDefinition is a list of senses; keep it compact
    return definition[0] if isinstance(definition, list) else str(definition)


if __name__ == "__main__":
    # Regenerate the merged reading table and print a coverage report for review.
    from uniunihan_db.data.paths import VI_READINGS_FILE
    from uniunihan_db.util import configure_logging

    configure_logging(__name__)

    readings = get_han_viet_readings()
    unihan = get_unihan()

    with VI_READINGS_FILE.open("w", encoding="utf-8") as f:
        f.write("char\tcodepoint\treadings\n")
        for char in sorted(readings):
            cp = f"U+{ord(char):04X}"
            f.write(f"{char}\t{cp}\t{'|'.join(sorted(readings[char]))}\n")

    freq = get_vi_syllable_frequency()
    # how many reading-bearing chars are "Sinitic" (have a Mandarin reading)?
    sinitic = sum(
        1
        for c in readings
        if any(k in unihan.get(c, {}) for k in ("kMandarin", "kHanyuPinyin"))
    )
    reading_syllables = {p for prons in readings.values() for p in prons}
    covered = sum(1 for s in reading_syllables if s in freq)
    logger.info("=== VI data coverage report ===")
    logger.info(f"chars with a Hán-Việt reading: {len(readings)}")
    logger.info(f"  of which Sinitic (has Mandarin reading in Unihan): {sinitic}")
    logger.info(f"distinct Hán-Việt reading syllables: {len(reading_syllables)}")
    logger.info(f"  of those found in frequency data: {covered}")
    logger.info(f"wrote merged readings to {VI_READINGS_FILE}")
