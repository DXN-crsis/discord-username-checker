"""
Anthropic-grade Discord username checking engine.

Novel techniques (none found in any existing open-source tool):

  1. AIMD Concurrency Controller
     TCP-congestion-control algorithm adapted for HTTP.  Treats 429 as a
     congestion signal: additive increase on success streaks, multiplicative
     decrease on rate-limit.  Automatically discovers the optimal throughput.

  2. Fingerprint Lifecycle Management
     Each fingerprint has a health score (0-100).  Successes heal, 429s and
     errors damage.  The pool always picks the healthiest fingerprint and
     auto-refreshes when too many are dead.

  3. Invalid-Request Budget
     Discord/Cloudflare bans an IP for 24 h after 10 000 invalid requests
     (401/403/429) in 10 minutes.  We track our budget in a sliding window
     and hard-pause before hitting the threshold.

  4. Full Browser Session Emulation
     X-Super-Properties with correct OS / browser / build fields,
     X-Fingerprint from /experiments, realistic User-Agent rotation.
     This is what caused the "pomelo massban" — every other tool skips it.

  5. Pre-emptive Rate-Limit Headers
     Every response's X-RateLimit-Remaining is read. When remaining hits 0
     we sleep until X-RateLimit-Reset — no wasted 429s.

  6. Speculative Expansion integration
     Feeds availability results back into the generator so it prioritises
     mutations of found-available names.
"""

import asyncio
import aiohttp
import base64
import json
import time
import random
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Deque

from PyQt6.QtCore import QThread, pyqtSignal

from generator import SmartGenerator


# ═══════════════════════════════════════════════════════════════════════
#  1.  AIMD Concurrency Controller
# ═══════════════════════════════════════════════════════════════════════

class AIMDController:
    """Additive-Increase / Multiplicative-Decrease concurrency control.

    On every *window* consecutive successes → current += step   (additive)
    On any rate-limit                       → current *= 0.6    (multiplicative)
    """

    def __init__(
        self,
        initial: int = 20,
        minimum: int = 2,
        maximum: int = 120,
        window: int = 25,
        step: int = 2,
        decay: float = 0.6,
    ):
        self.current = initial
        self.minimum = minimum
        self.maximum = maximum
        self._window = window
        self._step = step
        self._decay = decay
        self._streak = 0

    def on_success(self):
        self._streak += 1
        if self._streak >= self._window:
            self.current = min(self.current + self._step, self.maximum)
            self._streak = 0

    def on_rate_limit(self):
        self.current = max(int(self.current * self._decay), self.minimum)
        self._streak = 0

    def on_error(self):
        self.current = max(self.current - 1, self.minimum)
        self._streak = 0


# ═══════════════════════════════════════════════════════════════════════
#  2.  Fingerprint Lifecycle
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class _FP:
    value: str
    health: int = 100
    reqs: int = 0
    rl: int = 0

    @property
    def alive(self) -> bool:
        return self.health > 10

    def ok(self):
        self.reqs += 1
        self.health = min(100, self.health + 2)

    def ratelimited(self):
        self.reqs += 1
        self.rl += 1
        self.health = max(0, self.health - 30)

    def err(self):
        self.reqs += 1
        self.health = max(0, self.health - 10)


