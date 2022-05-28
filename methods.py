"""Inject new methods into existing FAdo classes

save_pdkey() -> Recursively compute and save a unique key for each regexp
                as the attribute "pdkey"
keyed_pds() -> KeyedSet of partial derivatives
"""

from FAdo.reex import *

class KeyedSet:
    """A simple implementation of a unique set where every object is expected
    to be identifiable by its attribute `key`
    """
    def __init__(self, key: str, iter=[]):
        self.keys = set() # identifying distinct elements
        self.set = list() # fast adding
        self.key = key
        for item in iter:
            self.add(item)

    def __iter__(self):
        return iter(self.set)

    def add(self, obj):
        before = len(self.keys)
        self.keys.add(getattr(obj, self.key))
        if len(self.keys) > before:
            self.set.append(obj)


class SavePDKey:
    # SIMPLE CASES
    def atom(self):
        self.pdkey = self.val
        return self.pdkey

    def epsilon(self):
        self.pdkey = Epsilon
        return Epsilon

    def emptyset(self):
        self.pdkey = EmptySet
        return EmptySet

    # COMPOSITE CASES
    def concat(self):
        self.pdkey = f".{self.arg1.save_pdkey()}{self.arg2.save_pdkey()}"
        return self.pdkey

    def disj(self):
        self.pdkey = f"+{self.arg1.save_pdkey()}{self.arg2.save_pdkey()}"
        return self.pdkey

    def star(self):
        self.pdkey = f"*{self.arg.save_pdkey()}"
        return self.pdkey

CAtom.save_pdkey = SavePDKey.atom
CEpsilon.save_pdkey = SavePDKey.epsilon
CEmptySet.save_pdkey = SavePDKey.emptyset
CConcat.save_pdkey = SavePDKey.concat
CDisj.save_pdkey = SavePDKey.disj
CStar.save_pdkey = SavePDKey.star


class PD:
    # SIMPLE CASES
    def atom(self, symbol):
        pds = KeyedSet("pdkey")
        if self.val == symbol:
            new_pd = CEpsilon(self.Sigma)
            new_pd.pdkey = Epsilon
            pds.add(new_pd)
        return pds

    def epsilon(self, symbol):
        return KeyedSet("pdkey")

    def emptyset(self, symbol):
        return KeyedSet("pdkey")

    # COMPOSITE CASES
    def concat(self, symbol):
        pds = KeyedSet("pdkey")
        for pd in self.arg1.keyed_pds(symbol):
            if pd.emptysetP():
                pass
            elif pd.epsilonP():
                pds.add(self.arg2)
            else:
                new_pd = CConcat(pd, self.arg2, self.Sigma)
                new_pd.pdkey = f".{pd.pdkey}{self.arg2.pdkey}"
                pds.add(new_pd)
        if self.arg1.ewp():
            for pd in self.arg2.keyed_pds(symbol):
                pds.add(pd)
        return pds

    def disj(self, symbol):
        pds = self.arg1.keyed_pds(symbol)
        for pd in self.arg2.keyed_pds(symbol):
            pds.add(pd)
        return pds

    def star(self, symbol):
        pds = KeyedSet("pdkey")
        for pd in self.arg.keyed_pds(symbol):
            if pd.emptysetP():
                pass
            elif pd.epsilonP():
                pds.add(self)
            else:
                new_pd = CConcat(pd, self, self.Sigma)
                new_pd.pdkey = f".{pd.pdkey}{self.arg.pdkey}"
                pds.add(new_pd)
        return pds

CAtom.keyed_pds = PD.atom
CEpsilon.keyed_pds = PD.epsilon
CEmptySet.keyed_pds = PD.emptyset
CConcat.keyed_pds = PD.concat
CDisj.keyed_pds = PD.disj
CStar.keyed_pds = PD.star






"""Create the membership evaluation functions with the signature:
    f(tree: RegExp, word: str) -> bool

Each function is decorated in a process_`timer`. So calling f actually
returns a 2-tuple: (bool result, CPU time taken)
"""

from copy import deepcopy
from functools import wraps
from time import process_time
from FAdo.reex import RegExp

def timer(func):
    @wraps(func)
    def f(*args):
        ti = process_time()
        result = func(*args)
        tf = process_time()
        return result, tf - ti
    return f

@timer
def Derivative(tree: RegExp, word: str) -> bool:
    """Word derivatives; maintain a single current regexp"""
    return tree.evalWordP(word)

@timer
def pddag(tree: RegExp, word: str) -> bool:
    """First convert into partial derivative NFA, then execute membership"""
    return tree.nfaPDDAG().evalWordP(word)

@timer
def pdset(tree: RegExp, word: str) -> bool:
    """Typical partial derivative set implementation"""
    current = set([tree])
    for symbol in word:
        next = set()
        for re in current:
            for pd in re.partialDerivatives(symbol):
                next.add(pd)
        current = next
    return any(map(lambda pd: pd.ewp(), current))

@timer
def pdlist(tree: RegExp, word: str) -> bool:
    """Like pdset, but using lists instead of sets"""
    current = [tree]
    for symbol in word:
        next = list()
        for re in current:
            for pd in re.partialDerivatives(symbol):
                next.append(pd)
        current = next
    return any(map(lambda pd: pd.ewp(), current))

@timer
def pdfast(tree: RegExp, word: str) -> bool:
    """Optimized partial derivatives using KeyedSets instead"""
    tree = deepcopy(tree) # deepcopied so attribute `pdkey` is not created on the passed regexp
    tree.save_pdkey()
    current = KeyedSet("pdkey", [tree])
    for symbol in word:
        next = KeyedSet("pdkey")
        for re in current:
            for pd in re.keyed_pds(symbol):
                next.add(pd)
        current = next
    return any(map(lambda pd: pd.ewp(), current))

@timer
def follow(tree: RegExp, word: str) -> bool:
    """Follow construction then evaluate NFA membership. This has experimentally been proven to be fast"""
    return tree.nfaFollow().evalWordP(word)


METHODS = [Derivative, pddag, pdset, pdlist, pdfast, follow]