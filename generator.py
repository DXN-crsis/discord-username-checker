"""
Discord username generator - semi-triliteral usernames with numbers and symbols.
Generates short, human-unpredictable usernames following Discord's pomelo rules.

Rules:
  - Allowed chars: a-z, 0-9, period (.), underscore (_)
  - Length: 2-32
  - No consecutive periods (..)
  - Cannot start or end with period
  - Case insensitive (forced lowercase)
"""

import random
import string
import itertools
from typing import List, Set


class UsernameGenerator:
    LETTERS = string.ascii_lowercase
    DIGITS = string.digits
    VALID_CHARS = LETTERS + DIGITS + '._'

    def __init__(self, min_length: int = 2, max_length: int = 4):
        self.min_length = max(2, min_length)
        self.max_length = max(self.min_length, min(max_length, 6))
        self._used: Set[str] = set()
        self._exhaustive_queue: List[str] = []
        self._exhaustive_index: int = 0

    @staticmethod
    def is_valid(username: str) -> bool:
        if len(username) < 2 or len(username) > 32:
            return False
        if not all(c in string.ascii_lowercase + string.digits + '._' for c in username):
            return False
        if username.startswith('.') or username.endswith('.'):
            return False
        if '..' in username:
            return False
        return True

    # ── Random generation ────────────────────────────────────────────

    def _rand_2(self) -> str:
        """2-char username (no period allowed at edges, so only _ as symbol)."""
        pool = self.LETTERS + self.DIGITS + '_'
        return random.choice(pool) + random.choice(pool)

    def _rand_3_mid_symbol(self) -> str:
        """3-char: [alphanum] [. or _] [alphanum]  — symbol in the middle."""
        edge = self.LETTERS + self.DIGITS
        return random.choice(edge) + random.choice('._') + random.choice(edge)

    def _rand_3_free(self) -> str:
        """3-char with any valid arrangement."""
        while True:
            u = ''.join(random.choice(self.VALID_CHARS) for _ in range(3))
            if self.is_valid(u):
                return u

    def _rand_4(self) -> str:
        """4-char with one symbol placed randomly (valid position)."""
        edge = self.LETTERS + self.DIGITS
        symbol = random.choice('._')
        parts = [random.choice(edge) for _ in range(3)]
        if symbol == '.':
            pos = random.randint(1, 2)  # not first or last
        else:
            pos = random.randint(0, 3)
        parts.insert(pos, symbol)
        return ''.join(parts)

    def _rand_longer(self, length: int) -> str:
        """5-6 char username with 1-2 symbols."""
        while True:
            u = ''.join(random.choice(self.VALID_CHARS) for _ in range(length))
            if self.is_valid(u):
                return u

    def generate_random(self, count: int) -> List[str]:
        """Generate a batch of unique random usernames."""
        results: List[str] = []
        attempts = 0
        max_attempts = count * 30

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            length = random.choices(
                range(self.min_length, self.max_length + 1),
                weights=self._length_weights(),
                k=1,
            )[0]

            if length == 2:
                u = self._rand_2()
            elif length == 3:
                # 70% mid-symbol pattern, 30% free
                u = self._rand_3_mid_symbol() if random.random() < 0.7 else self._rand_3_free()
            elif length == 4:
                u = self._rand_4()
            else:
                u = self._rand_longer(length)

            if self.is_valid(u) and u not in self._used:
                self._used.add(u)
                results.append(u)

        return results

    def _length_weights(self) -> List[float]:
        """Weight shorter lengths more heavily — they're more valuable."""
        weights = []
        for l in range(self.min_length, self.max_length + 1):
            if l == 2:
                weights.append(0.10)
            elif l == 3:
                weights.append(0.60)
            elif l == 4:
                weights.append(0.25)
            else:
                weights.append(0.05)
        return weights

    # ── Exhaustive generation ────────────────────────────────────────

    def prepare_exhaustive(self):
        """Build a shuffled list of ALL valid usernames in [min, max] length."""
        self._exhaustive_queue = []
        for length in range(self.min_length, self.max_length + 1):
            for combo in itertools.product(self.VALID_CHARS, repeat=length):
                u = ''.join(combo)
                if self.is_valid(u):
                    self._exhaustive_queue.append(u)
        random.shuffle(self._exhaustive_queue)
        self._exhaustive_index = 0

    def generate_exhaustive_batch(self, count: int) -> List[str]:
        end = min(self._exhaustive_index + count, len(self._exhaustive_queue))
        batch = self._exhaustive_queue[self._exhaustive_index:end]
        self._exhaustive_index = end
        return batch

    @property
    def exhaustive_total(self) -> int:
        return len(self._exhaustive_queue)

    @property
    def exhaustive_remaining(self) -> int:
        return max(0, len(self._exhaustive_queue) - self._exhaustive_index)

    @property
    def used_count(self) -> int:
        return len(self._used)
