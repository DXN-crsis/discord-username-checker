"""
Discord username availability checker.
Uses Discord's unauthenticated registration endpoint with fingerprint rotation
and high-concurrency async requests for maximum speed.
"""

import asyncio
import aiohttp
import base64
import json
import time
import random
from typing import Optional, List, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from generator import UsernameGenerator


class DiscordAPI:
    """Low-level Discord API interaction."""

    BASE = "https://discord.com/api/v9"

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]

    BUILDS = list(range(280000, 295000))

    def __init__(self, token: Optional[str] = None):
        self.token = token.strip() if token else None
        self._fingerprints: List[str] = []
        self._fp_idx = 0

    # ── Headers ──────────────────────────────────────────────────────

    @classmethod
    def _super_properties(cls, ua: str) -> str:
        props = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": ua,
            "browser_version": "124.0.0.0",
            "os_version": "10",
            "referrer": "https://discord.com/",
            "referring_domain": "discord.com",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": random.choice(cls.BUILDS),
            "client_event_source": None,
        }
        return base64.b64encode(json.dumps(props).encode()).decode()

    def _pick_ua(self) -> str:
        return random.choice(self.USER_AGENTS)

    def _next_fp(self) -> str:
        if not self._fingerprints:
            return ""
        fp = self._fingerprints[self._fp_idx % len(self._fingerprints)]
        self._fp_idx += 1
        return fp

    # ── Fingerprint pool ─────────────────────────────────────────────

    async def fetch_fingerprint(self, session: aiohttp.ClientSession) -> str:
        ua = self._pick_ua()
        headers = {
            "User-Agent": ua,
            "X-Super-Properties": self._super_properties(ua),
        }
        try:
            async with session.get(
                f"{self.BASE}/experiments", headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("fingerprint", "")
        except Exception:
            pass
        return ""

    async def init_fingerprints(self, session: aiohttp.ClientSession, count: int = 5):
        tasks = [self.fetch_fingerprint(session) for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self._fingerprints = [r for r in results if isinstance(r, str) and r]
        if not self._fingerprints:
            self._fingerprints = [""]

    # ── Username check ───────────────────────────────────────────────

    async def check(
        self, session: aiohttp.ClientSession, username: str, retries: int = 2
    ) -> Tuple[str, Optional[bool], float]:
        """
        Check if *username* is available.
        Returns (username, is_available_or_None, elapsed_seconds).
        """
        start = time.monotonic()
        ua = self._pick_ua()

        if self.token:
            url = f"{self.BASE}/users/@me/pomelo-attempt"
            headers = {
                "Authorization": self.token,
                "Content-Type": "application/json",
                "User-Agent": ua,
                "Origin": "https://discord.com",
            }
        else:
            url = f"{self.BASE}/unique-username/username-attempt-unauthed"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": ua,
                "X-Fingerprint": self._next_fp(),
                "X-Super-Properties": self._super_properties(ua),
                "Origin": "https://discord.com",
                "Referer": "https://discord.com/register",
            }

        body = json.dumps({"username": username})

        for attempt in range(retries + 1):
            try:
                async with session.post(
                    url,
                    data=body,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        taken = data.get("taken", True)
                        return (username, not taken, time.monotonic() - start)

                    if resp.status == 429:
                        try:
                            data = await resp.json()
                            wait = min(data.get("retry_after", 1.0), 5.0)
                        except Exception:
                            wait = 1.0
                        if attempt < retries:
                            await asyncio.sleep(wait)
                            continue
                        return (username, None, time.monotonic() - start)

                    # Other errors
                    return (username, None, time.monotonic() - start)

            except asyncio.CancelledError:
                raise
            except Exception:
                if attempt < retries:
                    await asyncio.sleep(0.5)
                    continue
                return (username, None, time.monotonic() - start)

        return (username, None, time.monotonic() - start)


# ═══════════════════════════════════════════════════════════════════════
#  Qt worker thread — bridges async checking with the PyQt6 event loop
# ═══════════════════════════════════════════════════════════════════════

class CheckerWorker(QThread):
    """Runs the async checker loop in a background thread."""

    # Signals
    username_result = pyqtSignal(str, object, float)   # name, available|None, ms
    stats_update = pyqtSignal(int, int, int, float)    # checked, available, errors, rate
    log = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(
        self,
        token: Optional[str] = None,
        concurrency: int = 50,
        min_len: int = 2,
        max_len: int = 4,
        mode: str = "random",
    ):
        super().__init__()
        self.token = token
        self.concurrency = concurrency
        self.min_len = min_len
        self.max_len = max_len
        self.mode = mode
        self._running = False

        # Stats
        self._checked = 0
        self._available = 0
        self._errors = 0
        self._t0 = 0.0

    # ── Control ──────────────────────────────────────────────────────

    def stop(self):
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    # ── Thread entry ─────────────────────────────────────────────────

    def run(self):
        self._running = True
        self._checked = 0
        self._available = 0
        self._errors = 0
        self._t0 = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._main())
        except Exception as exc:
            self.log.emit(f"Fatal: {exc}")
        finally:
            loop.close()
            self.done.emit()

    # ── Async main ───────────────────────────────────────────────────

    async def _main(self):
        api = DiscordAPI(self.token)
        gen = UsernameGenerator(self.min_len, self.max_len)

        connector = aiohttp.TCPConnector(
            limit=self.concurrency * 2,
            limit_per_host=self.concurrency * 2,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            self.log.emit("Initializing fingerprints...")
            await api.init_fingerprints(session, count=8)
            self.log.emit(f"Ready — {len(api._fingerprints)} fingerprints loaded")

            if self.mode == "exhaustive":
                self.log.emit("Generating exhaustive username list...")
                gen.prepare_exhaustive()
                self.log.emit(f"Exhaustive list: {gen.exhaustive_total:,} usernames")

            sem = asyncio.Semaphore(self.concurrency)

            while self._running:
                if self.mode == "random":
                    batch = gen.generate_random(self.concurrency)
                else:
                    batch = gen.generate_exhaustive_batch(self.concurrency)
                    if not batch:
                        self.log.emit("Exhaustive scan complete!")
                        break

                tasks = [self._check_one(api, session, sem, u) for u in batch]
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_one(self, api: DiscordAPI, session, sem, username: str):
        async with sem:
            if not self._running:
                return
            name, avail, elapsed = await api.check(session, username)

            self._checked += 1
            if avail is True:
                self._available += 1
            elif avail is None:
                self._errors += 1

            self.username_result.emit(name, avail, elapsed * 1000)

            if self._checked % 5 == 0:
                total_time = time.time() - self._t0
                rate = self._checked / max(total_time, 0.001)
                self.stats_update.emit(
                    self._checked, self._available, self._errors, rate
                )
