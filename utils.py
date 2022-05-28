from functools import cache
from dataclasses import dataclass
from typing import Callable, TypeVar, Type, List
import subprocess
import random
import yaml
import json
from FAdo.reex import *
from FAdo.cfg import smallAlphabet
from methods import METHODS


@dataclass
class _GenConfig:
    alphabet_size: int
    alphabet: set[str]
    epsilon: bool
    empty: bool
    lengths: list[int]
    per_length: int

@dataclass
class _FileConfig:
    regexps: str
    regexps_todo: str
    data_output: str

@dataclass
class Config:
    gen: _GenConfig
    multiprocessing: int
    files: _FileConfig


@cache
def config() -> Config:
    """Gets the configuration options"""
    handle = open("config.yaml", "r")
    cfg = yaml.safe_load(handle)
    handle.close()

    return Config(
        gen=_GenConfig(
            alphabet_size=cfg["gen"]["alphabet_size"],
            alphabet=set(smallAlphabet(cfg["gen"]["alphabet_size"])),
            epsilon=None if cfg["gen"]["epsilon"] is False else True,
            empty=None if cfg["gen"]["empty"] is False else True,
            lengths=cfg["gen"]["lengths"],
            per_length=cfg["gen"]["per_length"]
        ),
        multiprocessing=cfg["multiprocessing"],
        files=_FileConfig(**dict((k, f"data/{v}") for k, v in cfg["files"].items()))
    )


_T = TypeVar("_T")
class OutputFileEntry:
    """A class to simplify io to the output file"""
    regexp: str
    length: int
    nwords_acc: int
    nwords_rej: int
    avg_word_length: float

    def __init__(self, **kwargs):
        for method in METHODS:
            setattr(self, self.method_time_key(method), 0.0)

        for attr, cls in self.__annotations__.items():
            if attr in kwargs:
                setattr(self, attr, cls(kwargs[attr]))
            elif not hasattr(self, attr):
                raise Exception(f"Must provide kwarg {attr}")

    @staticmethod
    def properties():
        """The column names of the output file"""
        try:
            return OutputFileEntry.props
        except AttributeError:
            OutputFileEntry.props = sorted(OutputFileEntry.__annotations__.keys())
            return OutputFileEntry.props

    @staticmethod
    def method_time_key(method: Callable) -> str:
        return f"time4{method.__name__}"

    @classmethod
    def from_csv_str(cls: Type[_T], string: str) -> _T:
        """Parse an OutputFileEntry from a csv string
        Note: this string should not end with a line delimiter
        """
        d = dict()
        elements = string.split(",")
        props = OutputFileEntry.properties()
        for i in range(len(elements)):
            d[props[i]] = elements[i]

        return OutputFileEntry(**d)

    def to_csv_line(self) -> str:
        r"""Converts self to a string. When writing to a file make sure to add a \n"""
        return ",".join(str(getattr(self, prop)) for prop in self.properties())

    @classmethod
    def from_json_str(cls: Type[_T], string: str) -> _T:
        """Parse an OutputFileEntry from a json string"""
        return OutputFileEntry(**json.loads(string))

    def to_json(self) -> str:
        """Converts self to a minified json string"""
        return json.dumps(self.as_dict(), separators=(",", ":"))

    def add_time(self, func, time: float):
        """Adds time to a specific method given a method function"""
        key = f"time4{func.__name__}"
        setattr(self, key, getattr(self, key) + time)

    def get_time(self, func) -> float:
        """Gets the current time of a specific method"""
        return getattr(self, self.method_time_key(func))

    def as_dict(self) -> dict:
        """Returns self as a dictionary"""
        return dict((prop, getattr(self, prop)) for prop in self.properties())

# Dynamically inject additional annotations based on METHODS used
for method in METHODS:
    OutputFileEntry.__annotations__[OutputFileEntry.method_time_key(method)] = float


def radix_sort(language):
    """Sorts a language by length, and then by alphabetic order (ascending)"""
    lengths = dict()
    for word in language:
        crossection = lengths.get(len(word), list())
        crossection.append(word)
        lengths[len(word)] = crossection

    lang = list()
    for l in sorted(lengths.keys()):
        lang.extend(sorted(lengths[l]))

    return lang


def _concat_pict(*arr: List[set[str]]) -> set[str]:
    """Uses Microsoft's PICT command-line tool to find pairwise coverage
    for a given list of languages `arr`
    """
    fname = f"tmp/pict_{os.getpid()}.txt"
    output = ""
    for num, words in enumerate(arr):
        output += f"{num}: {', '.join(w if len(w)>0 else '_' for w in words)}\n"

    try:
        with open(fname, "w") as handle:
            handle.write(output)
    except FileNotFoundError:
        os.mkdir("tmp")
        with open(fname, "w") as handle:
            handle.write(output)
    finally:
        results = subprocess.check_output(["pict", fname], encoding="utf-8")
        return set(word.replace("\t", "").replace("_", "") for word in results.splitlines()[1:])