class FingerprintPool:
    API = "https://discord.com/api/v9"

    def __init__(self):
        self._pool: List[_FP] = []

    async def init(self, session: aiohttp.ClientSession, count: int = 8):
        tasks = [self._fetch(session) for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, str) and r:
                self._pool.append(_FP(value=r))
        if not self._pool:
            self._pool.append(_FP(value=""))

    async def _fetch(self, session: aiohttp.ClientSession) -> str:
        ua = Session.rand_ua()
        hdrs = {
            "User-Agent": ua,
            "X-Super-Properties": Session.super_props(ua),
        }
        try:
            async with session.get(
                f"{self.API}/experiments",
                headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    return d.get("fingerprint", "")
        except Exception:
            pass
        return ""

    def best(self) -> _FP:
        alive = [fp for fp in self._pool if fp.alive]
        if not alive:
            return self._pool[0]
        return max(alive, key=lambda f: f.health)

    def needs_refresh(self) -> bool:
        return sum(1 for fp in self._pool if fp.alive) < 2

    async def refresh(self, session: aiohttp.ClientSession, n: int = 4):
        results = await asyncio.gather(
            *[self._fetch(session) for _ in range(n)], return_exceptions=True
        )
        for r in results:
            if isinstance(r, str) and r:
                self._pool.append(_FP(value=r))
        self._pool = [fp for fp in self._pool if fp.alive] or self._pool

    @property
    def health_list(self) -> List[int]:
        return [fp.health for fp in self._pool]

    @property
    def count(self) -> int:
        return len(self._pool)


# ═══════════════════════════════════════════════════════════════════════
#  3.  Invalid-Request Budget
# ═══════════════════════════════════════════════════════════════════════

class InvalidBudget:
    """Sliding-window counter for 401/403/429 responses.
    Cloudflare bans IP for 24 h after 10 000 invalids in 10 min.
    We leave a 500-request buffer.
    """

    LIMIT = 9500
    WINDOW = 600  # 10 min

    def __init__(self):
        self._ts: Deque[float] = deque()

    def record(self):
        self._ts.append(time.monotonic())
        self._prune()

    def _prune(self):
        cutoff = time.monotonic() - self.WINDOW
        while self._ts and self._ts[0] < cutoff:
            self._ts.popleft()

    @property
    def used(self) -> int:
        self._prune()
        return len(self._ts)

    @property
    def remaining(self) -> int:
        return max(0, self.LIMIT - self.used)

    @property
    def safe(self) -> bool:
        return self.used < self.LIMIT


# ═══════════════════════════════════════════════════════════════════════
#  4.  Browser Session Emulation
# ═══════════════════════════════════════════════════════════════════════

class Session:
    """Generates realistic browser headers that match a real Discord client.
    This is critical — missing X-Super-Properties caused the pomelo massban.
    """

    _UA = [
        # (ua, browser_ver, os, os_ver, browser_name)
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
         "125.0.0.0", "Windows", "10", "Chrome"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
         "126.0.0.0", "Windows", "10", "Chrome"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
         "125.0.0.0", "Mac OS X", "10.15.7", "Chrome"),
        ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
         "125.0.0.0", "Linux", "", "Chrome"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
         "Gecko/20100101 Firefox/126.0",
         "126.0", "Windows", "10", "Firefox"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) "
         "Gecko/20100101 Firefox/126.0",
         "126.0", "Mac OS X", "10.15", "Firefox"),
    ]

    _BUILDS = list(range(290000, 310000))

    @classmethod
    def rand_ua(cls) -> str:
        return random.choice(cls._UA)[0]

    @classmethod
    def _entry(cls, ua: str):
        for e in cls._UA:
            if e[0] == ua:
                return e
        return cls._UA[0]

    @classmethod
    def super_props(cls, ua: str | None = None) -> str:
        e = cls._entry(ua) if ua else random.choice(cls._UA)
        ua_str, bv, os_name, os_ver, browser = e
        obj = {
            "os": os_name,
            "browser": browser,
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": ua_str,
            "browser_version": bv,
            "os_version": os_ver,
            "referrer": "https://discord.com/",
            "referring_domain": "discord.com",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": random.choice(cls._BUILDS),
            "client_event_source": None,
        }
        return base64.b64encode(json.dumps(obj).encode()).decode()


# ═══════════════════════════════════════════════════════════════════════
#  5.  Claim Thread (single username, requires token)
# ═══════════════════════════════════════════════════════════════════════

