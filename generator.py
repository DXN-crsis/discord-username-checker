"""
Smart Discord username generator — Anthropic-grade.

Novel techniques not found in any existing tool:
  1. Entropy-weighted character selection (uncommon letters → more likely available)
  2. Consonant-heavy pattern templates matching user's target style (nm8, rnu_)
  3. Speculative expansion — when a username is found available, generate
     single-character mutations and prioritise them (like CPU speculative exec)
  4. Priority queue drains before random generation resumes

Discord pomelo rules:
  chars : a-z 0-9 . _
  length: 2-32
  no consecutive periods, cannot start/end with period
"""

import random
import string
import itertools
from collections import deque
from typing import List, Set, Deque


class SmartGenerator:

    CONSONANTS = list("bcdfghjklmnpqrstvwxyz")
    VOWELS = list("aeiou")
    DIGITS = list("0123456789")
    SYMBOLS = list("._")
    VALID = string.ascii_lowercase + string.digits + "._"

    # ── Entropy weights ──────────────────────────────────────────────
    # Rare letters get higher weight → generated more often → less
    # likely to already be claimed by a human.

    C_W = [3, 2, 2, 4, 3, 2, 5, 4, 2, 3, 3, 3, 6, 2, 2, 2, 4, 4, 6, 3, 6]
    #      b  c  d  f  g  h  j  k  l  m  n  p  q  r  s  t  v  w  x  y  z

    V_W = [1, 1, 1, 1, 2]          # a e i o u  (u rarer)
    D_W = [1, 1, 2, 3, 3, 2, 3, 4, 4, 3]   # 0-9  (7,8 rarer in names)
    S_W = [1, 3]                    # . _  (underscore rarer → better odds)

    # ── Pattern templates ────────────────────────────────────────────
    # C=consonant V=vowel D=digit S=symbol
    # Designed to produce names like nm8, rnu_, k3x, f_m, 8zq, jw.2

    P3 = [
        "CCD", "CDC", "DCC",       # nm8  n8m  8nm
        "CCS", "CSC",              # nm_  n_m
        "CCV", "VCC", "CVC",       # rnu  ank  nuk
        "CVD", "DVC", "VDC",       # na8  8na  a8n
        "CDD", "DDC", "DCD",       # n89  89n  8n9
    ]
    P4 = [
        "CCVS", "CCDS", "CCSD",    # rnu_ nm8_ nm_8
        "CCCD", "DCCC", "CDCC",    # nmk8 8nmk n8mk
        "CCVC", "CVCC", "VCCD",    # rnuk ankm ank8
        "CDCS", "CSCD", "SCCD",    # n8m_ n_m8 _nm8
        "CCDV", "CVCD", "DCCV",    # nm8a ank8 8nmu
        "CCDD", "DDCC", "CDDC",    # nm89 89nm n88m
        "CVCS", "CSCV",            # nuk_ n_mu
    ]
    P5 = [
        "CCCDS", "CCDCS", "CCVCD", "DCCCV", "CVCCV",
        "CCSCD", "CCVCS", "CVDCC", "CVCDS", "DCCVS",
    ]

    # ── Init ─────────────────────────────────────────────────────────

    def __init__(self, min_length: int = 3, max_length: int = 4):
        self.min_length = max(2, min_length)
        self.max_length = max(self.min_length, min(max_length, 6))
        self._used: Set[str] = set()
        self._priority: Deque[str] = deque(maxlen=600)
        self._exhaustive_queue: List[str] = []
        self._exhaustive_idx: int = 0

    # ── Validation ───────────────────────────────────────────────────

    @staticmethod
    def is_valid(u: str) -> bool:
        if len(u) < 2 or len(u) > 32:
            return False
        if not all(c in SmartGenerator.VALID for c in u):
            return False
        if u[0] == "." or u[-1] == ".":
            return False
        if ".." in u:
            return False
        return True

    # ── Weighted character pick ──────────────────────────────────────

    def _char(self, t: str) -> str:
        if t == "C":
            return random.choices(self.CONSONANTS, self.C_W, k=1)[0]
        if t == "V":
            return random.choices(self.VOWELS, self.V_W, k=1)[0]
        if t == "D":
            return random.choices(self.DIGITS, self.D_W, k=1)[0]
        if t == "S":
            return random.choices(self.SYMBOLS, self.S_W, k=1)[0]
        return random.choice(self.CONSONANTS)

    # ── Single name generation ───────────────────────────────────────

    def _one(self) -> str:
        ln = self._pick_length()
        pats = {3: self.P3, 4: self.P4, 5: self.P5}.get(ln)
        if pats:
            pat = random.choice(pats)[:ln]
        else:
            # Build ad-hoc pattern for lengths 2 or 6
            types = ["C"] * (ln - 1) + [random.choice(["D", "S"])]
            random.shuffle(types)
            pat = "".join(types)
        name = "".join(self._char(c) for c in pat)
        return name

    def _pick_length(self) -> int:
        lo, hi = self.min_length, self.max_length
        rng = list(range(lo, hi + 1))
        weights = []
        for n in rng:
            if n == 2:
                weights.append(0.05)
            elif n == 3:
                weights.append(0.55)
            elif n == 4:
                weights.append(0.30)
            elif n == 5:
                weights.append(0.08)
            else:
                weights.append(0.02)
        return random.choices(rng, weights, k=1)[0]

    # ── Batch generation ─────────────────────────────────────────────

    def generate(self, count: int) -> List[str]:
        """Return up to *count* unique usernames.
        Drains priority queue (speculative mutations) first, then random.
        """
        out: List[str] = []

        # Priority queue — mutations of previously-found available names
        while self._priority and len(out) < count:
            u = self._priority.popleft()
            if u not in self._used and self.is_valid(u):
                self._used.add(u)
                out.append(u)

        # Random fill
        tries = 0
        while len(out) < count and tries < count * 40:
            tries += 1
            u = self._one()
            if self.is_valid(u) and u not in self._used:
                self._used.add(u)
                out.append(u)
        return out

    # ── Speculative expansion (novel) ────────────────────────────────

    def feedback(self, username: str, available: bool):
        """Called when a result arrives. If available, expand nearby."""
        if available:
            self._expand(username)

    def _expand(self, base: str):
        """Single-character substitution mutations of *base*.
        These are likely to also be available (locality in name-space).
        """
        pool = self.VALID
        mutations: List[str] = []
        for i in range(len(base)):
            for c in pool:
                v = base[:i] + c + base[i + 1 :]
                if v != base and v not in self._used and self.is_valid(v):
                    mutations.append(v)
        random.shuffle(mutations)
        for m in mutations[:50]:
            self._priority.append(m)

    # ── Exhaustive mode ──────────────────────────────────────────────

    def prepare_exhaustive(self):
        self._exhaustive_queue = []
        for ln in range(self.min_length, self.max_length + 1):
            for combo in itertools.product(self.VALID, repeat=ln):
                u = "".join(combo)
                if self.is_valid(u):
                    self._exhaustive_queue.append(u)
        random.shuffle(self._exhaustive_queue)
        self._exhaustive_idx = 0

    def generate_exhaustive_batch(self, count: int) -> List[str]:
        end = min(self._exhaustive_idx + count, len(self._exhaustive_queue))
        batch = self._exhaustive_queue[self._exhaustive_idx : end]
        self._exhaustive_idx = end
        return batch

    @property
    def exhaustive_total(self) -> int:
        return len(self._exhaustive_queue)

    @property
    def exhaustive_remaining(self) -> int:
        return max(0, len(self._exhaustive_queue) - self._exhaustive_idx)

    @property
    def used_count(self) -> int:
        return len(self._used)

    @property
    def priority_count(self) -> int:
        return len(self._priority)