def get_random_sample(population, n: int):
    """Retrieve up to n items from population selected without replacement.
    Throw away and clear all non-selected items.
    """
    t = type(population)
    if t is not list:
        population = list(population)

    rnd = random.Random(1)
    indices = list(range(0, len(population)))
    rnd.shuffle(indices)

    sample = [population[i] for i in indices[:n]]
    population.clear()
    return t(sample)


def pairwise_language_generation(sre, maxsize: int=2_048) -> set[str]:
    """Finds a set of accepted words for the regular expression.
    Note this expects a SRE tree to take full advantage of pairwise features.

    Lixiao Zheng, Shuai Ma, Yuanyang Wang, and Gang Lin.
    "String Generation for Testing Regular Expressions"
    The Computer Journal, Vol. 63 No. 1, 2020

    Inspired from that paper. Note star repetitions are taken 0, 1, and 3 times.

    Example:
        >>> pairwise_language_generation(str2sre("(a+b+c)(d+e)(f+g+h)"))
        {'aeg', 'beg', 'cdg', 'adh', 'ceh', 'bef', 'adf', 'bdh', 'cdf'}
    """
    t = type(sre)
    if t is CAtom:
        return set([sre.val])
    elif t is CEpsilon:
        return set([""])
    elif t is CEmptySet:
        return set()
    elif t is SDisj:
        lang = set()
        for child in sre.arg:
            lang.update(pairwise_language_generation(child))
        if len(lang) > maxsize:
            lang = get_random_sample(lang, maxsize)
        return lang
    elif t is SStar:
        lang = pairwise_language_generation(sre.arg)
        lang.add("")
        lang.update(_concat_pict(lang, lang, lang))
        if len(lang) > maxsize:
            lang = get_random_sample(lang, maxsize)
        return lang
    elif t is SConcat:
        lang = _concat_pict(*[ pairwise_language_generation(child) for child in sre.arg ])
        if len(lang) > maxsize:
            lang = get_random_sample(lang, maxsize)
        return lang
    else:
        raise NotImplementedError()


def find_rejected_words(evalWordP: Callable[[str], bool], accepted: set[str]) -> set[str]:
    """Delete characters from accepting words to create potentially rejecting words.
    The returned set of rejecting words have been tested for membership, and are edit distance
    one away from an accepting word (aka the word is "close" to in the language and it is
    unlikely that membership can be decided trivially).

    How?
        1. Given a set of accepting words, create a dictionary by word length which maps to a
            2-tuple (R, L) where:   R is random order from [0, |w|)
                                    L is the all words from accepted of length |w|
        2. For each word length choose a symbol index to delete.
        3. Delete the appropriate index from each word in accepted.
        4. Stop if there are no more unique indices to delete or we have found as many rejecting
            as accepting words.
    """
    rnd = random.Random(1)
    acclen = dict()
    for word in accepted:
        crossection = acclen.get(len(word), list())
        crossection.append(word)
        acclen[len(word)] = crossection
    for length in acclen:
        order = list(range(0, len(acclen[length][0])))
        rnd.shuffle(order)
        acclen[length] = (order, acclen[length])

    # edge case: cannot delete from the empty word
    if 0 in acclen:
        del acclen[0]

    rejected = set()
    while len(acclen) > 0:
        for length in acclen.copy():
            order, lang = acclen[length]
            i = order.pop()
            if len(order) == 0:     # there are no more indices to delete for this cross-section
                del acclen[length]

            for word in lang:
                w = word[:i] + word[i+1:]
                if not evalWordP(w):
                    rejected.add(w)
                    if len(rejected) == len(accepted): # enough words have been found
                        return rejected

    return rejected


def min_word_length(tree: RegExp) -> int|float:
    """Find the minimum word length of the language.
    Returns float("inf") if empty
    """
    t = type(tree)
    if t is CAtom:
        return 1
    elif t in [CEpsilon, CStar, SStar]:
        return 0
    elif t is CDisj:
        return min(min_word_length(tree.arg1), min_word_length(tree.arg2))
    elif t is SDisj:
        return min(map(lambda child: min_word_length(child), tree.arg))
    elif t is CConcat:
        return min_word_length(tree.arg1) + min_word_length(tree.arg2)
    elif t is SConcat:
        return sum(map(lambda child: min_word_length(child), tree.arg))
    elif t is CEmptySet: # MAYBE
        return float("inf")
    else:
        raise NotImplementedError()