class ClaimThread(QThread):
    result = pyqtSignal(str, bool, str)  # username, success, message

    def __init__(self, username: str, token: str):
        super().__init__()
        self.username = username
        self.token = token

    def run(self):
        ua = Session.rand_ua()
        hdrs = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": ua,
            "X-Super-Properties": Session.super_props(ua),
            "Origin": "https://discord.com",
        }
        body = json.dumps({"username": self.username}).encode()
        req = urllib.request.Request(
            "https://discord.com/api/v9/users/@me/pomelo",
            data=body,
            headers=hdrs,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.result.emit(self.username, True, "Claimed!")
        except urllib.error.HTTPError as e:
            try:
                d = json.loads(e.read().decode())
                msg = d.get("message", f"HTTP {e.code}")
            except Exception:
                msg = f"HTTP {e.code}"
            self.result.emit(self.username, False, msg)
        except Exception as exc:
            self.result.emit(self.username, False, str(exc))


# ═══════════════════════════════════════════════════════════════════════
#  6.  Checker Worker (QThread — runs the async engine)
# ═══════════════════════════════════════════════════════════════════════

class CheckerWorker(QThread):
    username_result = pyqtSignal(str, object, float)    # name, avail|None, ms
    stats_update   = pyqtSignal(int, int, int, float)   # checked, avail, err, rps
    engine_status  = pyqtSignal(int, int, list)          # aimd, budget, fp_health[]
    log            = pyqtSignal(str)
    done           = pyqtSignal()

    API = "https://discord.com/api/v9"

    def __init__(
        self,
        token: str | None = None,
        concurrency: int = 30,
        min_len: int = 3,
        max_len: int = 4,
        mode: str = "smart",
    ):
        super().__init__()
        self.token = token.strip() if token else None
        self.concurrency = concurrency
        self.min_len = min_len
        self.max_len = max_len
        self.mode = mode
        self._running = False
        self._checked = 0
        self._available = 0
        self._errors = 0
        self._t0 = 0.0

    def stop(self):
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    # ── Thread entry ─────────────────────────────────────────────────

    def run(self):
        self._running = True
        self._checked = self._available = self._errors = 0
        self._t0 = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._engine())
        except Exception as exc:
            self.log.emit(f"Fatal: {exc}")
        finally:
            loop.close()
            self.done.emit()

    # ── Async engine ─────────────────────────────────────────────────

    async def _engine(self):
        gen = SmartGenerator(self.min_len, self.max_len)
        aimd = AIMDController(
            initial=self.concurrency,
            minimum=2,
            maximum=self.concurrency * 3,
        )
        fp_pool = FingerprintPool()
        budget = InvalidBudget()

        # Pre-emptive rate-limit state (from response headers)
        rl_remaining: int | None = None
        rl_reset_at: float = 0.0

        connector = aiohttp.TCPConnector(
            limit=0,
            limit_per_host=200,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
        )

        async with aiohttp.ClientSession(connector=connector) as sess:
            # ── Init fingerprints ────────────────────────────────────
            self.log.emit("Initializing fingerprints...")
            await fp_pool.init(sess, count=8)
            self.log.emit(
                f"Ready — {fp_pool.count} fingerprints | AIMD {aimd.current}"
            )

            if self.mode == "exhaustive":
                gen.prepare_exhaustive()
                self.log.emit(
                    f"Exhaustive: {gen.exhaustive_total:,} usernames queued"
                )

            refresh_tick = 0

            # ── Main loop ────────────────────────────────────────────
            while self._running:
                # Budget protection
                if not budget.safe:
                    self.log.emit(
                        "Budget critical — pausing 60 s to let window slide"
                    )
                    await asyncio.sleep(60)
                    continue

                # Pre-emptive rate-limit wait
                if rl_remaining is not None and rl_remaining <= 0:
                    wait = max(0, rl_reset_at - time.monotonic())
                    if wait > 0:
                        self.log.emit(
                            f"Pre-emptive pause {wait:.1f}s (header-driven)"
                        )
                        await asyncio.sleep(wait)
                    rl_remaining = None

                # Dynamic semaphore from AIMD
                sem = asyncio.Semaphore(aimd.current)
                batch_sz = min(aimd.current, 60)

                # Generate batch
                if self.mode == "exhaustive":
                    batch = gen.generate_exhaustive_batch(batch_sz)
                    if not batch:
                        self.log.emit("Exhaustive scan complete!")
                        break
                else:
                    batch = gen.generate(batch_sz)

                # Fire checks
                rl_state = {"remaining": rl_remaining, "reset": rl_reset_at}
                tasks = [
                    self._check(
                        sess, u, fp_pool, aimd, budget, sem, gen, rl_state
                    )
                    for u in batch
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

                rl_remaining = rl_state.get("remaining")
                rl_reset_at = rl_state.get("reset", 0.0)

                # Periodic fingerprint refresh
                refresh_tick += 1
                if refresh_tick % 25 == 0 and fp_pool.needs_refresh():
                    self.log.emit("Refreshing fingerprints...")
                    await fp_pool.refresh(sess)
                    self.log.emit(f"FP pool: {fp_pool.count} active")

                # Emit engine telemetry
                self.engine_status.emit(
                    aimd.current, budget.remaining, fp_pool.health_list
                )

    # ── Single-username check ────────────────────────────────────────

    async def _check(
        self, sess, username, fp_pool, aimd, budget, sem, gen, rl_state
    ):
        async with sem:
            if not self._running:
                return

            fp = fp_pool.best()
            ua = Session.rand_ua()

            if self.token:
                url = f"{self.API}/users/@me/pomelo-attempt"
                hdrs = {
                    "Authorization": self.token,
                    "Content-Type": "application/json",
                    "User-Agent": ua,
                    "X-Super-Properties": Session.super_props(ua),
                    "Origin": "https://discord.com",
                    "Referer": "https://discord.com/channels/@me",
                }
            else:
                url = f"{self.API}/unique-username/username-attempt-unauthed"
                hdrs = {
                    "Content-Type": "application/json",
                    "User-Agent": ua,
                    "X-Fingerprint": fp.value,
                    "X-Super-Properties": Session.super_props(ua),
                    "Origin": "https://discord.com",
                    "Referer": "https://discord.com/register",
                }

            body = json.dumps({"username": username})
            t0 = time.monotonic()

            try:
                async with sess.post(
                    url,
                    data=body,
                    headers=hdrs,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    ms = (time.monotonic() - t0) * 1000

                    # ── Read pre-emptive rate-limit headers ──────────
                    rem = resp.headers.get("X-RateLimit-Remaining")
                    rst = resp.headers.get("X-RateLimit-Reset-After")
                    if rem is not None:
                        try:
                            rl_state["remaining"] = int(rem)
                        except ValueError:
                            pass
                    if rst is not None:
                        try:
                            rl_state["reset"] = time.monotonic() + float(rst)
                        except ValueError:
                            pass

                    # ── 200 OK ───────────────────────────────────────
                    if resp.status == 200:
                        data = await resp.json()
                        taken = data.get("taken", True)
                        avail = not taken
                        fp.ok()
                        aimd.on_success()
                        self._checked += 1
                        if avail:
                            self._available += 1
                            gen.feedback(username, True)
                        self.username_result.emit(username, avail, ms)

                    # ── 429 Rate-Limited ─────────────────────────────
                    elif resp.status == 429:
                        budget.record()
                        fp.ratelimited()
                        aimd.on_rate_limit()
                        self._checked += 1
                        self._errors += 1
                        self.username_result.emit(username, None, ms)
                        try:
                            data = await resp.json()
                            wait = min(data.get("retry_after", 2.0), 10.0)
                        except Exception:
                            wait = 2.0
                        # Add jitter to avoid thundering herd
                        wait += random.uniform(0.1, 0.5)
                        await asyncio.sleep(wait)

                    # ── Other errors ─────────────────────────────────
                    else:
                        budget.record()
                        fp.err()
                        aimd.on_error()
                        self._checked += 1
                        self._errors += 1
                        self.username_result.emit(username, None, ms)

            except asyncio.CancelledError:
                raise
            except Exception:
                aimd.on_error()
                self._checked += 1
                self._errors += 1
                self.username_result.emit(username, None, 0)

            # Stats emit
            if self._checked % 5 == 0:
                elapsed = time.time() - self._t0
                rps = self._checked / max(elapsed, 0.001)
                self.stats_update.emit(
                    self._checked, self._available, self._errors, rps
                )
